from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import time

# Add the parent directory to sys.path to make agents importable
# when running the script directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents import Agent, Runner, WebSearchTool, trace, gen_trace_id, custom_span

# Load environment variables
dotenv_path = Path(__file__).parent / "local.env"
load_dotenv(dotenv_path)

# Directly set the API key if not in environment
if "OPENAI_API_KEY" not in os.environ and os.path.exists(dotenv_path):
    with open(dotenv_path, 'r') as f:
        for line in f:
            if line.strip().startswith('OPENAI_API_KEY='):
                key = line.strip().split('=', 1)[1]
                os.environ["OPENAI_API_KEY"] = key
                print("API key loaded from local.env")
                break

# Model for web search planning
class PolicySearchItem(BaseModel):
    reason: str = Field(description="Reasoning for why this search is important to the policy query")
    query: str = Field(description="The search term to use for the web search")

class PolicySearchPlan(BaseModel):
    searches: list[PolicySearchItem] = Field(description="A list of web searches to perform to answer the policy query")

# Model for policy research data
class PolicyResearchData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings")
    key_data_points: list[str] = Field(description="Important facts, statistics, or precedents discovered")
    case_studies: list[str] = Field(description="Examples of similar policies in other jurisdictions")
    
    class Config:
        # Simple configuration to ensure correct schema generation
        schema_extra = {
            "required": ["short_summary", "key_data_points", "case_studies"]
        }

# Agent definitions
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

policy_search_agent = Agent(
    name="Policy Search Agent",
    instructions=(
        "You are a policy researcher. Given a search term, you search the web for information relevant to "
        "local government policy analysis. Produce a concise summary of the results (2-3 paragraphs, less than 300 words). "
        "Focus on extracting policy implications, precedents from other jurisdictions, key statistics, and stakeholder perspectives. "
        "Be objective and factual."
    ),
    tools=[WebSearchTool()],
)

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

class PolicyResearchManager:
    def __init__(self):
        self.trace_id = None
        
    async def run(self, query: str) -> PolicyResearchData:
        """Run a comprehensive policy research process"""
        self.trace_id = gen_trace_id()
        
        with trace("Policy Research Process", trace_id=self.trace_id):
            print(f"Starting policy research on: {query}")
            print(f"Trace ID: {self.trace_id}")
            
            # Step 1: Plan web searches
            print("Planning research searches...")
            search_plan = await self._plan_searches(query)
            print(f"Will perform {len(search_plan.searches)} searches")
            
            # Step 2: Execute web searches
            print("Researching policy information...")
            search_results = await self._perform_searches(search_plan)
            print(f"Completed {len(search_results)} successful searches")
            
            # Step 3: Synthesize research
            print("Synthesizing research results...")
            research_data = await self._synthesize_research(query, search_results)
            print("Research synthesis complete!")
            
            print("\nResearch Summary:\n")
            print(research_data.short_summary)
            
            return research_data
    
    async def _plan_searches(self, query: str) -> PolicySearchPlan:
        """Generate a plan of web searches to perform"""
        with custom_span("Planning policy research"):
            result = await Runner.run(
                policy_research_planner,
                f"Policy Query: {query}",
            )
            return result.final_output_as(PolicySearchPlan)
    
    async def _perform_searches(self, search_plan: PolicySearchPlan) -> list[str]:
        """Execute the planned web searches in parallel"""
        with custom_span("Executing policy research"):
            num_completed = 0
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results = []
            
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                print(f"  Search progress: {num_completed}/{len(tasks)} completed")
                
            return results
    
    async def _search(self, item: PolicySearchItem) -> str | None:
        """Execute a single web search"""
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                policy_search_agent,
                input_text,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"Error during search: {e}")
            return None
    
    async def _synthesize_research(self, query: str, search_results: list[str]) -> PolicyResearchData:
        """Synthesize the search results into structured policy research data"""
        with custom_span("Synthesizing policy research"):
            input_text = f"Original policy query: {query}\n\nResearch findings:\n{json.dumps(search_results, indent=2)}"
            result = await Runner.run(
                policy_research_synthesizer,
                input_text,
            )
            return result.final_output_as(PolicyResearchData)


async def run_policy_research(query: str) -> PolicyResearchData:
    """Run a policy research process and return structured research data"""
    manager = PolicyResearchManager()
    return await manager.run(query)


if __name__ == "__main__":
    policy_query = input("Enter a policy research query: ")
    research_data = asyncio.run(run_policy_research(policy_query))
    
    print("\n=== POLICY RESEARCH RESULTS ===\n")
    print(f"Summary: {research_data.short_summary}\n")
    
    print("Key Data Points:")
    for point in research_data.key_data_points:
        print(f"- {point}")
    
    print("\nCase Studies:")
    for case in research_data.case_studies:
        print(f"- {case}") 