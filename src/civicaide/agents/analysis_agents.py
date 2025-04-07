"""
Analysis agents for CivicAide policy system.

This module contains agent definitions specialized for policy analysis.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, TypeVar

# Import base agents and utilities
from src.civicaide.agents.base_agents import (
    extract_json_from_markdown,
    parse_agent_output_as_json,
    run_with_error_handling
)

# Import the agents SDK
from agents import Agent, Runner
from pydantic import BaseModel, Field

# Models for policy analysis

class PolicyProposal(BaseModel):
    """Model for a policy proposal."""
    title: str = Field(description="Title of the policy proposal")
    description: str = Field(description="Detailed description of the policy proposal")
    score: Optional[float] = Field(description="Score assigned to the proposal (1-10)")

class PolicyProposalSet(BaseModel):
    """Model for a set of policy proposals."""
    proposals: List[PolicyProposal] = Field(description="List of policy proposals")

class RefinedPolicyProposal(BaseModel):
    """Model for a refined policy proposal."""
    title: str = Field(description="Title of the policy proposal")
    description: str = Field(description="Detailed description of the policy proposal")
    implementation_steps: List[str] = Field(description="Steps to implement the policy")
    stakeholder_impacts: Dict[str, str] = Field(description="Impacts on different stakeholders")
    challenges: List[str] = Field(description="Potential challenges and how to address them")
    
    class Config:
        schema_extra = {
            "required": ["title", "description", "implementation_steps", "stakeholder_impacts", "challenges"]
        }

# Analysis-specific agents

policy_generation_agent = Agent(
    name="Policy Generation Agent",
    instructions=(
        "You are an expert in local government policy. Given the policy query, generate a JSON array of "
        "policy proposals. Each proposal should be an object with 'title' and 'description' fields. "
        "Provide at least 3 different approaches to addressing the policy challenge."
    ),
)

policy_evaluation_agent = Agent(
    name="Policy Evaluation Agent",
    instructions=(
        "You evaluate a list of policy proposals formatted in JSON. For each proposal, assign a score from 1 to 10 "
        "based on its feasibility and potential impact for local government. Output a JSON array where each element "
        "includes 'title', 'description', and 'score'."
    ),
)

policy_judge_agent = Agent(
    name="Policy Judge Agent",
    instructions=(
        "You are a policy judge. Given a list of evaluated policy proposals in JSON format, review them and select the best proposal "
        "based on feasibility and impact. Return the selected proposal as a JSON object."
    ),
)

policy_refinement_agent = Agent(
    name="Policy Refinement Agent",
    instructions=(
        "You are tasked with improving a high-scoring policy proposal. Given the proposal in JSON with fields "
        "title, description, and score, refine the proposal by adding actionable details and recommendations. "
        "Return the refined proposal as a JSON object with the following fields: title, description, "
        "implementation_steps, stakeholder_impacts, and challenges."
    ),
)

policy_meta_review_agent = Agent(
    name="Policy Meta-Review Agent",
    instructions=(
        "You are a senior policy analyst. Using the refined policy proposal and the original policy query, "
        "compose a final, in-depth policy analysis report. Include background, key recommendations, and potential challenges. "
        "Return the report as plain text with clear section headings."
    ),
)

# Helper functions specific to policy analysis

async def generate_and_evaluate_proposals(query: str) -> List[PolicyProposal]:
    """
    Generate and evaluate policy proposals for a given query.
    
    Args:
        query: The policy query to generate proposals for
        
    Returns:
        List of evaluated proposals with scores
    """
    # Step 1: Generate initial policy proposals
    gen_result = await Runner.run(policy_generation_agent, input=query)
    gen_output = gen_result.final_output.strip()
    
    try:
        proposals = parse_agent_output_as_json(gen_output)
    except ValueError as e:
        raise ValueError(f"Failed to parse policy generation output: {e}")
    
    # Step 2: Evaluate and rank proposals
    eval_input = json.dumps(proposals, indent=2)
    eval_result = await Runner.run(policy_evaluation_agent, input=eval_input)
    eval_output = eval_result.final_output.strip()
    
    try:
        evaluated_proposals = parse_agent_output_as_json(eval_output)
        return evaluated_proposals
    except ValueError as e:
        raise ValueError(f"Failed to parse policy evaluation output: {e}")

async def select_and_refine_proposal(evaluated_proposals: List[PolicyProposal]) -> RefinedPolicyProposal:
    """
    Select the best proposal and refine it.
    
    Args:
        evaluated_proposals: List of evaluated policy proposals with scores
        
    Returns:
        A refined policy proposal with implementation details
    """
    # Step 1: Judge to select the best proposal
    judge_input = json.dumps(evaluated_proposals, indent=2)
    judge_result = await Runner.run(policy_judge_agent, input=judge_input)
    judge_output = judge_result.final_output.strip()
    
    try:
        selected_proposal = parse_agent_output_as_json(judge_output)
    except ValueError as e:
        raise ValueError(f"Failed to parse judge output: {e}")
    
    # Step 2: Refine the selected proposal
    refinement_input = json.dumps(selected_proposal, indent=2)
    refinement_result = await Runner.run(policy_refinement_agent, input=refinement_input)
    refinement_output = refinement_result.final_output.strip()
    
    try:
        refined_proposal = parse_agent_output_as_json(refinement_output)
        return refined_proposal
    except ValueError as e:
        raise ValueError(f"Failed to parse refinement output: {e}")

async def create_final_report(query: str, refined_proposal: RefinedPolicyProposal) -> str:
    """
    Create a final policy analysis report.
    
    Args:
        query: The original policy query
        refined_proposal: The refined policy proposal
        
    Returns:
        A comprehensive policy analysis report
    """
    meta_input = (
        f"Policy Query: {query}\n\nRefined Policy Proposal:\n"
        f"Title: {refined_proposal.title}\n"
        f"Description: {refined_proposal.description}\n"
        f"Implementation Steps: {json.dumps(refined_proposal.implementation_steps, indent=2)}\n"
        f"Stakeholder Impacts: {json.dumps(refined_proposal.stakeholder_impacts, indent=2)}\n"
        f"Challenges: {json.dumps(refined_proposal.challenges, indent=2)}\n"
    )
    
    meta_result = await Runner.run(policy_meta_review_agent, input=meta_input)
    return meta_result.final_output.strip() 