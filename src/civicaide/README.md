# CivicAide Policy Analyst

This module provides a comprehensive policy analysis and research workflow for local government officials and staff. It leverages multi-agent orchestration to deliver data-driven, thoroughly researched policy reports.

## Components

### 1. Policy Analysis (Multi-Agent Workflow)

The Policy Analysis component uses a sequence of specialized agents:

1. **Policy Generation Agent:**
   - Generates initial policy proposals in JSON format from a given policy query.
2. **Policy Evaluation Agent:**
   - Evaluates and scores each proposal based on feasibility and potential impact.
3. **Policy Judge Agent:**
   - Reviews evaluated proposals and selects the best one, similar to Google's AI Co-Scientist judge.
4. **Policy Refinement Agent:**
   - Refines the top-ranked proposal by adding actionable details and recommendations.
5. **Policy Meta-Review Agent:**
   - Consolidates the refined proposal and the original query into a final, comprehensive policy analysis report.

### 2. Policy Research (Web-Enabled)

The Policy Research component enables data-driven decision making:

1. **Policy Research Planner:**
   - Creates a strategic plan of web searches to gather comprehensive information.
2. **Policy Search Agent:**
   - Executes web searches in parallel to collect relevant information.
3. **Policy Research Synthesizer:**
   - Synthesizes web search results into structured research data.

### 3. Context-Aware Policy Evolution System

The Policy Evolution component uses an innovative tournament approach to evolve policy proposals:

1. **Context Gathering:**
   - Collects detailed information about your local jurisdiction, including demographics, economic context, political landscape, and key stakeholders.
2. **Smart Web Research:**
   - Conducts targeted web searches based on your specific local context.
   - Finds real-world examples, ordinances, and impact assessments from similar jurisdictions.
3. **Policy Generation:**
   - Creates multiple diverse policy proposals tailored to your local context.
4. **Policy Tournament:**
   - Uses an Elo-based ranking system to compare policies against each other.
   - Evaluates based on environmental impact, economic feasibility, equity, and stakeholder acceptance.
5. **Policy Evolution:**
   - Takes the top-performing policies and evolves them to address weaknesses.
   - Each generation improves on previous iterations.
6. **Comprehensive Reporting:**
   - Provides detailed stakeholder impact analysis across different groups.
   - Includes implementation steps customized to your jurisdiction.

### 4. Integrated Policy System

The Integrated System combines Policy Research and Analysis components:

1. First conducts thorough web research on the policy topic
2. Uses that research to inform the policy analysis process
3. Produces a comprehensive report with both research findings and policy recommendations
4. Can save outputs to markdown or JSON files for sharing

## Usage

### Policy Analysis Only

```python
import asyncio
from civicaide.policy_analysis import run_policy_analysis

query = "Analyze the impact of a ban on single-use plastic bags."
report = asyncio.run(run_policy_analysis(query))
print(report)
```

### Policy Research Only

```python
import asyncio
from civicaide.policy_research import run_policy_research

query = "What are the impacts of introducing congestion charging?"
research = asyncio.run(run_policy_research(query))
print(research.short_summary)
```

### Context-Aware Policy Evolution

```python
import asyncio
from civicaide.policy_evolution import run_policy_evolution

query = "Ban on single-use plastic bags"
report = asyncio.run(run_policy_evolution(query))
# The system will interactively ask about your local context
```

### Integrated System

```python
import asyncio
from civicaide.integrated_policy_system import run_integrated_policy_system

query = "Should our city implement rent control policies?"
results = asyncio.run(run_integrated_policy_system(
    query, 
    output_file="rent_control_policy_report.md"
))
```

## Command Line Usage

Each component can also be run directly from the command line:

```bash
python -m civicaide.run_policy_system
```

Then select which component to run (1-4) from the menu.

## Requirements

In addition to the base OpenAI Agents SDK requirements, CivicAide requires:
- Python 3.9+
- requests
- dotenv

For web research functionality, an OpenAI API key is required. For enhanced search capabilities, you can also add a SERP API key to your environment variables.

## Future Enhancements

- Integration with local demographic and economic data sources
- Visualization of policy impacts
- Policy comparison tools to contrast different approaches
- User interface for non-technical policymakers

## Testing

Unit tests are available in `tests/civicaide/test_policy_analysis.py`. 