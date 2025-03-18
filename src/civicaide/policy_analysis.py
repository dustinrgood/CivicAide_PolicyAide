import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from openai import AsyncOpenAI

# Add the parent directory to sys.path to make agents importable
# when running the script directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from local.env in the src/civicaide directory
dotenv_path = Path(__file__).parent / "local.env"
load_dotenv(dotenv_path)

# Directly set the API key if not in environment
# (This is not ideal for production, but helps with debugging)
if "OPENAI_API_KEY" not in os.environ and os.path.exists(dotenv_path):
    with open(dotenv_path, 'r') as f:
        for line in f:
            if line.strip().startswith('OPENAI_API_KEY='):
                key = line.strip().split('=', 1)[1]
                os.environ["OPENAI_API_KEY"] = key
                print("API key loaded from local.env")
                break

from agents import Agent, Runner

# Print debug info to verify API key is set
has_key = "OPENAI_API_KEY" in os.environ
key_length = len(os.environ.get("OPENAI_API_KEY", "")) if has_key else 0
print(f"API key found: {has_key}, Length: {key_length}")

# Agent 1: Policy Generation Agent (Generation component)
policy_generation_agent = Agent(
    name="Policy Generation Agent",
    instructions=(
        "You are an expert in local government policy. Given the policy query, generate a JSON array of "
        "policy proposals. Each proposal should be an object with 'title' and 'description' fields. Provide at least 3 proposals."
    ),
)

# Agent 2: Policy Evaluation Agent (Reflection/Ranking component)
policy_evaluation_agent = Agent(
    name="Policy Evaluation Agent",
    instructions=(
        "You evaluate a list of policy proposals formatted in JSON. For each proposal, assign a score from 1 to 10 "
        "based on its feasibility and potential impact for local government. Output a JSON array where each element "
        "includes 'title', 'description', and 'score'."
    ),
)

# Agent 2.5: Policy Judge Agent (LLM-as-a-Judge component)
policy_judge_agent = Agent(
    name="Policy Judge Agent",
    instructions=(
        "You are a policy judge. Given a list of evaluated policy proposals in JSON format, review them and select the best proposal "
        "based on feasibility and impact. Return the selected proposal as a JSON object."
    ),
)

# Agent 3: Policy Refinement Agent (Evolution component)
policy_refinement_agent = Agent(
    name="Policy Refinement Agent",
    instructions=(
        "You are tasked with improving a high-scoring policy proposal. Given the proposal in JSON with fields "
        "title, description, and score, refine the proposal by adding actionable details and recommendations. "
        "Return the refined proposal as a JSON object."
    ),
)

# Agent 4: Policy Meta-Review Agent (Meta-review component)
policy_meta_review_agent = Agent(
    name="Policy Meta-Review Agent",
    instructions=(
        "You are a senior policy analyst. Using the refined policy proposal and the original policy query, "
        "compose a final, in-depth policy analysis report. Include background, key recommendations, and potential challenges. "
        "Return the report as plain text."
    ),
)

async def run_policy_analysis(query: str) -> str:
    # STEP 1: Generate initial policy proposals.
    gen_result = await Runner.run(policy_generation_agent, input=query)
    gen_output = gen_result.final_output.strip()
    
    # Remove markdown code block markers if present
    if gen_output.startswith("```") and "```" in gen_output[3:]:
        # Extract content between markdown markers
        gen_output = gen_output.split("```", 2)[1]
        if gen_output.startswith("json"):
            gen_output = gen_output[4:].strip()  # Remove "json" and any leading whitespace
        else:
            gen_output = gen_output.strip()

    try:
        proposals = json.loads(gen_output)
    except Exception as e:
        raise ValueError(f"Failed to parse policy generation output as JSON: {e}\nOutput was: {gen_output}")

    # STEP 2: Evaluate and rank proposals.
    eval_input = json.dumps(proposals, indent=2)
    eval_result = await Runner.run(policy_evaluation_agent, input=eval_input)
    eval_output = eval_result.final_output.strip()
    
    # Remove markdown code block markers if present
    if eval_output.startswith("```") and "```" in eval_output[3:]:
        # Extract content between markdown markers
        eval_output = eval_output.split("```", 2)[1]
        if eval_output.startswith("json"):
            eval_output = eval_output[4:].strip()  # Remove "json" and any leading whitespace
        else:
            eval_output = eval_output.strip()

    try:
        evaluated_proposals = json.loads(eval_output)
    except Exception as e:
        raise ValueError(f"Failed to parse policy evaluation output as JSON: {e}\nOutput was: {eval_output}")

    # STEP 2.5: Use the Policy Judge Agent to select the best proposal.
    judge_input = json.dumps(evaluated_proposals, indent=2)
    judge_result = await Runner.run(policy_judge_agent, input=judge_input)
    judge_output = judge_result.final_output.strip()
    
    # Remove markdown code block markers if present
    if judge_output.startswith("```") and "```" in judge_output[3:]:
        # Extract content between markdown markers
        judge_output = judge_output.split("```", 2)[1]
        if judge_output.startswith("json"):
            judge_output = judge_output[4:].strip()  # Remove "json" and any leading whitespace
        else:
            judge_output = judge_output.strip()

    try:
        judged_proposal = json.loads(judge_output)
    except Exception as e:
        raise ValueError(f"Failed to parse judged proposal output as JSON: {e}\nOutput was: {judge_output}")

    # STEP 3: Refine the selected proposal from the judge.
    refinement_input = json.dumps(judged_proposal, indent=2)
    refinement_result = await Runner.run(policy_refinement_agent, input=refinement_input)
    refinement_output = refinement_result.final_output.strip()
    
    # Remove markdown code block markers if present
    if refinement_output.startswith("```") and "```" in refinement_output[3:]:
        # Extract content between markdown markers
        refinement_output = refinement_output.split("```", 2)[1]
        if refinement_output.startswith("json"):
            refinement_output = refinement_output[4:].strip()  # Remove "json" and any leading whitespace
        else:
            refinement_output = refinement_output.strip()

    try:
        refined_proposal = json.loads(refinement_output)
    except Exception as e:
        raise ValueError(f"Failed to parse refined proposal output as JSON: {e}\nOutput was: {refinement_output}")

    # STEP 4: Meta-review to create the final report.
    meta_input = (
        f"Policy Query: {query}\n\nRefined Policy Proposal:\n"
        f"Title: {refined_proposal.get('title', 'N/A')}\n"
        f"Description: {refined_proposal.get('description', 'N/A')}\n"
    )
    meta_result = await Runner.run(policy_meta_review_agent, input=meta_input)
    final_report = meta_result.final_output.strip()
    return final_report

if __name__ == "__main__":
    query = input("Enter local government policy query: ")
    report = asyncio.run(run_policy_analysis(query))
    print("\nFinal Policy Analysis Report:\n")
    print(report) 