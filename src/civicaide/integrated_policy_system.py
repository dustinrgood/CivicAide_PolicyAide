from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime

# Add the parent directory to sys.path to make civicaide importable
# when running the script directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
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

# Import our components using absolute imports instead of relative imports
try:
    # First try relative import (when imported as part of a package)
    from .policy_analysis import run_policy_analysis
    from .policy_research import run_policy_research, PolicyResearchData
except ImportError:
    # Fall back to absolute import (when run as a script)
    from src.civicaide.policy_analysis import run_policy_analysis
    from src.civicaide.policy_research import run_policy_research, PolicyResearchData

async def run_integrated_policy_system(query: str, output_file: Optional[str] = None) -> dict:
    """
    Run the complete integrated policy system that:
    1. Performs web research on the policy topic
    2. Generates multiple policy proposals based on research
    3. Evaluates, judges, and refines the best proposal
    4. Creates a comprehensive report
    
    Args:
        query: The policy query to analyze
        output_file: Optional file path to save the results (default: None)
        
    Returns:
        A dictionary containing all outputs from the system
    """
    print("\n===== CivicAide Integrated Policy System =====")
    print(f"Policy Query: {query}")
    print("="*48, "\n")
    
    # Step 1: Research phase
    print("\n----- PHASE 1: POLICY RESEARCH -----\n")
    print("Gathering real-world data, precedents, and stakeholder perspectives...")
    research_data = await run_policy_research(query)
    
    # Step 2: Analysis & proposal phase
    print("\n----- PHASE 2: POLICY ANALYSIS -----\n")
    print("Generating policy proposals based on research...")
    
    # Enrich the analysis with the research data
    enriched_query = (
        f"Policy Query: {query}\n\n"
        f"RESEARCH CONTEXT:\n"
        f"Key facts: {json.dumps(research_data.key_data_points)}\n"
        f"Case studies: {json.dumps(research_data.case_studies)}\n\n"
        f"Based on this research, analyze this policy question and provide recommendations."
    )
    
    # Run the policy analysis using the enriched query
    print("Analyzing policy options and creating detailed report...")
    analysis_report = await run_policy_analysis(enriched_query)
    
    # Compile final results
    integrated_results = {
        "policy_query": query,
        "timestamp": datetime.now().isoformat(),
        "research": {
            "summary": research_data.short_summary,
            "key_data_points": research_data.key_data_points,
            "case_studies": research_data.case_studies
        },
        "analysis_report": analysis_report
    }
    
    # Save results to file if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if output_file.endswith('.json'):
                json.dump(integrated_results, f, indent=2)
            else:
                # Text format
                f.write(f"# CivicAide Policy Report: {query}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Research Summary\n\n")
                f.write(f"{research_data.short_summary}\n\n")
                
                f.write("### Key Data Points\n\n")
                for point in research_data.key_data_points:
                    f.write(f"- {point}\n")
                f.write("\n")
                
                f.write("### Case Studies\n\n")
                for case in research_data.case_studies:
                    f.write(f"- {case}\n")
                f.write("\n")
                
                f.write("## Policy Analysis Report\n\n")
                f.write(f"{analysis_report}\n")
                
        print(f"\nReport saved to: {output_file}")
    
    # Print summary
    print("\n===== INTEGRATED POLICY SYSTEM RESULTS =====\n")
    print(f"Research summary: {research_data.short_summary}\n")
    print("Analysis Report Preview:")
    preview_length = min(500, len(analysis_report))
    print(f"{analysis_report[:preview_length]}...\n")
    print(f"Complete analysis is {len(analysis_report)} characters long.")
    
    return integrated_results


if __name__ == "__main__":
    # Interactive mode
    query = input("Enter your policy question: ")
    
    save_option = input("Save report to file? (y/n): ").lower().strip()
    output_file = None
    
    if save_option == 'y':
        default_filename = f"policy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filename = input(f"Enter filename (default: {default_filename}): ").strip()
        if not filename:
            filename = default_filename
        output_file = filename
    
    results = asyncio.run(run_integrated_policy_system(query, output_file))
    
    # Final message
    print("\nCivicAide policy analysis complete! 🎉") 