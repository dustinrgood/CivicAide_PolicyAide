"""
Research agents for CivicAide policy system.

This module contains agent definitions specialized for policy research.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import base agents and utilities
from src.civicaide.agents.base_agents import (
    web_search_agent,
    extract_json_from_markdown,
    parse_agent_output_as_json
)

# Import the agents SDK
from agents import Agent, Runner
from pydantic import BaseModel, Field

# Models for policy research

class PolicySearchItem(BaseModel):
    """Model for a policy search item."""
    reason: str = Field(description="Reasoning for why this search is important to the policy query")
    query: str = Field(description="The search term to use for the web search")

class PolicySearchPlan(BaseModel):
    """Model for a policy search plan."""
    searches: List[PolicySearchItem] = Field(description="A list of web searches to perform to answer the policy query")

class PolicyResearchData(BaseModel):
    """Model for policy research data."""
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings")
    key_data_points: List[str] = Field(description="Important facts, statistics, or precedents discovered")
    case_studies: List[str] = Field(description="Examples of similar policies in other jurisdictions")
    
    class Config:
        schema_extra = {
            "required": ["short_summary", "key_data_points", "case_studies"]
        }

# Research-specific agents

policy_research_planner = Agent(
    name="Policy Research Planner",
    instructions=(
        "You are a policy research planner. Given a local government policy query, create a plan of web "
        "searches to gather comprehensive information. Include searches for existing policies, case studies, "
        "academic research, stakeholder perspectives, and relevant statistics. Output between 5-15 search queries."
    ),
    model="gpt-4o",
    output_type=PolicySearchPlan,
)

# Note: We're using the web_search_agent from base_agents.py instead of defining it again

policy_research_synthesizer = Agent(
    name="Policy Research Synthesizer",
    instructions=(
        "You are a senior policy researcher tasked with synthesizing web search results into coherent policy research. "
        "Organize the information into the key data points and case studies found in your research. "
        "Provide a concise summary of the findings that can inform policy development. "
        "Be balanced and objective, presenting multiple perspectives where they exist."
    ),
    model="gpt-4o",
    output_type=PolicyResearchData,
)

# Additional helper functions specific to research

async def perform_policy_searches(search_plan: PolicySearchPlan) -> List[str]:
    """
    Execute the planned web searches in parallel.
    
    Args:
        search_plan: The plan of searches to perform
        
    Returns:
        List of search results as strings
    """
    import asyncio
    
    async def _search(item: PolicySearchItem) -> Optional[str]:
        """Execute a single web search."""
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                web_search_agent,
                input_text,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"Error during search: {e}")
            return None
    
    tasks = [asyncio.create_task(_search(item)) for item in search_plan.searches]
    results = []
    
    for task in asyncio.as_completed(tasks):
        result = await task
        if result is not None:
            results.append(result)
    
    return results 