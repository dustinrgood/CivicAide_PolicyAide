"""
Evolution agents for CivicAide policy system.

This module contains agent definitions specialized for policy evolution.
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field

# Import base agents and utilities
from src.civicaide.agents.base_agents import (
    web_search_agent,
    extract_json_from_markdown,
    parse_agent_output_as_json,
    StakeholderImpact,
    ImplementationStep
)

# Import the agents SDK
from agents import Agent, Runner
from pydantic import BaseModel, Field

# Models for policy evolution

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

# The ELO rating system for policy evolution
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

# Evolution-specific agents

policy_context_agent = Agent(
    name="Policy Context Agent",
    instructions=(
        "You gather local context information for policy development. Given a policy topic, "
        "identify key local factors that would affect policy implementation, including demographics, "
        "economic considerations, political landscape, existing regulations, and local stakeholders. "
        "Provide a comprehensive local context analysis that can inform policy creation."
    ),
    model="gpt-4o"
)

policy_creator_agent = Agent(
    name="Policy Creator Agent",
    instructions=(
        "Create innovative policy proposals based on a policy question and local context. "
        "For each proposal, include a detailed description, rationale, and potential stakeholder impacts. "
        "Generate diverse approaches that address the policy challenge from different perspectives. "
        "Return proposals in a structured JSON format."
    ),
    model="gpt-4o",
    output_type=PolicyProposalBatch
)

policy_comparison_agent = Agent(
    name="Policy Comparison Agent",
    instructions=(
        "Compare two policy proposals and determine which is superior. Consider feasibility, "
        "potential impact, equity considerations, cost-effectiveness, and stakeholder support. "
        "Provide detailed reasoning for your decision. Return a JSON object indicating the winner_id, "
        "loser_id, and reasoning for the decision."
    ),
    model="gpt-4o",
    output_type=ComparisonResult
)

policy_evolution_agent = Agent(
    name="Policy Evolution Agent",
    instructions=(
        "Evolve a policy proposal by improving its weaknesses and building on its strengths. "
        "Consider the feedback provided about similar proposals. Create an improved version that "
        "addresses implementation challenges, enhances stakeholder benefits, and increases feasibility. "
        "Return a JSON object with the original_id, evolved_proposal (with a new ID), and improvements."
    ),
    model="gpt-4o",
    output_type=EvolutionResult
)

final_report_agent = Agent(
    name="Final Report Agent",
    instructions=(
        "Create a comprehensive policy report based on the top-rated policy proposals. Include a "
        "concise summary, key considerations, implementation steps, stakeholder analysis, impact assessment, "
        "equity considerations, cost-benefit analysis, and alternative scenarios. Provide actionable "
        "recommendations that can be implemented by local government."
    ),
    model="gpt-4o",
    output_type=FinalReportModel
)

# Helper functions specific to policy evolution

async def create_initial_proposals(
    query: str, 
    local_context: str, 
    research_findings: Optional[List[str]] = None,
    count: int = 6
) -> List[PolicyProposalModel]:
    """
    Create initial policy proposals based on query, local context, and research.
    
    Args:
        query: The policy query
        local_context: Local context information
        research_findings: Optional research findings
        count: Number of proposals to generate
        
    Returns:
        List of policy proposals
    """
    # Prepare the input for the policy creator agent
    input_text = f"Policy Query: {query}\n\nLocal Context:\n{local_context}"
    
    if research_findings:
        input_text += "\n\nResearch Findings:\n"
        for i, finding in enumerate(research_findings, 1):
            input_text += f"{i}. {finding}\n"
    
    input_text += f"\nPlease generate {count} diverse policy proposals."
    
    # Run the agent to create proposals
    result = await Runner.run(policy_creator_agent, input=input_text)
    proposals_batch = result.final_output_as(PolicyProposalBatch)
    
    return proposals_batch.proposals

async def run_proposal_tournament(
    proposals: List[PolicyProposalModel],
    elo_system: EloRating
) -> List[Tuple[PolicyProposalModel, float]]:
    """
    Run a tournament to rank policy proposals using ELO ratings.
    
    Args:
        proposals: List of policy proposals
        elo_system: ELO rating system
        
    Returns:
        List of tuples containing (proposal, rating) sorted by rating
    """
    # Generate all possible pairs for comparison
    comparison_pairs = []
    proposal_ids = [p.id for p in proposals]
    
    for i in range(len(proposal_ids)):
        for j in range(i + 1, len(proposal_ids)):
            comparison_pairs.append((proposal_ids[i], proposal_ids[j]))
    
    # Shuffle the pairs to avoid bias
    random.shuffle(comparison_pairs)
    
    # Run the comparisons
    for id1, id2 in comparison_pairs:
        # Get the proposals
        proposal1 = next(p for p in proposals if p.id == id1)
        proposal2 = next(p for p in proposals if p.id == id2)
        
        # Format the input for the comparison agent
        input_text = (
            f"Compare these two policy proposals:\n\n"
            f"Proposal 1 (ID: {proposal1.id}):\n"
            f"Title: {proposal1.title}\n"
            f"Description: {proposal1.description}\n"
            f"Rationale: {proposal1.rationale}\n\n"
            f"Proposal 2 (ID: {proposal2.id}):\n"
            f"Title: {proposal2.title}\n"
            f"Description: {proposal2.description}\n"
            f"Rationale: {proposal2.rationale}\n\n"
            f"Determine which proposal is superior and provide your reasoning."
        )
        
        # Run the comparison
        result = await Runner.run(policy_comparison_agent, input=input_text)
        comparison = result.final_output_as(ComparisonResult)
        
        # Update ELO ratings
        elo_system.update_rating(comparison.winner_id, comparison.loser_id)
    
    # Create the ranked list of proposals with their ratings
    ranked_proposals = []
    for proposal in proposals:
        rating = elo_system.get_rating(proposal.id)
        ranked_proposals.append((proposal, rating))
    
    # Sort by rating in descending order
    ranked_proposals.sort(key=lambda x: x[1], reverse=True)
    
    return ranked_proposals

async def evolve_proposals(
    top_proposals: List[PolicyProposalModel],
    feedback: str,
    generation: int
) -> List[PolicyProposalModel]:
    """
    Evolve the top proposals to create improved versions.
    
    Args:
        top_proposals: List of top-rated proposals to evolve
        feedback: Feedback from previous comparisons
        generation: The current generation number
        
    Returns:
        List of evolved proposals
    """
    evolved_proposals = []
    
    for proposal in top_proposals:
        # Format the input for the evolution agent
        input_text = (
            f"Policy Proposal to Evolve (Generation {generation}):\n\n"
            f"ID: {proposal.id}\n"
            f"Title: {proposal.title}\n"
            f"Description: {proposal.description}\n"
            f"Rationale: {proposal.rationale}\n\n"
            f"General Feedback from Comparisons:\n{feedback}\n\n"
            f"Please evolve this proposal to address weaknesses and enhance strengths. "
            f"This is generation {generation + 1} of the evolutionary process."
        )
        
        # Run the evolution
        result = await Runner.run(policy_evolution_agent, input=input_text)
        evolution = result.final_output_as(EvolutionResult)
        
        # Add generation info to the evolved proposal
        evolved_proposal = evolution.evolved_proposal
        evolved_proposals.append(evolved_proposal)
    
    return evolved_proposals

async def create_final_policy_report(
    query: str,
    top_proposals: List[PolicyProposalModel],
    local_context: str
) -> FinalReportModel:
    """
    Create a comprehensive final policy report.
    
    Args:
        query: The original policy query
        top_proposals: The top-rated policy proposals
        local_context: The local context information
        
    Returns:
        A comprehensive policy report
    """
    # Format the input for the final report agent
    proposals_json = json.dumps([p.dict() for p in top_proposals], indent=2)
    
    input_text = (
        f"Policy Query: {query}\n\n"
        f"Local Context:\n{local_context}\n\n"
        f"Top Policy Proposals:\n{proposals_json}\n\n"
        f"Please create a comprehensive final policy report that synthesizes these proposals "
        f"and provides clear recommendations for implementation."
    )
    
    # Run the final report agent
    result = await Runner.run(final_report_agent, input=input_text)
    return result.final_output_as(FinalReportModel) 