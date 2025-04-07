"""
Base agent definitions for CivicAide policy system.

This module contains base agent definitions and utility functions that are 
shared across the different policy components (research, analysis, evolution).
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the agents SDK
from agents import Agent, Runner, WebSearchTool, trace, custom_span, gen_trace_id
from agents.result import RunResult
from pydantic import BaseModel, Field

# Common utility functions for agents

def extract_json_from_markdown(output: str) -> str:
    """
    Extract JSON content from a markdown code block.
    
    Args:
        output: Text potentially containing markdown code blocks
        
    Returns:
        Extracted content without markdown delimiters
    """
    # Remove markdown code block markers if present
    if output.startswith("```") and "```" in output[3:]:
        # Extract content between markdown markers
        output = output.split("```", 2)[1]
        if output.startswith("json"):
            output = output[4:].strip()  # Remove "json" and any leading whitespace
        else:
            output = output.strip()
    return output

def parse_agent_output_as_json(output: str) -> Any:
    """
    Parse agent output as JSON safely, with handling for markdown code blocks.
    
    Args:
        output: The output text from an agent
        
    Returns:
        Parsed JSON content
        
    Raises:
        ValueError: If the output cannot be parsed as JSON
    """
    cleaned_output = extract_json_from_markdown(output.strip())
    
    try:
        return json.loads(cleaned_output)
    except Exception as e:
        raise ValueError(f"Failed to parse output as JSON: {e}\nOutput was: {cleaned_output}")

# Base agent definitions that can be used across components

# Web Search Agent (used in both policy research and policy evolution)
web_search_agent = Agent(
    name="Web Search Agent",
    instructions=(
        "You are an objective policy researcher. Given a search term related to policy analysis, "
        "search the web for relevant information. Focus on finding factual information, statistics, "
        "precedents, case studies, and different stakeholder perspectives. Summarize the most "
        "relevant information concisely (2-3 paragraphs, under 300 words)."
    ),
    tools=[WebSearchTool()],
)

# Synthesis Agent (similar versions appear in different components)
synthesis_agent = Agent(
    name="Synthesis Agent",
    instructions=(
        "You synthesize information into a coherent, structured format. Given a collection of "
        "research findings, analysis, or evaluations, organize the information into a clear, "
        "comprehensive synthesis that highlights key themes, patterns, and insights. Be objective "
        "and balanced in your presentation of different perspectives."
    ),
    model="gpt-4o"
)

# Common Pydantic models for shared data structures

class StakeholderImpact(BaseModel):
    """Model for stakeholder impact analysis."""
    stakeholder: str
    positive_impacts: List[str]
    negative_impacts: List[str]
    
    class Config:
        schema_extra = {
            "required": ["stakeholder", "positive_impacts", "negative_impacts"]
        }

class ImplementationStep(BaseModel):
    """Model for implementation steps."""
    step_number: int
    description: str
    timeline: str
    responsible_parties: List[str]
    resources_needed: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "required": ["step_number", "description", "timeline", "responsible_parties"]
        }

# Helper functions for agent operations

async def run_with_error_handling(agent: Agent, input_text: str) -> RunResult:
    """
    Run an agent with standardized error handling.
    
    Args:
        agent: The agent to run
        input_text: The input text for the agent
        
    Returns:
        The result from the agent
        
    Raises:
        Exception: If the agent run fails after retries
    """
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            return await Runner.run(agent, input=input_text)
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                raise Exception(f"Failed to run {agent.name} after {max_retries} retries: {str(e)}")
            # Wait before retrying (exponential backoff)
            await asyncio.sleep(2 ** retry_count) 