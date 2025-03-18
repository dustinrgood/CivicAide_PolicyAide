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
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the agents SDK
from src.agents import Agent, Runner, ItemHelpers, trace, custom_span, gen_trace_id

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
        
        # Fallback or mock results
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
        # Initialize trace with a unique ID
        trace_id = gen_trace_id()
        self.trace_id = trace_id
        
        # Use the trace context manager to properly set up tracing
        with trace("Policy Evolution Process", trace_id=trace_id) as current_trace:
            self.current_trace = current_trace
            print(f"\n{'='*60}")
            print(f"CivicAide Policy Evolution System - Mimicking Google's AI Co-Scientist")
            print(f"{'='*60}\n")
            print(f"Policy Query: {query}\n")
            print(f"Trace ID: {trace_id}")
            
            # Step 1: Gather local context
            local_context = await self._gather_local_context(query)
            
            # Step 2: Conduct web research based on local context
            research_results = await self._conduct_web_research(query, local_context)
            
            # Step 3: Generate initial policy proposals informed by research and context
            for generation in range(self.max_generations):
                print(f"\n--- Generation {generation+1} ---\n")
                self.generation_count = generation + 1
                
                # Step 3a: Generate initial proposals or evolve existing ones
                if generation == 0:
                    await self._generate_initial_proposals(query, local_context, research_results)
                else:
                    await self._evolve_top_proposals()
                
                # Step 3b: Run a tournament to compare and rank proposals
                await self._run_tournament()
                
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
            
            return final_report
    
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
            f"7. Who are the key stakeholders that would be affected by this policy?"
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
            "key_stakeholders": ""
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
        except Exception as e:
            print(f"Error collecting input: {e}")
            # Provide default values if input fails
            for key in responses:
                if not responses[key]:
                    responses[key] = "Not specified"
        
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
        
        # Make sure all fields have values
        for key in responses:
            if not responses[key]:
                responses[key] = "Not specified"
        
        # Print the collected responses for verification
        print("\nCollected context information:")
        for key, value in responses.items():
            print(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Create context object
        try:
            local_context = LocalContext(**responses)
            print("\nLocal context information gathered successfully.")
            return local_context
        except Exception as e:
            print(f"Error creating local context: {e}")
            # Create a fallback context with default values
            fallback_context = LocalContext(
                jurisdiction_type="Not specified",
                population_size="Not specified",
                economic_context="Not specified",
                existing_policies="Not specified",
                political_landscape="Not specified",
                budget_constraints="Not specified",
                local_challenges="Not specified",
                key_stakeholders="Not specified"
            )
            print("Using default context values due to input error.")
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
        
        with custom_span("Initial Policy Generation", parent=self.current_trace):
            # Prepare the generation prompt with context and research
            generation_prompt = (
                f"Policy Query: {query}\n\n"
                f"Local Context:\n"
                f"- Jurisdiction: {local_context.jurisdiction_type} (Population: {local_context.population_size})\n"
                f"- Economic Context: {local_context.economic_context}\n"
                f"- Existing Policies: {local_context.existing_policies}\n"
                f"- Political Landscape: {local_context.political_landscape}\n"
                f"- Budget Constraints: {local_context.budget_constraints}\n"
                f"- Local Challenges: {local_context.local_challenges}\n"
                f"- Key Stakeholders: {local_context.key_stakeholders}\n\n"
                f"Based on this policy query and local context, generate diverse policy proposals."
            )
            
            generation_result = await Runner.run(
                policy_generation_agent,
                generation_prompt,
            )
            
            proposal_batch = generation_result.final_output_as(PolicyProposalBatch)
            
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
        
        with custom_span("Policy Tournament", parent=self.current_trace):
            proposal_ids = list(self.proposals.keys())
            
            for round_num in range(self.tournament_rounds):
                print(f"  Tournament round {round_num + 1}/{self.tournament_rounds}")
                
                # Randomly pair proposals for comparison
                random.shuffle(proposal_ids)
                
                for i in range(0, len(proposal_ids) - 1, 2):
                    if i + 1 >= len(proposal_ids):
                        break
                    
                    proposal_a_id = proposal_ids[i]
                    proposal_b_id = proposal_ids[i + 1]
                    
                    winner_id = await self._compare_proposals(proposal_a_id, proposal_b_id)
                    
                    # Update Elo ratings
                    self.elo_system.update_rating(winner_id, proposal_a_id if winner_id != proposal_a_id else proposal_b_id)
                    
                    print(f"    Comparison: {self.proposals[proposal_a_id].title} vs {self.proposals[proposal_b_id].title}")
                    print(f"    Winner: {self.proposals[winner_id].title}")
    
    async def _compare_proposals(self, proposal_id_1: str, proposal_id_2: str) -> str:
        """Compare two policy proposals and determine which is superior."""
        proposal_1 = self.proposals[proposal_id_1]
        proposal_2 = self.proposals[proposal_id_2]
        
        # Prepare the comparison prompt
        comparison_prompt = (
            f"Policy Comparison:\n\n"
            f"Policy 1: {proposal_1.title}\n{proposal_1.description}\n{proposal_1.rationale}\n\n"
            f"Policy 2: {proposal_2.title}\n{proposal_2.description}\n{proposal_2.rationale}\n\n"
            f"Compare these policies based on environmental impact, economic feasibility, "
            f"social equity, implementation complexity, and stakeholder acceptance across "
            f"different groups (small businesses, large retailers, low-income residents, "
            f"environmental groups, local government, manufacturers).\n\n"
            f"Which policy is more effective and equitable overall? Explain your reasoning."
        )
        
        # Run the comparison agent
        result = await Runner.run(comparison_agent, comparison_prompt)
        
        # Get the response text in a failsafe way by converting the entire result to string
        response_text = str(result)
        
        # Log the comparison
        print(f"    Comparison: {proposal_1.title} vs {proposal_2.title}")
        
        # Simple heuristic: The policy that appears more often in the last part is likely the winner
        policy1_mentions_in_conclusion = response_text[-500:].count("Policy 1") + response_text[-500:].count(proposal_1.title)
        policy2_mentions_in_conclusion = response_text[-500:].count("Policy 2") + response_text[-500:].count(proposal_2.title)
        
        if policy1_mentions_in_conclusion > policy2_mentions_in_conclusion:
            winner_id = proposal_id_1
            print(f"    Winner: {proposal_1.title}")
        else:
            winner_id = proposal_id_2
            print(f"    Winner: {proposal_2.title}")
        
        return winner_id
    
    async def _evolve_top_proposals(self):
        """Evolve the top-performing policy proposals."""
        print("\n--- Evolving Top Policies ---\n")
        
        with custom_span("Policy Evolution", parent=self.current_trace):
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
                
                # Convert the evolved Pydantic model to our internal dataclass
                evolved_proposal = PolicyProposal(
                    id=result.evolved_proposal.id,
                    title=result.evolved_proposal.title,
                    description=result.evolved_proposal.description,
                    rationale=result.evolved_proposal.rationale,
                    stakeholder_impacts=stakeholder_impacts,
                    implementation_challenges=implementation_challenges,
                    equity_considerations=equity_considerations,
                    economic_analysis=economic_analysis,
                    generation=proposal.generation + 1
                )
                
                # Add evolved proposal to our collection
                self.proposals[evolved_proposal.id] = evolved_proposal
                
                print(f"  Evolved: {proposal.title} -> {evolved_proposal.title}")
                print(f"  Improvements: {result.improvements[:100]}...")
    
    async def _create_final_report(self, query: str, local_context: LocalContext, research_results: ResearchResults) -> FinalReportModel:
        """Create a final policy report incorporating local context and research findings."""
        print("\n--- Creating Final Policy Report ---\n")
        
        with custom_span("Final Policy Report", parent=self.current_trace):
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
            
            # Generate the final report with enhanced stakeholder analysis
            report_input = (
                f"Policy Query: {query}\n\n"
                f"Local Context:\n"
                f"- Jurisdiction: {local_context.jurisdiction_type} (Population: {local_context.population_size})\n"
                f"- Economic Context: {local_context.economic_context}\n"
                f"- Existing Policies: {local_context.existing_policies}\n"
                f"- Political Landscape: {local_context.political_landscape}\n"
                f"- Budget Constraints: {local_context.budget_constraints}\n"
                f"- Local Challenges: {local_context.local_challenges}\n\n"
                f"Top Policy Proposals: {json.dumps([model_to_dict(model) for model in top_proposal_models], indent=2)}\n\n"
                f"Impact Matrix: {json.dumps(impact_matrix, indent=2)}\n\n"
                f"Stakeholder Analysis: {json.dumps(stakeholder_analysis, indent=2)}"
            )
            
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
    
    print(f"Executive Summary:\n{report.summary}\n")
    
    print("Top Policy Proposals:")
    for i, proposal in enumerate(report.top_proposals):
        print(f"\n{i+1}. {proposal.title}")
        print(f"   {proposal.description[:200]}...")
    
    print("\nKey Considerations:")
    for consideration in report.key_considerations:
        print(f"- {consideration}")
    
    print("\nImplementation Steps:")
    for i, step in enumerate(report.implementation_steps):
        print(f"{i+1}. {step}")
    
    # Ask if the user wants to save the report
    save_option = input("\nSave report to file? (y/n): ").lower().strip()
    if save_option.startswith('y'):
        from datetime import datetime
        
        default_filename = f"policy_evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filename = input(f"Enter filename (default: {default_filename}): ").strip()
        output_file = filename if filename else default_filename
        
        with open(output_file, 'w') as f:
            f.write(f"# Policy Evolution Report: {query}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"{report.summary}\n\n")
            
            f.write("## Top Policy Proposals\n\n")
            for i, proposal in enumerate(report.top_proposals):
                f.write(f"### {i+1}. {proposal.title}\n\n")
                f.write(f"{proposal.description}\n\n")
                f.write(f"**Rationale**: {proposal.rationale}\n\n")
            
            f.write("## Key Considerations\n\n")
            for consideration in report.key_considerations:
                f.write(f"- {consideration}\n")
            f.write("\n")
            
            f.write("## Implementation Steps\n\n")
            for i, step in enumerate(report.implementation_steps):
                f.write(f"{i+1}. {step}\n")
        
        print(f"\nReport saved to: {output_file}") 