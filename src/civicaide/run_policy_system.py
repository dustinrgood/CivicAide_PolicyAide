#!/usr/bin/env python
"""
This is the main entry point for running the CivicAide Policy Analysis System.
This script uses absolute imports to avoid module import issues.
"""

import os
import sys
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the integrated policy system
from src.civicaide.integrated_policy_system import run_integrated_policy_system
from src.civicaide.policy_analysis import run_policy_analysis
from src.civicaide.policy_research import run_policy_research
from src.civicaide.policy_evolution import run_policy_evolution, FinalReportModel
# Import the trace processor
from src.civicaide.trace_manager import get_trace_processor

# Create trace directory if it doesn't exist
TRACES_DIR = Path(__file__).parent / "traces"
TRACES_DIR.mkdir(exist_ok=True)

def generate_trace_id():
    """Generate a unique trace ID"""
    return f"trace_{uuid.uuid4().hex[:24]}"

def save_trace_data(policy_query, policy_type, trace_id, agent_spans):
    """
    Save trace data to a JSON file, organized by policy topic
    
    Args:
        policy_query: The query or topic of the policy
        policy_type: Type of policy analysis (research, analysis, evolution, integrated)
        trace_id: Unique identifier for this trace
        agent_spans: List of dictionaries representing agent activities
    """
    # Create a sanitized filename based on the query
    safe_query = "".join(c if c.isalnum() else "_" for c in policy_query.lower())
    safe_query = safe_query[:30]  # Limit length
    
    # Format timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create trace data structure
    trace_data = {
        "trace_id": trace_id,
        "query": policy_query,
        "policy_type": policy_type,
        "timestamp": datetime.now().isoformat(),
        "spans": agent_spans
    }
    
    # Save to file
    filename = f"{policy_type}_{safe_query}_{timestamp}.json"
    file_path = TRACES_DIR / filename
    
    with open(file_path, 'w') as f:
        json.dump(trace_data, f, indent=2)
    
    print(f"Trace data saved to: {file_path}")
    return file_path

def print_banner():
    """Print a welcome banner"""
    print("\n" + "=" * 60)
    print("       CivicAide Policy Analysis System")
    print("=" * 60 + "\n")
    print("An AI-powered multi-agent system for local government policy analysis.")
    print("Combining policy research and analysis capabilities.\n")

async def run_with_tracing(policy_query, policy_type, run_function, *args, **kwargs):
    """
    Run a policy function with tracing enabled
    
    Args:
        policy_query: The query or topic being analyzed
        policy_type: Type of policy analysis (research, analysis, etc.)
        run_function: The async function to run
        args, kwargs: Arguments to pass to the run function
    
    Returns:
        tuple: (result, trace_file_path)
    """
    # Check if a trace ID is already set (e.g., from OpenAI API)
    trace_id = os.environ.get("OPENAI_TRACE_ID")
    
    # If no trace ID from OpenAI, generate our own
    if not trace_id:
        trace_id = generate_trace_id()
        print(f"Generating local trace ID: {trace_id}")
    else:
        print(f"Using OpenAI trace ID: {trace_id}")
    
    # Enable OpenAI tracing
    os.environ["OPENAI_EXTRA_HEADERS"] = json.dumps({
        "OpenAI-Beta": "assistants=v2 tools=v2 trace=v1",
        "X-Trace-Id": trace_id
    })
    
    # Create initial span for the system startup
    agent_spans = [{
        "span_id": "span_1",
        "span_type": "system_initialization",
        "started_at": datetime.now().isoformat(),
        "ended_at": datetime.now().isoformat(),
        "details": {
            "agent_name": "System",
            "message": f"Initialized {policy_type} process for: {policy_query}"
        }
    }]
    
    # Track start time
    start_time = datetime.now()
    
    # Set trace ID in environment for any components that can use it
    if not os.environ.get("OPENAI_TRACE_ID"):
        os.environ["CIVICAIDE_TRACE_ID"] = trace_id
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Record the initialization in our trace manager
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="System",
        input_text=f"Policy Query: {policy_query}",
        output_text=f"Initialized {policy_type} process for: {policy_query}",
        span_type="system_initialization",
        metadata={
            "policy_query": policy_query,
            "policy_type": policy_type
        }
    )
    
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
        
        # If we don't have a trace ID from OpenAI yet, we'll check for one after the function runs
        check_for_openai_trace = True
    else:
        check_for_openai_trace = False
    
    # Run the function
    result = await run_function(policy_query, *args, **kwargs)
    
    # Track end time
    end_time = datetime.now()
    
    # Check if an OpenAI trace ID was generated during the function run
    if check_for_openai_trace and os.environ.get("OPENAI_TRACE_ID"):
        trace_id = os.environ.get("OPENAI_TRACE_ID")
        print(f"OpenAI trace ID found: {trace_id}")
    
    # Add completion span
    agent_spans.append({
        "span_id": f"span_{len(agent_spans) + 1}",
        "span_type": "system_completion",
        "started_at": end_time.isoformat(),
        "ended_at": end_time.isoformat(),
        "details": {
            "agent_name": "System",
            "message": f"Completed {policy_type} process in {(end_time - start_time).total_seconds()} seconds"
        }
    })
    
    # Record the completion in our trace manager
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="System",
        input_text=f"Completed {policy_type} process",
        output_text=f"Completed {policy_type} process in {(end_time - start_time).total_seconds()} seconds",
        span_type="system_completion",
        metadata={
            "policy_query": policy_query,
            "policy_type": policy_type,
            "duration_seconds": (end_time - start_time).total_seconds()
        }
    )
    
    # Create intermediate agent spans based on the policy type
    if policy_type == "research":
        # Add research-specific spans
        agent_spans.insert(1, {
            "span_id": "span_2",
            "span_type": "research",
            "started_at": (start_time).isoformat(),
            "ended_at": (end_time).isoformat(),
            "details": {
                "agent_name": "Research Agent",
                "message": "Conducted policy research"
            }
        })
    elif policy_type == "analysis":
        # Add analysis-specific spans
        agent_spans.insert(1, {
            "span_id": "span_2",
            "span_type": "analysis_planning",
            "started_at": (start_time).isoformat(),
            "ended_at": (datetime.now()).isoformat(),
            "details": {
                "agent_name": "Policy Analysis Agent",
                "message": "Analyzed policy options"
            }
        })
    elif policy_type == "evolution":
        # Add evolution-specific spans
        research_end = start_time + (end_time - start_time) * 0.3
        generation_end = research_end + (end_time - start_time) * 0.3
        evaluation_end = generation_end + (end_time - start_time) * 0.2
        
        agent_spans.insert(1, {
            "span_id": "span_2",
            "span_type": "research",
            "started_at": (start_time).isoformat(),
            "ended_at": (research_end).isoformat(),
            "details": {
                "agent_name": "Research Agent",
                "message": "Researched policy background"
            }
        })
        
        agent_spans.insert(2, {
            "span_id": "span_3",
            "span_type": "policy_generation",
            "started_at": (research_end).isoformat(),
            "ended_at": (generation_end).isoformat(),
            "details": {
                "agent_name": "Policy Generation Agent",
                "message": "Generated policy proposals"
            }
        })
        
        agent_spans.insert(3, {
            "span_id": "span_4",
            "span_type": "policy_evaluation",
            "started_at": (generation_end).isoformat(),
            "ended_at": (evaluation_end).isoformat(),
            "details": {
                "agent_name": "Policy Evaluation Agent",
                "message": "Evaluated policy proposals"
            }
        })
        
        agent_spans.insert(4, {
            "span_id": "span_5",
            "span_type": "stakeholder_analysis",
            "started_at": (evaluation_end).isoformat(),
            "ended_at": (end_time).isoformat(),
            "details": {
                "agent_name": "Stakeholder Analysis Agent",
                "message": "Analyzed stakeholder impacts"
            }
        })
    elif policy_type == "integrated":
        # Add integrated-specific spans
        research_end = start_time + (end_time - start_time) * 0.25
        planning_end = research_end + (end_time - start_time) * 0.15
        generation_end = planning_end + (end_time - start_time) * 0.25
        evaluation_end = generation_end + (end_time - start_time) * 0.15
        
        agent_spans.insert(1, {
            "span_id": "span_2",
            "span_type": "research",
            "started_at": (start_time).isoformat(),
            "ended_at": (research_end).isoformat(),
            "details": {
                "agent_name": "Research Agent",
                "message": "Researched policy context"
            }
        })
        
        agent_spans.insert(2, {
            "span_id": "span_3",
            "span_type": "planning",
            "started_at": (research_end).isoformat(),
            "ended_at": (planning_end).isoformat(),
            "details": {
                "agent_name": "Planning Agent",
                "message": "Planned policy approach"
            }
        })
        
        agent_spans.insert(3, {
            "span_id": "span_4",
            "span_type": "policy_generation",
            "started_at": (planning_end).isoformat(),
            "ended_at": (generation_end).isoformat(),
            "details": {
                "agent_name": "Policy Generation Agent",
                "message": "Generated policy proposals"
            }
        })
        
        agent_spans.insert(4, {
            "span_id": "span_5",
            "span_type": "policy_evaluation",
            "started_at": (generation_end).isoformat(),
            "ended_at": (evaluation_end).isoformat(), 
            "details": {
                "agent_name": "Policy Evaluation Agent",
                "message": "Evaluated policy proposals"
            }
        })
        
        agent_spans.insert(5, {
            "span_id": "span_6",
            "span_type": "stakeholder_analysis",
            "started_at": (evaluation_end).isoformat(),
            "ended_at": (end_time).isoformat(),
            "details": {
                "agent_name": "Stakeholder Analysis Agent",
                "message": "Analyzed stakeholder impacts"
            }
        })
    
    # Retrieve trace processor instance
    trace_processor = get_trace_processor()
    
    # Populate trace processor with current trace data
    trace_processor.current_trace_id = trace_id
    trace_processor.traces[trace_id] = agent_spans
    
    # Save trace to Supabase and file
    trace_file = trace_processor.save_trace_to_file_and_db_and_db(policy_query, policy_type)
    
    # Also save locally as backup using the old method
    local_file = save_trace_data(policy_query, policy_type, trace_id, agent_spans)
    
    # Add OpenAI logs link to trace
    openai_trace_url = f"https://platform.openai.com/logs?filter=%7B%22trace_id%22%3A%22{trace_id}%22%7D"
    print(f"\nOpenAI logs for this run: {openai_trace_url}")
    
    # Return the trace file from the trace processor if available, otherwise the local file
    return result, (trace_file or local_file)

async def main_async():
    """Async main entry point"""
    print_banner()
    
    # Ask the user what they want to run
    print("Available components:")
    print("1. Full Integrated Policy System (research + analysis)")
    print("2. Policy Research Only")
    print("3. Policy Analysis Only")
    print("4. Context-Aware Policy Evolution System (with local context and web research)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    # Get the policy query
    query = input("\nEnter your policy question or topic: ")
    
    # Ask about saving output
    save_option = input("Save report to file? (y/n): ").lower().strip()
    output_file = None
    
    if save_option.startswith('y'):
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if choice == '1':
            default_filename = f"integrated_policy_report_{timestamp}.md"
        elif choice == '2':
            default_filename = f"policy_research_{timestamp}.md"
        elif choice == '3':
            default_filename = f"policy_analysis_{timestamp}.md"
        elif choice == '4':
            default_filename = f"context_aware_policy_{timestamp}.md"
        else:
            default_filename = f"policy_report_{timestamp}.md"
            
        filename = input(f"Enter filename (default: {default_filename}): ").strip()
        output_file = filename if filename else default_filename
    
    # Run the selected component with tracing
    if choice == '1':
        print("\nRunning the full Integrated Policy System...")
        result, trace_file = await run_with_tracing(
            query, 
            "integrated", 
            run_integrated_policy_system, 
            output_file
        )
        print("\nIntegrated Policy System completed successfully!")
        print(f"Trace data saved to: {trace_file}")
        
    elif choice == '2':
        print("\nRunning Policy Research only...")
        research_data, trace_file = await run_with_tracing(query, "research", run_policy_research)
        
        # Save results if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"# Policy Research Report: {query}\n\n")
                f.write(f"## Summary\n\n{research_data.short_summary}\n\n")
                
                f.write("## Key Data Points\n\n")
                for point in research_data.key_data_points:
                    f.write(f"- {point}\n")
                f.write("\n")
                
                f.write("## Case Studies\n\n")
                for case in research_data.case_studies:
                    f.write(f"- {case}\n")
                f.write("\n")
                
                f.write("## Stakeholder Perspectives\n\n")
                for stakeholder, perspective in research_data.stakeholder_perspectives.items():
                    f.write(f"- **{stakeholder}**: {perspective}\n")
                
                # Add link to trace data
                f.write("\n\n---\n")
                f.write(f"Trace data: [View execution trace](file://{trace_file})\n")
                
            print(f"\nResearch report saved to: {output_file}")
        
        print("\nPolicy Research completed successfully!")
        print(f"Trace data saved to: {trace_file}")
        
    elif choice == '3':
        print("\nRunning Policy Analysis only...")
        report, trace_file = await run_with_tracing(query, "analysis", run_policy_analysis)
        
        # Save results if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"# Policy Analysis Report: {query}\n\n")
                f.write(report)
                
                # Add link to trace data
                f.write("\n\n---\n")
                f.write(f"Trace data: [View execution trace](file://{trace_file})\n")
                
            print(f"\nAnalysis report saved to: {output_file}")
        
        print("\nPolicy Analysis completed successfully!")
        print(f"Trace data saved to: {trace_file}")
        
    elif choice == '4':
        print("\nRunning Context-Aware Policy Evolution System...")
        print("\nThis system will gather local context information and conduct web research")
        print("to create policy proposals tailored to your specific jurisdiction.")
        
        report, trace_file = await run_with_tracing(query, "evolution", run_policy_evolution)
        
        # Save results if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"# Context-Aware Policy Evolution Report: {query}\n\n")
                f.write(f"## Executive Summary\n\n{report.summary}\n\n")
                
                f.write("## Top Policy Proposals\n\n")
                for i, proposal in enumerate(report.top_proposals):
                    f.write(f"### {i+1}. {proposal.title}\n\n")
                    f.write(f"{proposal.description}\n\n")
                    f.write(f"**Rationale**: {proposal.rationale}\n\n")
                
                # Add stakeholder analysis section
                if hasattr(report, 'stakeholder_analysis') and report.stakeholder_analysis:
                    f.write("## Stakeholder Impact Analysis\n\n")
                    for stakeholder, impacts in report.stakeholder_analysis.items():
                        f.write(f"### {stakeholder.replace('_', ' ').title()}\n\n")
                        for impact in impacts:
                            f.write(f"- {impact}\n")
                        f.write("\n")
                
                # Add equity assessment section
                if hasattr(report, 'equity_assessment') and report.equity_assessment:
                    f.write("## Equity Assessment\n\n")
                    f.write(f"{report.equity_assessment}\n\n")
                
                # Add cost-benefit analysis section
                if hasattr(report, 'cost_benefit_summary') and report.cost_benefit_summary:
                    f.write("## Cost-Benefit Analysis\n\n")
                    f.write(f"{report.cost_benefit_summary}\n\n")
                
                f.write("## Implementation Considerations\n\n")
                for consideration in report.key_considerations:
                    f.write(f"- {consideration}\n")
                f.write("\n")
                
                f.write("## Implementation Steps\n\n")
                for i, step in enumerate(report.implementation_steps):
                    f.write(f"{i+1}. {step}\n")
                
                # Add impact matrix if available
                if hasattr(report, 'impact_matrix') and report.impact_matrix:
                    f.write("\n## Policy Impact Matrix\n\n")
                    
                    # Create table header
                    headers = list(report.impact_matrix[0].keys())
                    f.write("| " + " | ".join(h.replace('_', ' ').title() for h in headers) + " |\n")
                    f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                    
                    # Create table rows
                    for row in report.impact_matrix:
                        f.write("| " + " | ".join(str(row.get(h, "N/A")) for h in headers) + " |\n")
                    f.write("\n")
                
                # Add alternative scenarios if available
                if hasattr(report, 'alternative_scenarios') and report.alternative_scenarios:
                    f.write("## Alternative Scenarios\n\n")
                    for i, scenario in enumerate(report.alternative_scenarios):
                        f.write(f"{i+1}. {scenario}\n")
                
                # Add link to trace data
                f.write("\n\n---\n")
                f.write(f"Trace data: [View execution trace](file://{trace_file})\n")
            
            print(f"\nContext-aware policy evolution report saved to: {output_file}")
        
        print("\nContext-Aware Policy Evolution completed successfully!")
        print(f"Trace data saved to: {trace_file}")
        
    else:
        print("\nInvalid choice. Please run again and select 1, 2, 3, or 4.")
    
    print("\nThank you for using CivicAide Policy Analysis System!")

def main():
    """Main entry point wrapper for async function"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 