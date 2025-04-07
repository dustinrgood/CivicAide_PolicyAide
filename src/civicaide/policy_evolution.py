from __future__ import annotations

import asyncio
import json
import os
import sys
import random
import time
import re
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any, AsyncIterator, TypeVar, Set
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import datetime
import uuid
import streamlit as st
from openai import AsyncOpenAI

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the agents SDK
from src.agents import Agent, Runner, ItemHelpers, trace, custom_span, gen_trace_id
from agents.result import RunResult
from src.civicaide.trace_manager import get_trace_processor
from agents.tracing import add_trace_processor
from agents.tracing.processors import BatchTraceProcessor, BackendSpanExporter

# Load environment variables
dotenv_path = Path(__file__).parent / "local.env"
load_dotenv(dotenv_path)

# Ensure API key is loaded
if "OPENAI_API_KEY" not in os.environ and os.path.exists(dotenv_path):
    with open(dotenv_path, 'r') as f:
        for line in f:
            if line.strip().startswith('OPENAI_API_KEY='):
                key = line.strip().split('=', 1)[1]
                os.environ["OPENAI_API_KEY"] = key
                print("API key loaded from local.env")
                break

# Initialize OpenAI client
client = AsyncOpenAI()

# Set up OpenAI tracing - add our processor alongside the default OpenAI one
backend_exporter = BackendSpanExporter()
trace_processor = BatchTraceProcessor(backend_exporter)
add_trace_processor(trace_processor)  # This adds our processor while keeping the OpenAI one

# Define specialized agents for the orchestration pattern
planning_agent = Agent(
    name="Planning agent",
    model="gpt-4o",  # Using a faster model for initial planning
    instructions="Specialized for planning research on policy topics. Generate a focused research plan with search queries and methodology.",
    output_type=dict  # Use dict instead of output_schema
)

synthesis_agent = Agent(
    name="Synthesis agent",
    model="gpt-4o",  # Using a more powerful model for complex synthesis
    instructions="Specialized for synthesizing complex policy research and findings. Create a cohesive synthesis that identifies key themes and promising approaches."
)

# ELO Rating System
@dataclass
class EloRating:
    """Elo rating system for policy proposals."""
    
    # Default starting Elo rating
    DEFAULT_RATING = 1200
    # K-factor determines how much ratings change after each match
    K_FACTOR = 32
    
    ratings: Dict[str, float] = field(default_factory=dict)
    
    def get_rating(self, proposal_id: str) -> float:
        """Get the Elo rating for a proposal."""
        return self.ratings.get(proposal_id, self.DEFAULT_RATING)
    
    def update_rating(self, winner_id: str, loser_id: str) -> Tuple[float, float]:
        """Update Elo ratings after a comparison."""
        winner_rating = self.get_rating(winner_id)
        loser_rating = self.get_rating(loser_id)
        
        # Calculate expected scores
        expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))
        
        # Update ratings
        new_winner_rating = winner_rating + self.K_FACTOR * (1 - expected_winner)
        new_loser_rating = loser_rating + self.K_FACTOR * (0 - expected_loser)
        
        # Store updated ratings
        self.ratings[winner_id] = new_winner_rating
        self.ratings[loser_id] = new_loser_rating
        
        return new_winner_rating, new_loser_rating

# Policy Proposal Models
@dataclass
class PolicyProposal:
    """A policy proposal in the evolution system."""
    id: str
    title: str
    description: str
    rationale: str
    elo_rating: float = 1200.0
    generation: int = 1
    stakeholder_impacts: Dict[str, str] = field(default_factory=dict)
    implementation_challenges: List[str] = field(default_factory=list)
    equity_considerations: str = ""
    economic_analysis: str = ""
    
    def full_text(self) -> str:
        """Get the full text of the proposal including title, description, and rationale."""
        return f"{self.title}\n\n{self.description}\n\nRationale:\n{self.rationale}"

# API-compatible Pydantic models for OpenAI
class PolicyProposalModel(BaseModel):
    """A policy proposal model for API interactions."""
    id: str
    title: str
    description: str
    rationale: str
    stakeholder_impacts: Optional[Dict[str, str]] = None
    implementation_challenges: Optional[List[str]] = None
    equity_considerations: Optional[str] = None
    economic_analysis: Optional[str] = None
    
    class Config:
        schema_extra = {
            "required": ["id", "title", "description", "rationale"]
        }

class PolicyProposalBatch(BaseModel):
    """A batch of policy proposals."""
    proposals: List[PolicyProposalModel]
    
    class Config:
        schema_extra = {
            "required": ["proposals"]
        }

class ComparisonResult(BaseModel):
    """Result of comparing two policy proposals."""
    winner_id: str
    loser_id: str
    reasoning: str
    
    class Config:
        schema_extra = {
            "required": ["winner_id", "loser_id", "reasoning"]
        }

class EvolutionResult(BaseModel):
    """Result of evolving a policy proposal."""
    original_id: str
    evolved_proposal: PolicyProposalModel
    improvements: str
    
    class Config:
        schema_extra = {
            "required": ["original_id", "evolved_proposal", "improvements"]
        }

class FinalReportModel(BaseModel):
    """Final policy report model for API interactions."""
    summary: str
    top_proposals: List[PolicyProposalModel]
    key_considerations: List[str]
    implementation_steps: List[str]
    stakeholder_analysis: Optional[Dict[str, List[str]]] = None
    impact_matrix: Optional[List[Dict[str, str]]] = None
    equity_assessment: Optional[str] = None
    cost_benefit_summary: Optional[str] = None
    alternative_scenarios: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "required": ["summary", "top_proposals", "key_considerations", "implementation_steps"]
        }

@dataclass
class FinalReport:
    """The final policy analysis report."""
    summary: str
    top_proposals: List[PolicyProposal]
    key_considerations: List[str]
    implementation_steps: List[str]
    stakeholder_analysis: Dict[str, List[str]] = field(default_factory=dict)
    impact_matrix: List[Dict[str, str]] = field(default_factory=list)
    equity_assessment: str = ""
    cost_benefit_summary: str = ""
    alternative_scenarios: List[str] = field(default_factory=list)

# Agent Definitions
policy_generation_agent = Agent(
    name="Policy Generation Agent",
    instructions="""Generate innovative, practical, and effective policy proposals for local governments on a given policy topic.
    
    For each policy proposal, provide:
    1. A clear, descriptive title
    2. A detailed description of the policy
    3. A strong rationale explaining why this policy would be effective
    4. Analysis of impacts on key stakeholder groups (businesses, residents, vulnerable populations, environment)
    5. Potential implementation challenges
    6. Equity considerations to ensure fair distribution of benefits and burdens
    7. Economic analysis including costs, benefits, and resource requirements
    
    Generate diverse proposals with different approaches to solving the problem.
    """,
    model="gpt-4o",
    output_type=PolicyProposalBatch,
)

comparison_agent = Agent(
    name="Policy Comparison Agent",
    instructions="""Compare two policy proposals to determine which is more effective and equitable.
    
    Evaluate each policy based on these criteria:
    1. Environmental impact - How effectively does it address the environmental issue?
    2. Economic feasibility - Is it financially reasonable to implement?
    3. Social equity - Does it distribute benefits and burdens fairly across different groups?
    4. Implementation complexity - How challenging would it be to execute?
    5. Stakeholder acceptance - How well would different groups receive it?
    
    For each stakeholder group, assess which policy better addresses their needs:
    - Small businesses
    - Large retailers
    - Low-income residents
    - Environmental advocates
    - Local government implementers
    - Industry/manufacturers
    
    Provide a clear explanation of why one policy is superior, considering all stakeholders.
    """,
    model="gpt-4o",
)

policy_evolution_agent = Agent(
    name="Policy Evolution Agent",
    instructions="""Improve existing policy proposals by addressing their weaknesses and enhancing their strengths.
    
    For each policy evolution:
    1. Identify 3-5 specific improvements to make the policy more effective, equitable, feasible, and comprehensive
    2. Create a new evolved version with these improvements integrated seamlessly
    3. Enhance stakeholder impact analysis for different groups
    4. Address implementation challenges more thoroughly
    5. Improve equity considerations and economic analysis
    6. Provide a concise explanation of how this evolved version is better than the original
    
    Focus on creating policies that balance effectiveness, equity, feasibility, and public acceptance.
    """,
    model="gpt-4o",
    output_type=EvolutionResult,
)

policy_report_agent = Agent(
    name="Policy Report Agent",
    instructions="""Create a comprehensive final policy report summarizing the best policies identified through the evolution process.
    
    The report should include:
    1. Executive summary - A concise overview of the key findings and recommendations
    2. Top policy proposals - Detailed descriptions of the best-performing policies
    3. Stakeholder impact analysis - How each policy affects different groups:
       - Small businesses vs. large corporations
       - Low-income vs. high-income residents
       - Environmental groups
       - Local government (implementation feasibility)
       - Vulnerable populations (elderly, disabled, economically disadvantaged)
    4. Equity assessment - Analysis of how benefits and burdens are distributed across different communities
    5. Cost-benefit summary - Economic analysis of the proposed policies
    6. Key considerations - Important factors to consider during implementation
    7. Implementation steps - A phased approach to policy rollout
    8. Impact matrix - Visual representation of how each policy scores across different evaluation criteria
    9. Alternative scenarios - How policies might perform under different conditions
    
    Format the report in a clear, professional manner with sections and subsections for easy navigation.
    """,
    model="gpt-4o",
    output_type=FinalReportModel,
)

policy_tournament_agent = Agent(
    name="Policy Tournament Agent",
    instructions="""Evaluate and compare two policy proposals to determine which is more effective.
    
    Consider these evaluation criteria:
    1. Environmental impact - How effectively does it address the environmental problem?
    2. Economic feasibility - Is it financially sustainable and reasonable to implement?
    3. Implementation complexity - How challenging would it be to execute?
    4. Public acceptance - How likely are stakeholders to support it?
    5. Equity - Does it distribute benefits and burdens fairly across different groups?
    6. Adaptability - Can it be adjusted as conditions change?
    7. Resource efficiency - Does it make good use of available resources?
    8. Stakeholder impacts - How does it affect different groups (businesses, residents, vulnerable populations)?
    
    For each comparison, provide a clear explanation of why one policy is superior to the other based on these criteria.
    """,
    model="gpt-4o",
)

# Local context gathering agent
context_gathering_agent = Agent(
    name="Context Gathering Agent",
    instructions="""Ask the user specific questions to understand their local context for policy implementation.
    
    Gather information about:
    1. Jurisdiction type and size (population, urban/suburban/rural)
    2. Economic context (major industries, business composition)
    3. Existing related policies or initiatives
    4. Political landscape and constraints
    5. Budget limitations
    6. Specific local challenges and opportunities
    7. Key stakeholders and their concerns
    
    Ask questions in a conversational way, adapting follow-up questions based on previous answers.
    Keep the context gathering focused on information relevant to the policy topic.
    At the end, produce a concise summary of the local context.
    """,
    model="gpt-4o",
)

# Web research agent
web_research_agent = Agent(
    name="Web Research Agent",
    instructions="""Research real-world examples and evidence for the policy topic.
    
    For the given policy question:
    1. Identify key search terms for finding relevant information
    2. Generate 3-5 specific search queries focusing on:
       - Recent successful policy implementations
       - Example ordinances from comparable jurisdictions
       - Evidence of effectiveness and challenges
       - Stakeholder responses and adaptations
    3. Synthesize findings into a concise research summary
    
    Focus on finding actionable, specific information that can inform practical policy design.
    Identify patterns across successful implementations and note key differences based on context.
    """,
    model="gpt-4o",
)

# Research planner agent
research_planner_agent = Agent(
    name="Research Planner Agent",
    instructions="""Plan a focused research strategy for the policy topic based on local context.
    
    Create a research plan that:
    1. Identifies 3-5 specific search queries based on the policy topic and local context
    2. Prioritizes finding real ordinances from similar jurisdictions
    3. Looks for evidence of effectiveness, implementation challenges, and costs
    4. Searches for stakeholder responses in similar contexts
    
    The research plan should be strategic, focusing on high-value information that will
    directly inform policy design for the specific local context provided.
    """,
    model="gpt-4o",
)

class LocalContext(BaseModel):
    """Local context information for policy adaptation."""
    jurisdiction_type: str
    population_size: str
    economic_context: str
    existing_policies: str
    political_landscape: str
    budget_constraints: str
    local_challenges: str
    key_stakeholders: str
    demographic_profile: Optional[str] = "Not specified"
    prior_attempts: Optional[str] = "Not specified"
    budget_cycle: Optional[str] = "Not specified"
    election_timeline: Optional[str] = "Not specified"
    stakeholder_influence: Optional[Dict[str, Dict[str, str]]] = Field(default_factory=dict)
    contextual_notes: Optional[str] = None  # For storing additional context from user input
    
    class Config:
        schema_extra = {
            "required": ["jurisdiction_type", "population_size", "economic_context", 
                         "existing_policies", "political_landscape", "budget_constraints",
                         "local_challenges", "key_stakeholders"]
        }

class ResearchPlan(BaseModel):
    """Plan for policy research."""
    search_queries: List[str]
    focus_areas: List[str]
    specific_jurisdictions: List[str]
    
    class Config:
        schema_extra = {
            "required": ["search_queries", "focus_areas"]
        }

class ResearchResults(BaseModel):
    """Results from policy research."""
    successful_implementations: List[str]
    example_ordinances: List[Dict[str, str]]
    effectiveness_evidence: List[str]
    stakeholder_responses: Dict[str, List[str]]
    implementation_challenges: List[str]
    
    class Config:
        schema_extra = {
            "required": ["successful_implementations", "example_ordinances", 
                         "effectiveness_evidence", "stakeholder_responses", 
                         "implementation_challenges"]
        }

# Web search API function
async def web_search_api(query: str) -> Dict:
    """Perform a web search using an external search API."""
    # Replace with your actual search API implementation
    # This is a placeholder that returns mock results
    
    try:
        # Use a public search API (or replace with your preferred API)
        api_key = os.getenv("SERP_API_KEY")
        if api_key:
            # If you have a SERP API key, use it for real searches
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": api_key,
                "engine": "google",
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Search API error: {response.status_code}")
        
        # Use the OpenAI Agents SDK web search instead if SERP_API_KEY is not available
        # This will provide real web search results from OpenAI's search backend
        try:
            from src.agents import Runner
            from src.agents import Agent
            
            # Create a simple web search agent
            web_search_agent = Agent(
                name="Web Search Agent",
                instructions=f"Perform a web search for '{query}' and return the most relevant results",
                model="gpt-4o",
            )
            
            # Run the web search through OpenAI's web search tool
            print(f"Using OpenAI web search for: {query}")
            search_result = await Runner.run_with_tools(
                web_search_agent, 
                query,
                tool_choice={"type": "web_search"}
            )
            
            # Format the results similar to SerpAPI format
            result_text = str(search_result)
            
            # Extract URLs and content from result text
            import re
            urls = re.findall(r'https?://[^\s)]+', result_text)
            content_parts = result_text.split("\n\n")
            
            # Create synthetic organic results
            organic_results = []
            for i, url in enumerate(urls[:3]):  # Limit to top 3 results if more were found
                snippet = content_parts[i] if i < len(content_parts) else f"Result for {query}"
                organic_results.append({
                    "title": f"Web Result {i+1} for {query}",
                    "snippet": snippet[:200] + "...",
                    "link": url
                })
            
            # If no URLs were found, create default results
            if not organic_results:
                for i in range(3):
                    organic_results.append({
                        "title": f"Web Result {i+1} for {query}",
                        "snippet": f"Information about {query} from web search.",
                        "link": f"https://example.com/result{i+1}"
                    })
            
            return {
                "query": query,
                "organic_results": organic_results
            }
        except Exception as e:
            print(f"Error using OpenAI web search: {e}")
            # Fall back to mock results if OpenAI search fails
            print("Falling back to simulated search results due to OpenAI search error")
        
        # Fallback or mock results if both search methods fail
        print("Using simulated search results")
        time.sleep(1)  # Simulate API delay
        
        # Return mock results based on the query
        return {
            "query": query,
            "organic_results": [
                {
                    "title": f"Example result for {query} - Implementation Guide",
                    "snippet": f"This guide provides a comprehensive overview of {query} implementation strategies for local governments.",
                    "link": "https://example.com/result1"
                },
                {
                    "title": f"Case Study: {query} in Similar Jurisdictions",
                    "snippet": f"Analysis of several municipalities that have successfully implemented {query} policies.",
                    "link": "https://example.com/result2"
                },
                {
                    "title": f"Economic Impact Assessment of {query}",
                    "snippet": f"Research on the economic effects of {query} on businesses and consumers.",
                    "link": "https://example.com/result3"
                }
            ]
        }
    except Exception as e:
        print(f"Error performing web search: {e}")
        return {"error": str(e), "organic_results": []}

# Tournament and Evolution System
class PolicyEvolutionManager:
    """
    Manages the policy evolution process using a tournament system and ELO ratings.
    
    This implements a system similar to Google's AI Co-Scientist, where:
    1. Multiple policy proposals are generated
    2. Proposals compete in tournament-style evaluations
    3. Top proposals are evolved to create better versions
    4. The process repeats for multiple generations
    5. Final report synthesizes the best elements
    """
    
    def __init__(self, max_generations: int = 3, tournament_rounds: int = 5, evolution_candidates: int = 2):
        self.elo_system = EloRating()
        self.proposals: Dict[str, PolicyProposal] = {}
        self.max_generations = max_generations
        self.tournament_rounds = tournament_rounds
        self.evolution_candidates = evolution_candidates
        self.generation_count = 0
        self.trace_id = None
        self.current_trace = None
    
    async def run(self, query: str) -> FinalReportModel:
        """Run the full policy evolution process."""
        # Get trace manager
        trace_processor = get_trace_processor()
        
        # Use trace ID from OpenAI if available, otherwise generate a new one
        # Ensure trace ID always starts with "trace_" to meet OpenAI requirements
        openai_trace_id = os.environ.get("OPENAI_TRACE_ID")
        if openai_trace_id:
            trace_id = openai_trace_id
            print(f"Using OpenAI trace ID: {trace_id}")
        else:
            trace_id = f"trace_{uuid.uuid4().hex[:24]}"  # Use gen_trace_id() format
            print(f"Generated trace ID: {trace_id}")
            
        self.trace_id = trace_id
        
        # Set OpenAI API headers for tracing if we have an API key
        if "OPENAI_API_KEY" in os.environ:
            # Enable traces in the OpenAI client
            os.environ["OPENAI_API_TYPE"] = "openai"
            os.environ["OPENAI_API_VERSION"] = "2023-05-15"  # Use appropriate version
            
            # The OpenAI client will automatically use this header when creating the client
            os.environ["OPENAI_EXTRA_HEADERS"] = json.dumps({
                "OpenAI-Beta": "assistants=v2 tools=v2 trace=v1",
                "X-Trace-Id": trace_id
            })
        
        # Initialize trace - custom_span doesn't accept trace_id directly
        with trace("Policy Evolution Process", trace_id=trace_id) as current_trace:
            self.current_trace = current_trace
            
            # Ensure we have a valid trace ID
            print(f"\nInitializing Policy Evolution System for: {query}")
            print(f"Trace ID: {trace_id}")
            
            # Record the initialization
            system_span_id = trace_processor.record_agent_interaction(
                trace_id=trace_id,
                agent_name="System",
                input_text=f"Policy Query: {query}",
                output_text=f"Initialized Policy Evolution System",
                span_type="system_initialization",
                model="system"
            )
                
            try:
                # Step 1: Gather local context information through user interaction
                local_context = await self._gather_local_context(query)
                
                # Record the context gathering
                context_span_id = trace_processor.record_agent_interaction(
                    trace_id=trace_id,
                    agent_name="Context Agent",
                    input_text=f"Policy Query: {query}",
                    output_text=f"Gathered local context: {local_context.jurisdiction_type}, {local_context.population_size} population",
                    span_type="context_gathering",
                    model="system",
                    parent_span_id=system_span_id,
                    system_instructions="""Ask the user specific questions to understand their local context for policy implementation.
                        Focus on jurisdiction type, population, economic factors, political landscape, and stakeholder dynamics."""
                )
                
                # Step 2: Conduct web research based on local context
                research_results = await self._conduct_web_research(query, local_context)
                
                # Record the research results
                research_span_id = trace_processor.record_agent_interaction(
                    trace_id=trace_id,
                    agent_name="Research Agent",
                    input_text=f"Policy Query: {query}\nLocal Context: {local_context.jurisdiction_type}",
                    output_text=f"Generated research results with {len(research_results.successful_implementations)} successful implementations",
                    span_type="research",
                    parent_span_id=system_span_id,
                    system_instructions="""Research real-world examples and evidence for the policy topic.
                        Focus on successful implementations, challenges faced, and lessons learned from similar jurisdictions."""
                )
                
                # Step 3: Generate initial policy proposals informed by research and context
                for generation in range(self.max_generations):
                    print(f"\n--- Generation {generation+1} ---\n")
                    self.generation_count = generation + 1
                    
                    # Create a generation span to group all activities in this generation
                    generation_span_id = trace_processor.record_agent_interaction(
                        trace_id=trace_id,
                        agent_name="Generation Manager",
                        input_text=f"Generation {generation+1} started",
                        output_text=f"Managing generation {generation+1} of policy proposals",
                        span_type="generation_marker",
                        parent_span_id=system_span_id
                    )
                    
                    # Step 3a: Generate initial proposals or evolve existing ones
                    if generation == 0:
                        await self._generate_initial_proposals(query, local_context, research_results)
                        
                        # Record the proposal generation
                        generation_process_span_id = trace_processor.record_agent_interaction(
                            trace_id=trace_id,
                            agent_name="Policy Generation Agent",
                            input_text=f"Generate initial policy proposals for: {query}",
                            output_text=f"Generated {len(self.proposals)} initial policy proposals",
                            span_type="policy_generation",
                            model="gpt-4-turbo",
                            parent_span_id=generation_span_id,
                            metadata={
                                "generation": generation + 1,
                                "proposal_count": len(self.proposals)
                            },
                            system_instructions="""Generate innovative, practical, and effective policy proposals for local governments on a given policy topic.
                                Consider the local context, research findings, and stakeholder needs. Focus on feasibility, equity, and measurable impact."""
                        )
                    else:
                        await self._evolve_top_proposals()
                        
                        # Record the policy evolution
                        generation_process_span_id = trace_processor.record_agent_interaction(
                            trace_id=trace_id,
                            agent_name="Policy Evolution Agent",
                            input_text=f"Evolve top proposals for generation {generation}",
                            output_text=f"Evolved policy proposals for generation {generation}",
                            span_type="policy_evolution",
                            model="gpt-4-turbo",
                            parent_span_id=generation_span_id,
                            metadata={
                                "generation": generation + 1,
                                "proposal_count": len(self.proposals)
                            },
                            system_instructions="""Improve existing policy proposals by addressing their weaknesses and enhancing their strengths.
                                Focus on practical implementation, equity considerations, and measurable outcomes."""
                        )
                    
                    # Step 3b: Run a tournament to compare and rank proposals
                    await self._run_tournament()
                    
                    # Record the tournament results
                    tournament_span_id = trace_processor.record_agent_interaction(
                        trace_id=trace_id,
                        agent_name="Policy Evaluation Agent",
                        input_text=f"Evaluate policy proposals via tournament for generation {generation+1}",
                        output_text=f"Completed tournament evaluation for generation {generation+1}",
                        span_type="policy_evaluation",
                        model="gpt-4-turbo",
                        parent_span_id=generation_span_id,
                        metadata={
                            "generation": generation + 1,
                            "tournament_rounds": self.tournament_rounds
                        },
                        system_instructions="""Compare two policy proposals to determine which is more effective and equitable.
                            Evaluate based on practicality, impact, cost-effectiveness, and alignment with local needs."""
                    )
                    
                    # Step 3c: Display current rankings
                    print("\nCurrent Policy Proposal Rankings:")
                    top_proposals = sorted(
                        self.proposals.values(),
                        key=lambda p: self.elo_system.get_rating(p.id),
                        reverse=True
                    )
                    
                    for i, proposal in enumerate(top_proposals):
                        print(f"{i+1}. {proposal.title} (Elo: {self.elo_system.get_rating(proposal.id):.1f})")
                    print()
                
                # Step 4: Create a final report
                final_report = await self._create_final_report(query, local_context, research_results)
                
                # Record the final report generation
                final_report_span_id = trace_processor.record_agent_interaction(
                    trace_id=trace_id,
                    agent_name="Stakeholder Analysis Agent",
                    input_text=f"Analyze stakeholder impacts for top policy proposals on: {query}",
                    output_text=f"Completed evolution process with {len(final_report.top_proposals)} top proposals",
                    span_type="stakeholder_analysis",
                    model="gpt-4-turbo",
                    parent_span_id=system_span_id,
                    metadata={
                        "top_proposal_count": len(final_report.top_proposals),
                        "total_generations": self.generation_count,
                        "total_proposals": len(self.proposals)
                    },
                    system_instructions="""Create a comprehensive final policy report summarizing the best policies identified through the evolution process.
                        Include detailed stakeholder analysis, implementation steps, and impact assessments."""
                )
                
                # Add OpenAI trace URL
                openai_trace_url = f"https://platform.openai.com/logs?filter=%7B%22trace_id%22%3A%22{trace_id}%22%7D"
                print(f"\nOpenAI logs for this run: {openai_trace_url}")
                
                # Save the trace data
                trace_file = trace_processor.save_trace_to_file_and_db(query, "evolution")
                if trace_file:
                    print(f"Trace data saved to: {trace_file}")
                
                return final_report
            except Exception as e:
                print(f"Error in policy evolution process: {e}")
                raise
    
    async def _gather_local_context(self, query: str) -> LocalContext:
        """Gather local context information through interaction with the user."""
        print("\n--- Gathering Local Context ---\n")
        
        # Initial context gathering prompt
        context_prompt = (
            f"I'll help you design an effective policy approach for: '{query}'\n\n"
            f"To customize this for your specific jurisdiction, I need to understand your local context.\n"
            f"Please answer the following questions to help me provide more relevant policy recommendations:\n\n"
            f"1. What type of jurisdiction are you in (city, county, etc.) and what's the approximate population?\n"
            f"2. What are the major industries or economic drivers in your area?\n"
            f"3. Do you have any existing policies related to this topic?\n"
            f"4. Are there specific political considerations or constraints to be aware of?\n"
            f"5. What budget limitations should be considered for implementation?\n"
            f"6. Are there any unique local challenges or opportunities related to this policy area?\n"
            f"7. Who are the key stakeholders that would be affected by this policy?\n"
            f"8. What key demographic factors are important (e.g., median age, income distribution)?\n"
            f"9. Have similar policies been attempted locally before?\n"
            f"10. Where are you in the budget cycle?\n"
            f"11. Are there any upcoming elections to consider?"
        )
        
        # Print the context prompt
        print(context_prompt)
        
        # Initialize the response dictionary with default values
        responses = {
            "jurisdiction_type": "",
            "population_size": "",
            "economic_context": "",
            "existing_policies": "",
            "political_landscape": "",
            "budget_constraints": "",
            "local_challenges": "",
            "key_stakeholders": "",
            "demographic_profile": "",
            "prior_attempts": "",
            "budget_cycle": "",
            "election_timeline": "",
            "stakeholder_influence": {},
            "contextual_notes": None
        }
        
        # Collect responses for each field
        try:
            responses["jurisdiction_type"] = input("Jurisdiction type and population: ")
            responses["economic_context"] = input("Major industries/economic drivers: ")
            responses["existing_policies"] = input("Existing related policies: ")
            responses["political_landscape"] = input("Political considerations/constraints: ")
            responses["budget_constraints"] = input("Budget limitations: ")
            responses["local_challenges"] = input("Unique local challenges/opportunities: ")
            responses["key_stakeholders"] = input("Key stakeholders: ")
            
            # Collect deeper contextual elements
            responses["demographic_profile"] = input("Key demographic factors: ")
            responses["prior_attempts"] = input("Have similar policies been attempted locally before? Details: ")
            responses["budget_cycle"] = input("Where are you in the budget cycle? ")
            responses["election_timeline"] = input("Upcoming election considerations: ")
            
            # Optional stakeholder influence mapping - ALWAYS ensure it's a dictionary
            collect_stakeholder_influence = input("Would you like to provide detailed stakeholder influence information? (yes/no): ")
            
            # Initialize stakeholder_influence as an empty dictionary by default
            responses["stakeholder_influence"] = {}
            
            if collect_stakeholder_influence.lower().strip() == "yes":
                # Only enter this section if they specifically type "yes"
                while True:
                    stakeholder = input("Enter stakeholder name (or 'done' to finish): ")
                    if stakeholder.lower() == 'done':
                        break
                    influence = input(f"Rate {stakeholder}'s influence (1-5): ")
                    stance = input(f"{stakeholder}'s likely stance on this policy (support/neutral/oppose): ")
                    responses["stakeholder_influence"][stakeholder] = {"influence": influence, "stance": stance}
            else:
                # For any other input, just store it as a contextual note and keep stakeholder_influence as empty dict
                if collect_stakeholder_influence and collect_stakeholder_influence.lower() != "no":
                    # If they provided additional context rather than just "no"
                    responses["contextual_notes"] = collect_stakeholder_influence
                    print("Additional context noted. Continuing with empty stakeholder influence mapping.")
            
        except Exception as e:
            print(f"Error collecting input: {e}")
            # Provide default values if input fails
            for key in responses:
                if not responses[key] and key != "stakeholder_influence" and key != "contextual_notes":
                    responses[key] = "Not specified"
            # Ensure stakeholder_influence is always a dictionary
            responses["stakeholder_influence"] = responses.get("stakeholder_influence", {})
        
        # Ensure population is extracted from jurisdiction if combined
        if "population" not in responses["population_size"].lower() and responses["jurisdiction_type"]:
            # Try to extract population from jurisdiction field if it contains numbers
            population_matches = re.findall(r'(\d[\d,]*)', responses["jurisdiction_type"])
            if population_matches:
                responses["population_size"] = population_matches[0]
                # Update jurisdiction to remove the population part
                jurisdiction_parts = responses["jurisdiction_type"].split(',')
                if len(jurisdiction_parts) > 1:
                    responses["jurisdiction_type"] = jurisdiction_parts[0].strip()
        
        # Make sure all required fields have values
        for key in responses:
            if not responses[key] and key != "contextual_notes" and key != "stakeholder_influence":
                responses[key] = "Not specified"
        
        # Print the collected responses for verification
        print("\nCollected context information:")
        for key, value in responses.items():
            if key != "stakeholder_influence":  # Skip detailed stakeholder influence for cleaner output
                print(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Create context object
        try:
            local_context = LocalContext(**responses)
            print("\nLocal context information gathered successfully.")
            
            # DEBUG: Add detailed logging of the local context object
            print("\n[DEBUG] Local context object attributes:")
            for attr, value in local_context.__dict__.items():
                if attr != "_sa_instance_state" and attr != "stakeholder_influence":
                    print(f"  {attr}: {value}")
            
            return local_context
        except Exception as e:
            print(f"Error creating local context: {e}")
            
            # More robust error handling - instead of using default values, 
            # try to salvage the input data by handling specific validation errors
            try:
                # Try fixing common validation issues
                fixed_responses = responses.copy()
                
                # Ensure stakeholder_influence is a dictionary
                if not isinstance(fixed_responses.get("stakeholder_influence"), dict):
                    fixed_responses["stakeholder_influence"] = {}
                    print("Fixed stakeholder_influence to be an empty dictionary.")
                
                # Try again with fixed data
                local_context = LocalContext(**fixed_responses)
                print("Successfully created local context after fixing validation issues.")
                
                # DEBUG: Add detailed logging of the local context object
                print("\n[DEBUG] Fixed local context object attributes:")
                for attr, value in local_context.__dict__.items():
                    if attr != "_sa_instance_state" and attr != "stakeholder_influence":
                        print(f"  {attr}: {value}")
                
                return local_context
            except Exception as e2:
                print(f"Error even after fixing validation issues: {e2}")
                
                # Last resort - create an object that preserves the input context as much as possible
                print("Using manual context creation to preserve user input...")
                
                # Extract the jurisdiction information as it's the most critical piece
                jurisdiction = responses.get("jurisdiction_type", "Not specified")
                if jurisdiction == "":
                    jurisdiction = "Not specified"
                    
                # Create a fallback context with manually constructed values
                fallback_context = LocalContext(
                    jurisdiction_type=jurisdiction,
                    population_size=responses.get("population_size", "Not specified") or "Not specified",
                    economic_context=responses.get("economic_context", "Not specified") or "Not specified",
                    existing_policies=responses.get("existing_policies", "Not specified") or "Not specified",
                    political_landscape=responses.get("political_landscape", "Not specified") or "Not specified",
                    budget_constraints=responses.get("budget_constraints", "Not specified") or "Not specified",
                    local_challenges=responses.get("local_challenges", "Not specified") or "Not specified",
                    key_stakeholders=responses.get("key_stakeholders", "Not specified") or "Not specified",
                    demographic_profile=responses.get("demographic_profile", "Not specified") or "Not specified",
                    prior_attempts=responses.get("prior_attempts", "Not specified") or "Not specified",
                    budget_cycle=responses.get("budget_cycle", "Not specified") or "Not specified",
                    election_timeline=responses.get("election_timeline", "Not specified") or "Not specified",
                    stakeholder_influence={},
                    contextual_notes=responses.get("contextual_notes")
                )
                
                print("Created fallback context with preserved user input.")
                return fallback_context

    async def _conduct_web_research(self, query: str, local_context: LocalContext) -> ResearchResults:
        """Conduct web research based on the policy query and local context."""
        print("\n--- Conducting Web Research ---\n")
        
        # Generate a research plan based on query and local context
        plan_prompt = (
            f"Policy Query: {query}\n\n"
            f"Local Context:\n"
            f"- Jurisdiction: {local_context.jurisdiction_type} (Population: {local_context.population_size})\n"
            f"- Economic Context: {local_context.economic_context}\n"
            f"- Existing Policies: {local_context.existing_policies}\n"
            f"- Political Landscape: {local_context.political_landscape}\n"
            f"- Budget Constraints: {local_context.budget_constraints}\n"
            f"- Local Challenges: {local_context.local_challenges}\n"
            f"- Key Stakeholders: {local_context.key_stakeholders}\n\n"
            f"Based on this policy query and local context, develop a focused research plan."
        )
        
        research_plan_result = await Runner.run(
            research_planner_agent,
            plan_prompt,
        )
        
        # For simplicity in this example, we'll create a simple research plan
        # In a real implementation, parse the agent's response into a structured plan
        research_plan = ResearchPlan(
            search_queries=[
                f"{query} successful implementations",
                f"{query} ordinance example {local_context.jurisdiction_type}",
                f"{query} economic impact {local_context.economic_context}",
                f"{query} stakeholder response {local_context.key_stakeholders}",
                f"{query} implementation challenges"
            ],
            focus_areas=["ordinance examples", "economic impact", "stakeholder responses"],
            specific_jurisdictions=[]
        )
        
        print(f"Generated research plan with {len(research_plan.search_queries)} search queries.")
        
        # Perform web searches based on research plan
        results = ResearchResults(
            successful_implementations=[],
            example_ordinances=[],
            effectiveness_evidence=[],
            stakeholder_responses={},
            implementation_challenges=[]
        )
        
        print("Executing web searches...")
        
        all_search_results = []
        
        # Perform actual web searches
        for i, search_query in enumerate(research_plan.search_queries):
            print(f"  Search {i+1}/{len(research_plan.search_queries)}: {search_query}")
            
            # Use the web search API to get results
            search_result = await web_search_api(search_query)
            all_search_results.append(search_result)
            
            # Process individual search results
            if "organic_results" in search_result:
                for result in search_result["organic_results"][:3]:  # Limit to top 3 results
                    if "example" in search_query and "ordinance" in search_query:
                        results.example_ordinances.append({
                            "title": result.get("title", ""),
                            "summary": result.get("snippet", ""),
                            "source": result.get("link", "")
                        })
                    
                    elif "successful" in search_query and "implementations" in search_query:
                        results.successful_implementations.append(
                            f"{result.get('title', '')}: {result.get('snippet', '')}"
                        )
                    
                    elif "economic impact" in search_query:
                        results.effectiveness_evidence.append(
                            f"{result.get('title', '')}: {result.get('snippet', '')}"
                        )
                    
                    elif "stakeholder" in search_query:
                        stakeholder_type = "general"
                        if "business" in search_query or "retailer" in search_query:
                            stakeholder_type = "businesses"
                        elif "consumer" in search_query or "resident" in search_query:
                            stakeholder_type = "residents"
                        elif "environmental" in search_query:
                            stakeholder_type = "environmental_groups"
                        
                        if stakeholder_type not in results.stakeholder_responses:
                            results.stakeholder_responses[stakeholder_type] = []
                        
                        results.stakeholder_responses[stakeholder_type].append(
                            f"{result.get('title', '')}: {result.get('snippet', '')}"
                        )
                    
                    elif "challenge" in search_query or "implementation" in search_query:
                        results.implementation_challenges.append(
                            f"{result.get('title', '')}: {result.get('snippet', '')}"
                        )
        
        # Synthesize the research findings
        synthesize_prompt = (
            f"Policy Query: {query}\n\n"
            f"Research Findings:\n"
            f"- Successful Implementations: {json.dumps(results.successful_implementations)}\n"
            f"- Example Ordinances: {json.dumps(results.example_ordinances)}\n"
            f"- Effectiveness Evidence: {json.dumps(results.effectiveness_evidence)}\n"
            f"- Stakeholder Responses: {json.dumps(results.stakeholder_responses)}\n"
            f"- Implementation Challenges: {json.dumps(results.implementation_challenges)}\n\n"
            f"Based on these research findings, provide a concise synthesis of key insights for policy design."
        )
        
        print("Web research completed. Synthesizing findings...")
        
        # For simplicity in this example, we'll skip running another agent call
        # But in a real implementation, you would have an agent synthesize the findings
        
        return results

    async def _generate_initial_proposals(self, query: str, local_context: LocalContext, research_results: ResearchResults):
        """Generate the initial set of policy proposals informed by context and research."""
        print("Generating initial policy proposals...")
        
        # Use span wrapper instead of directly calling custom_span
        with custom_span("Initial Policy Generation", parent=self.current_trace) as span:
            # Prepare the generation prompt with context and research
            generation_prompt = (
                f"Policy Query: {query}\n\n"
                f"LOCAL CONTEXT (IMPORTANT - CUSTOMIZE PROPOSALS FOR THIS SPECIFIC CONTEXT):\n"
                f"- Jurisdiction: {local_context.jurisdiction_type} (Population: {local_context.population_size})\n"
                f"- Economic Context: {local_context.economic_context}\n"
                f"- Existing Policies: {local_context.existing_policies}\n"
                f"- Political Landscape: {local_context.political_landscape}\n"
                f"- Budget Constraints: {local_context.budget_constraints}\n"
                f"- Local Challenges: {local_context.local_challenges}\n"
                f"- Key Stakeholders: {local_context.key_stakeholders}\n"
                f"- Demographics: {local_context.demographic_profile}\n"
                f"- Prior Policy Attempts: {local_context.prior_attempts}\n\n"
                f"RESEARCH FINDINGS:\n"
                f"- Successful Implementations: {json.dumps(research_results.successful_implementations)[:300]}...\n"
                f"- Example Ordinances: {json.dumps(research_results.example_ordinances)[:300]}...\n"
                f"- Stakeholder Responses: {json.dumps(research_results.stakeholder_responses)[:300]}...\n\n"
                f"Generate 4-6 diverse, innovative policy proposals for: {query}\n\n"
                f"Each proposal should include:\n"
                f"1. A descriptive title\n"
                f"2. A detailed description of the policy mechanism\n"
                f"3. A rationale explaining why it will be effective\n"
                f"4. Analysis of impacts on different stakeholder groups\n"
                f"5. Potential implementation challenges\n"
                f"6. Equity considerations\n"
                f"7. Economic analysis including costs and benefits\n\n"
                f"IMPORTANT: Make proposals HIGHLY RELEVANT to {local_context.jurisdiction_type} jurisdiction with {local_context.population_size} population and {local_context.political_landscape} political landscape."
            )
            
            # Generate the initial policy proposals
            policy_result = await Runner.run(
                policy_generation_agent,
                generation_prompt,
            )
            
            # Convert the result to a batch of proposals
            proposal_batch = policy_result.final_output_as(PolicyProposalBatch)
            
            # Add proposals to our collection, converting from Pydantic models to dataclasses
            for proposal_model in proposal_batch.proposals:
                # Create empty dicts/lists for None values
                stakeholder_impacts = proposal_model.stakeholder_impacts if proposal_model.stakeholder_impacts is not None else {}
                implementation_challenges = proposal_model.implementation_challenges if proposal_model.implementation_challenges is not None else []
                equity_considerations = proposal_model.equity_considerations if proposal_model.equity_considerations is not None else ""
                economic_analysis = proposal_model.economic_analysis if proposal_model.economic_analysis is not None else ""
                
                # Convert to our internal PolicyProposal dataclass
                proposal = PolicyProposal(
                    id=proposal_model.id,
                    title=proposal_model.title,
                    description=proposal_model.description,
                    rationale=proposal_model.rationale,
                    stakeholder_impacts=stakeholder_impacts,
                    implementation_challenges=implementation_challenges,
                    equity_considerations=equity_considerations,
                    economic_analysis=economic_analysis
                )
                self.proposals[proposal.id] = proposal
            
            print(f"Generated {len(proposal_batch.proposals)} initial policy proposals")
    
    async def _run_tournament(self):
        """Run a tournament to compare and rank policy proposals."""
        print("\n--- Running Policy Tournament ---\n")
        
        with custom_span("Policy Tournament", parent=self.current_trace) as span:
            # Create a tournament trace span that will be the parent of all comparison spans
            trace_processor = get_trace_processor()
            tournament_span_id = None
            
            if trace_processor and self.trace_id:
                tournament_span_id = trace_processor.record_agent_interaction(
                    trace_id=self.trace_id,
                    agent_name="Tournament Manager",
                    input_text=f"Running tournament with {self.tournament_rounds} rounds",
                    output_text=f"Tournament started with {len(self.proposals)} proposals",
                    span_type="tournament_management",
                    model="system"
                )
            
            proposal_ids = list(self.proposals.keys())
            
            for round_num in range(self.tournament_rounds):
                print(f"  Tournament round {round_num + 1}/{self.tournament_rounds}")
                
                # Create a round span for this specific tournament round
                round_span_id = None
                if trace_processor and self.trace_id:
                    round_span_id = trace_processor.record_agent_interaction(
                        trace_id=self.trace_id,
                        agent_name="Tournament Round Manager",
                        input_text=f"Tournament round {round_num + 1}/{self.tournament_rounds}",
                        output_text=f"Running round {round_num + 1} with {len(proposal_ids)} proposals",
                        span_type="tournament_round",
                        model="system",
                        parent_span_id=tournament_span_id
                    )
                
                # Randomly pair proposals for comparison
                random.shuffle(proposal_ids)
                
                for i in range(0, len(proposal_ids) - 1, 2):
                    if i + 1 >= len(proposal_ids):
                        break
                    
                    proposal_a_id = proposal_ids[i]
                    proposal_b_id = proposal_ids[i + 1]
                    
                    # Get the full text of each proposal
                    proposal_a_text = self.proposals[proposal_a_id].full_text()
                    proposal_b_text = self.proposals[proposal_b_id].full_text()
                    
                    winner_text = await self._compare_proposals(proposal_a_text, proposal_b_text, self.trace_id, round_span_id)
                    
                    # Determine winner based on text matching
                    winner_id = proposal_a_id if winner_text == proposal_a_text else proposal_b_id
                    loser_id = proposal_b_id if winner_text == proposal_a_text else proposal_a_id
                    
                    # Update Elo ratings
                    self.elo_system.update_rating(winner_id, loser_id)
                    
                    print(f"    Comparison: {self.proposals[proposal_a_id].title} vs {self.proposals[proposal_b_id].title}")
                    print(f"    Winner: {self.proposals[winner_id].title}")
    
    async def _compare_proposals(self, policy1: str, policy2: str, trace_id: str, parent_span_id: str = None) -> str:
        """Compare two policy proposals and return the better one."""
        
        # Get trace processor instance
        trace_processor = get_trace_processor()
        
        comparison_instructions = """Compare two policy proposals to determine which is more effective and equitable.
            Evaluate based on practicality, impact, cost-effectiveness, and alignment with local needs."""
        
        comparison_prompt = f"""Policy Comparison: Policy 1: {policy1}

        Policy 2: {policy2}

        Compare these policies based on:
        1. Effectiveness in addressing the core problem
        2. Equity and fairness considerations
        3. Implementation feasibility
        4. Cost-effectiveness
        5. Alignment with local context and needs

        Which policy is superior and why? Consider both immediate impact and long-term sustainability.
        """
        
        # Run the comparison through the model
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": comparison_instructions},
                {"role": "user", "content": comparison_prompt}
            ],
            temperature=0.7
        )
        
        # Extract token usage and response ID
        tokens_used = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        # Record the comparison in our trace if we have a trace processor
        if trace_processor:
            trace_processor.record_agent_interaction(
                trace_id=trace_id,
                agent_name="Policy Comparison Agent",
                input_text=comparison_prompt,
                output_text=response.choices[0].message.content,
                span_type="policy_comparison",
                parent_span_id=parent_span_id,
                model="gpt-4-turbo-preview",
                system_instructions=comparison_instructions,
                tokens_used=tokens_used,
                metadata={"openai_response_id": response.id}
            )
        
        # Parse the response to determine the winner
        output_text = response.choices[0].message.content.lower()
        
        # Simple heuristic - check which policy is mentioned more positively
        policy1_score = output_text.count("policy 1") + output_text.count("first policy")
        policy2_score = output_text.count("policy 2") + output_text.count("second policy")
        
        return policy1 if policy1_score > policy2_score else policy2
    
    async def _evolve_top_proposals(self):
        """Evolve the top-performing policy proposals."""
        print("\n--- Evolving Top Policies ---\n")
        
        with custom_span("Policy Evolution", parent=self.current_trace) as span:
            # Get the top-performing proposals to evolve
            top_proposals = self._get_top_proposals(self.evolution_candidates)
            
            for proposal in top_proposals:
                evolution_input = (
                    f"Evolve and improve this policy proposal:\n\n"
                    f"ID: {proposal.id}\n"
                    f"Title: {proposal.title}\n"
                    f"Description: {proposal.description}\n"
                    f"Rationale: {proposal.rationale}\n\n"
                    f"Create a significantly improved version while maintaining its core intent."
                )
                
                evolution_result = await Runner.run(
                    policy_evolution_agent,
                    evolution_input,
                )
                
                result = evolution_result.final_output_as(EvolutionResult)
                
                # Create empty dicts/lists for None values
                stakeholder_impacts = result.evolved_proposal.stakeholder_impacts if result.evolved_proposal.stakeholder_impacts is not None else {}
                implementation_challenges = result.evolved_proposal.implementation_challenges if result.evolved_proposal.implementation_challenges is not None else []
                equity_considerations = result.evolved_proposal.equity_considerations if result.evolved_proposal.equity_considerations is not None else ""
                economic_analysis = result.evolved_proposal.economic_analysis if result.evolved_proposal.economic_analysis is not None else ""
                
                # Create a new policy proposal with the evolved information
                evolved_proposal = PolicyProposal(
                    id=f"{result.original_id}_evolved_{self.generation_count}",
                    title=result.evolved_proposal.title,
                    description=result.evolved_proposal.description,
                    rationale=result.evolved_proposal.rationale,
                    stakeholder_impacts=stakeholder_impacts,
                    implementation_challenges=implementation_challenges,
                    equity_considerations=equity_considerations,
                    economic_analysis=economic_analysis,
                    generation=self.generation_count
                )
                
                # Add the evolved proposal to our collection
                self.proposals[evolved_proposal.id] = evolved_proposal
                
                # Print evolution information
                print(f"  Evolved: {proposal.title} -> {evolved_proposal.title}")
                
                # Truncate improvements text if too long
                improvements_text = result.improvements
                if len(improvements_text) > 100:
                    improvements_text = improvements_text[:100] + "..."
                    
                print(f"  Improvements: {improvements_text}")
    
    async def _create_final_report(self, query: str, local_context: LocalContext, research_results: ResearchResults) -> FinalReportModel:
        """Create a final policy report incorporating local context and research findings."""
        print("\n--- Creating Final Policy Report ---\n")
        
        # DEBUG: Print local context to verify it's properly passed to this function
        print("\n[DEBUG] Local context in final report creation:")
        for attr, value in local_context.__dict__.items():
            if attr != "_sa_instance_state" and attr != "stakeholder_influence":
                print(f"  {attr}: {value}")
        
        with custom_span("Final Policy Report", parent=self.current_trace) as span:
            # Get the top-rated proposals
            top_proposals = self._get_top_proposals(3)
            
            # Create a policy comparison matrix for stakeholder impacts
            impact_matrix = []
            for proposal in top_proposals:
                impact_row = {
                    "policy": proposal.title,
                    "environmental_impact": "High" if "environment" in proposal.description.lower() else "Medium",
                    "economic_feasibility": "Medium" if "cost" in proposal.description.lower() else "High",
                    "equity": "High" if hasattr(proposal, "equity_considerations") and proposal.equity_considerations else "Medium",
                    "implementation_complexity": "Medium" if hasattr(proposal, "implementation_challenges") and proposal.implementation_challenges else "High",
                }
                impact_matrix.append(impact_row)
            
            # Collect stakeholder impacts across all top proposals
            stakeholder_analysis = {
                "small_businesses": [],
                "large_retailers": [],
                "low_income_residents": [],
                "environmental_groups": [],
                "local_government": [],
                "manufacturers": [],
            }
            
            # Default stakeholder impacts if not provided in the policy proposals
            default_impacts = {
                "small_businesses": "May face initial adaptation challenges but benefit from level playing field",
                "large_retailers": "Have resources to adapt but may need to adjust supply chains",
                "low_income_residents": "Need protection from potential price increases or access issues",
                "environmental_groups": "Generally supportive but may push for stronger measures",
                "local_government": "Responsible for implementation and enforcement",
                "manufacturers": "Need to adapt product lines and materials",
            }
            
            # Fill in stakeholder analysis
            for proposal in top_proposals:
                for stakeholder in stakeholder_analysis:
                    impact = proposal.stakeholder_impacts.get(stakeholder, default_impacts[stakeholder])
                    stakeholder_analysis[stakeholder].append(f"{proposal.title}: {impact}")
            
            # Convert internal dataclass proposals to Pydantic models for API
            top_proposal_models = []
            for proposal in top_proposals:
                # Create empty dicts/lists for None values
                stakeholder_impacts = proposal.stakeholder_impacts if hasattr(proposal, 'stakeholder_impacts') else {}
                implementation_challenges = proposal.implementation_challenges if hasattr(proposal, 'implementation_challenges') else []
                equity_considerations = proposal.equity_considerations if hasattr(proposal, 'equity_considerations') else ""
                economic_analysis = proposal.economic_analysis if hasattr(proposal, 'economic_analysis') else ""
                
                # Create the model with safe values
                proposal_model = PolicyProposalModel(
                    id=proposal.id,
                    title=proposal.title,
                    description=proposal.description,
                    rationale=proposal.rationale,
                    stakeholder_impacts=stakeholder_impacts,
                    implementation_challenges=implementation_challenges,
                    equity_considerations=equity_considerations,
                    economic_analysis=economic_analysis
                )
                top_proposal_models.append(proposal_model)
            
            # Check if policy proposals mention the specific jurisdiction or local context
            local_context_referenced = False
            jurisdiction = local_context.jurisdiction_type
            
            if jurisdiction != "Not specified":
                for model in top_proposal_models:
                    if (jurisdiction.lower() in model.title.lower() or 
                        jurisdiction.lower() in model.description.lower() or 
                        jurisdiction.lower() in model.rationale.lower()):
                        local_context_referenced = True
                        break
            
            # Generate the final report with enhanced stakeholder analysis
            report_input = (
                f"Policy Query: {query}\n\n"
                f"LOCAL CONTEXT (CRITICAL FOR REPORT CUSTOMIZATION):\n"
                f"- Jurisdiction: {local_context.jurisdiction_type} (Population: {local_context.population_size})\n"
                f"- Economic Context: {local_context.economic_context}\n"
                f"- Existing Policies: {local_context.existing_policies}\n"
                f"- Political Landscape: {local_context.political_landscape}\n"
                f"- Budget Constraints: {local_context.budget_constraints}\n"
                f"- Local Challenges: {local_context.local_challenges}\n"
                f"- Key Stakeholders: {local_context.key_stakeholders}\n"
                f"- Demographics: {local_context.demographic_profile}\n"
                f"- Prior Policy Attempts: {local_context.prior_attempts}\n\n"
            )
            
            # Add stronger instructions if the local context wasn't referenced in proposals
            if not local_context_referenced and jurisdiction != "Not specified":
                report_input += (
                    f"SPECIAL INSTRUCTIONS (IMPORTANT):\n"
                    f"The policy proposals do not adequately reference the specific local context of {jurisdiction}. "
                    f"YOUR TASK IS TO EXPLICITLY LOCALIZE ALL RECOMMENDATIONS IN YOUR REPORT TO {jurisdiction.upper()}. "
                    f"Every section of your report must directly reference {jurisdiction} and tailor recommendations "
                    f"to its unique circumstances, including specific references to:\n"
                    f"- The economic landscape of {jurisdiction}: {local_context.economic_context}\n"
                    f"- Political realities in {jurisdiction}: {local_context.political_landscape}\n"
                    f"- Unique local challenges of {jurisdiction}: {local_context.local_challenges}\n"
                    f"- Key stakeholders in {jurisdiction}: {local_context.key_stakeholders}\n\n"
                )
            else:
                report_input += (
                    f"INSTRUCTIONS:\n"
                    f"Create a comprehensive policy report that directly addresses the specific context of {local_context.jurisdiction_type} "
                    f"with its unique economic factors ({local_context.economic_context}), "
                    f"political considerations ({local_context.political_landscape}), and "
                    f"local challenges ({local_context.local_challenges}).\n\n"
                    f"The report MUST reflect these contextual factors throughout all sections. "
                    f"Every recommendation should consider budget constraints: {local_context.budget_constraints}\n\n"
                )
            
            report_input += (
                f"Top Policy Proposals: {json.dumps([model_to_dict(model) for model in top_proposal_models], indent=2)}\n\n"
                f"Impact Matrix: {json.dumps(impact_matrix, indent=2)}\n\n"
                f"Stakeholder Analysis: {json.dumps(stakeholder_analysis, indent=2)}"
            )
            
            # DEBUG: Log a sample of the report input to verify local context is included
            print("\n[DEBUG] Sample of report input (first 500 chars):")
            print(report_input[:500])
            
            final_report = await Runner.run(
                policy_report_agent,
                report_input,
            )
            
            print("Final policy report created")
            return final_report.final_output_as(FinalReportModel)
    
    def _get_top_proposals(self, n: int) -> List[PolicyProposal]:
        """Get the top N proposals based on Elo rating."""
        # Sort proposals by Elo rating
        sorted_proposals = sorted(
            self.proposals.values(),
            key=lambda p: self.elo_system.get_rating(p.id),
            reverse=True
        )
        
        # Return top N (or all if fewer than N)
        return sorted_proposals[:min(n, len(sorted_proposals))]

def model_to_dict(model):
    """Convert a Pydantic model to dict, compatible with both v1 and v2."""
    if hasattr(model, 'model_dump'):
        return model.model_dump()
    else:
        return model.dict()

# Main entry point
async def run_policy_evolution(query: str) -> FinalReportModel:
    """Run the policy evolution process on a query."""
    manager = PolicyEvolutionManager()
    return await manager.run(query)

# Command-line interface
if __name__ == "__main__":
    query = input("Enter your policy question: ")
    report = asyncio.run(run_policy_evolution(query))
    
    print("\n" + "="*80)
    print("FINAL POLICY REPORT")
    print("="*80 + "\n")
    print(f"Summary: {report.summary}\n")
    
    print("Top Proposals:")
    for i, proposal in enumerate(report.top_proposals, 1):
        print(f"{i}. {proposal.title}")
        print(f"   {proposal.description[:100]}...")
    
    print("\nKey Considerations:")
    for i, consideration in enumerate(report.key_considerations, 1):
        print(f"{i}. {consideration}")

def main():
    """Main function for the policy evolution page when run from the app."""
    st.title("Policy Evolution")
    
    st.write("""
    Generate and evolve policy proposals through a tournament process.
    This advanced analysis develops multiple policy options and evaluates them competitively to find the strongest solutions.
    """)
    
    query = st.text_area("Enter your policy question:", placeholder="Example: How can our city incentivize renewable energy adoption?")
    
    # Optional local context settings
    with st.expander("Local Context Settings (Optional)"):
        col1, col2 = st.columns(2)
        with col1:
            jurisdiction_type = st.selectbox("Jurisdiction Type", 
                                           ["City", "County", "State", "Township", "Village", "Special District"])
            population = st.text_input("Population Size", placeholder="e.g. 120,000")
            economic_context = st.text_input("Economic Context", placeholder="e.g. Manufacturing, Service, Tourism")
            
        with col2:
            budget = st.text_input("Budget Constraints", placeholder="e.g. $50,000 annual sustainability budget")
            politics = st.text_input("Political Landscape", placeholder="e.g. Progressive council, upcoming election")
            key_stakeholders = st.text_input("Key Stakeholders", placeholder="e.g. Businesses, residents, environmental groups")
    
    if st.button("Run Policy Evolution"):
        if query:
            with st.spinner("Evolving policy options through multiple generations..."):
                try:
                    report = asyncio.run(run_policy_evolution(query))
                    st.session_state.evolution_report = report
                    st.success("Policy evolution complete!")
                except Exception as e:
                    st.error(f"Error in policy evolution: {str(e)}")
        else:
            st.warning("Please enter a policy question.")
    
    # Display results if available
    if 'evolution_report' in st.session_state:
        report = st.session_state.evolution_report
        
        st.subheader("Policy Evolution Results")
        st.markdown(f"**Summary:** {report.summary}")
        
        st.subheader("Top Policy Proposals")
        for i, proposal in enumerate(report.top_proposals, 1):
            with st.expander(f"{i}. {proposal.title}"):
                st.write(f"**Description:** {proposal.description}")
                st.write(f"**Rationale:** {proposal.rationale}")
                
                if proposal.stakeholder_impacts:
                    st.subheader("Stakeholder Impacts")
                    for stakeholder, impact in proposal.stakeholder_impacts.items():
                        st.write(f"**{stakeholder}:** {impact}")
                
                if proposal.implementation_challenges:
                    st.subheader("Implementation Challenges")
                    for challenge in proposal.implementation_challenges:
                        st.write(f"- {challenge}")
        
        st.subheader("Key Considerations")
        for consideration in report.key_considerations:
            st.markdown(f"- {consideration}")
        
        st.subheader("Implementation Steps")
        for i, step in enumerate(report.implementation_steps, 1):
            st.markdown(f"{i}. {step}")
        
        # Option to save to dashboard
        if st.button("Save to Dashboard"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"policy_evolution_{timestamp}.md"
            
            # Get the user's Downloads folder path
            home_dir = os.path.expanduser("~")
            downloads_dir = os.path.join(home_dir, "Downloads")
            file_path = os.path.join(downloads_dir, filename)
            
            # Create markdown for the report
            md_content = f"# Policy Evolution: {query}\n\n"
            md_content += f"## Executive Summary\n\n{report.summary}\n\n"
            md_content += "## Top Policy Proposals\n\n"
            
            for i, proposal in enumerate(report.top_proposals, 1):
                md_content += f"### {i}. {proposal.title}\n\n"
                md_content += f"{proposal.description}\n\n"
                md_content += f"**Rationale**: {proposal.rationale}\n\n"
            
            md_content += "## Key Considerations\n\n"
            for consideration in report.key_considerations:
                md_content += f"- {consideration}\n"
            
            md_content += "\n## Implementation Steps\n\n"
            for i, step in enumerate(report.implementation_steps, 1):
                md_content += f"{i}. {step}\n"
            
            # Save the file to Downloads folder
            try:
                with open(file_path, "w") as f:
                    f.write(md_content)
                st.success(f"Policy evolution report saved to your Downloads folder: {filename}")
            except Exception as e:
                st.error(f"Error saving file: {str(e)}")
                # Fallback to saving in current directory if Downloads folder isn't accessible
                fallback_path = filename
                with open(fallback_path, "w") as f:
                    f.write(md_content)
                st.warning(f"Couldn't save to Downloads folder. Saved to current directory instead: {fallback_path}")

async def orchestrate_policy_analysis(query: str, context: LocalContext) -> dict:
    """Orchestrate multiple specialized LLMs in parallel processes"""
    
    # DEBUG: Log the context at the start of orchestration
    print("\n[DEBUG] Starting orchestration with context:")
    for attr, value in context.__dict__.items():
        if attr != "_sa_instance_state" and attr != "stakeholder_influence":
            print(f"  {attr}: {value}")
    
    # Step 1: Initial research plan (using a fast model)
    print("\n[DEBUG] Running planning agent with query:", query)
    planning_result = await Runner.run(planning_agent, query)
    
    # DEBUG: Log the planning result
    print(f"\n[DEBUG] Planning result obtained. Search items: {len(planning_result.final_output.get('searches', []))}")
    
    # Step 2: Parallel research and analysis tasks (multiple models with different strengths)
    research_tasks = []
    for search_item in planning_result.final_output.get('searches', []):
        print(f"\n[DEBUG] Creating research task for: {search_item}")
        research_tasks.append(
            asyncio.create_task(perform_targeted_research(search_item, context))
        )
    
    # Also run policy precedent analysis in parallel
    print(f"\n[DEBUG] Creating precedent analysis task for jurisdiction: {context.jurisdiction_type}")
    research_tasks.append(
        asyncio.create_task(analyze_policy_precedents(query, context.jurisdiction_type))
    )
    
    # Step 3: Gather all research results
    print(f"\n[DEBUG] Gathering {len(research_tasks)} research tasks")
    research_results = await asyncio.gather(*research_tasks)
    
    # DEBUG: Log research results summary
    print(f"\n[DEBUG] Gathered {len(research_results)} research results")
    
    # Step 4: Have a synthesis model integrate findings
    synthesis_prompt = create_synthesis_prompt(query, research_results, context)
    
    # DEBUG: Log synthesis prompt sample
    print("\n[DEBUG] Synthesis prompt sample (first 300 chars):")
    print(synthesis_prompt[:300])
    
    synthesis_result = await Runner.run(synthesis_agent, synthesis_prompt)
    
    # Step 5: Generate three competing policy approaches using tournament method
    print("\n[DEBUG] Starting policy tournament with context from jurisdiction:", context.jurisdiction_type)
    policy_options = await generate_policy_tournament(
        synthesis_result.final_output, 
        context,
        rounds=7  # Increased from 5 for more thorough comparison
    )
    
    return {
        "research": research_results,
        "synthesis": synthesis_result.final_output,
        "policy_options": policy_options
    }

# Supporting functions for the orchestration

async def perform_targeted_research(search_item: str, context: LocalContext) -> dict:
    """Perform targeted research on a specific search item"""
    # This would be implemented to use a specialized research agent
    research_agent = Agent(
        name="Research specialist",
        model="gpt-4o",
        instructions="Specialized for deep research on policy topics"
    )
    
    research_prompt = (
        f"Conduct targeted research on '{search_item}' specifically for "
        f"{context.jurisdiction_type} with population {context.population_size}. "
        f"Consider economic context: {context.economic_context}. "
        f"Focus on finding relevant precedents, case studies, and outcome data."
    )
    
    result = await Runner.run(research_agent, research_prompt)
    return {
        "search_term": search_item,
        "findings": result.final_output,
        "source_quality": "high" if "academic" in result.final_output.lower() else "medium"
    }

async def analyze_policy_precedents(query: str, jurisdiction_type: str) -> dict:
    """Analyze policy precedents for similar jurisdictions"""
    # This would use a model specialized in legal/policy analysis
    precedent_agent = Agent(
        name="Policy precedent analyzer",
        model="gpt-4o",
        instructions="Specialized for analyzing policy precedents and legal frameworks"
    )
    
    precedent_prompt = (
        f"Analyze existing policy precedents related to '{query}' "
        f"specifically for {jurisdiction_type} jurisdictions. "
        f"Focus on identifying legal frameworks, constitutional limits, "
        f"and successful past implementations in similar contexts."
    )
    
    result = await Runner.run(precedent_agent, precedent_prompt)
    return {
        "precedents": result.final_output,
        "jurisdiction_relevance": "high" if jurisdiction_type.lower() in result.final_output.lower() else "medium"
    }

def create_synthesis_prompt(query: str, research_results: list, context: LocalContext) -> str:
    """Create a synthesis prompt from research results"""
    research_summary = "\n\n".join([
        f"Research on '{r.get('search_term', 'policy precedents')}': {r.get('findings', r.get('precedents', ''))}"
        for r in research_results
    ])
    
    return (
        f"Synthesize the following research about '{query}' for {context.jurisdiction_type} "
        f"with population {context.population_size} and political landscape: {context.political_landscape}.\n\n"
        f"Consider budget constraints: {context.budget_constraints}\n\n"
        f"RESEARCH FINDINGS:\n{research_summary}\n\n"
        f"Create a comprehensive synthesis that identifies key themes, contradictions, "
        f"and promising approaches across all research. Focus on what's most relevant "
        f"for this specific jurisdiction context."
    )

async def generate_policy_tournament(synthesis: str, context: LocalContext, rounds: int = 7) -> list:
    """Generate competing policy approaches and run a tournament to find the best"""
    # Generate initial policy options
    policy_agent = Agent(
        name="Policy designer",
        model="gpt-4o",
        instructions="Specialized for creative policy design"
    )
    
    # Generate three distinct policy approaches
    policy_generation_prompt = (
        f"Based on this synthesis: '{synthesis[:1000]}...', "
        f"generate three distinct policy approaches for {context.jurisdiction_type} "
        f"addressing different stakeholder priorities, implementation timelines, and costs. "
        f"Each policy should be realistic within budget constraints: {context.budget_constraints} "
        f"and political landscape: {context.political_landscape}."
    )
    
    initial_policies = await Runner.run(policy_agent, policy_generation_prompt)
    
    # Run tournament
    tournament_agent = Agent(
        name="Policy evaluator",
        model="gpt-4o",
        instructions="Specialized for critical policy evaluation"
    )
    
    policies = initial_policies.final_output
    for _ in range(rounds):
        # Select two random policies to compare
        policy_1, policy_2 = random.sample(policies, 2)
        
        comparison_prompt = (
            f"Compare these two policy approaches for {context.jurisdiction_type}:\n\n"
            f"POLICY A: {policy_1}\n\n"
            f"POLICY B: {policy_2}\n\n"
            f"Consider feasibility, stakeholder support, cost-effectiveness, and equity. "
            f"Which policy is stronger overall and why? Return your answer in this format: "
            f"WINNER: [A or B]\nREASONING: [detailed reasoning]"
        )
        
        result = await Runner.run(tournament_agent, comparison_prompt)
        
        # Update policies based on winner's strengths and loser's weaknesses
        if "WINNER: A" in result.final_output:
            winner, loser = policy_1, policy_2
        else:
            winner, loser = policy_2, policy_1
            
        # Evolve the weaker policy
        evolution_prompt = (
            f"Evolve this policy approach: {loser}\n\n"
            f"Incorporate these strengths from a competing policy: {winner}\n\n"
            f"Create an improved version that addresses the weaknesses while maintaining "
            f"its unique perspective and approach."
        )
        
        evolved_policy = await Runner.run(policy_agent, evolution_prompt)
        
        # Replace the loser with the evolved policy
        policies = [p if p != loser else evolved_policy.final_output for p in policies]
    
    return policies 