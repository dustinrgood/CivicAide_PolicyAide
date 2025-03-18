#!/usr/bin/env python
"""
This is the main entry point for running the CivicAide Policy Analysis System.
This script uses absolute imports to avoid module import issues.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the integrated policy system
from src.civicaide.integrated_policy_system import run_integrated_policy_system
from src.civicaide.policy_analysis import run_policy_analysis
from src.civicaide.policy_research import run_policy_research
from src.civicaide.policy_evolution import run_policy_evolution, FinalReportModel

def print_banner():
    """Print a welcome banner"""
    print("\n" + "=" * 60)
    print("       CivicAide Policy Analysis System")
    print("=" * 60 + "\n")
    print("An AI-powered multi-agent system for local government policy analysis.")
    print("Combining policy research and analysis capabilities.\n")

def main():
    """Main entry point"""
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
    
    # Run the selected component
    if choice == '1':
        print("\nRunning the full Integrated Policy System...")
        result = asyncio.run(run_integrated_policy_system(query, output_file))
        print("\nIntegrated Policy System completed successfully!")
        
    elif choice == '2':
        print("\nRunning Policy Research only...")
        research_data = asyncio.run(run_policy_research(query))
        
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
                
            print(f"\nResearch report saved to: {output_file}")
        
        print("\nPolicy Research completed successfully!")
        
    elif choice == '3':
        print("\nRunning Policy Analysis only...")
        report = asyncio.run(run_policy_analysis(query))
        
        # Save results if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"# Policy Analysis Report: {query}\n\n")
                f.write(report)
            print(f"\nAnalysis report saved to: {output_file}")
        
        print("\nPolicy Analysis completed successfully!")
        
    elif choice == '4':
        print("\nRunning Context-Aware Policy Evolution System...")
        print("\nThis system will gather local context information and conduct web research")
        print("to create policy proposals tailored to your specific jurisdiction.")
        report = asyncio.run(run_policy_evolution(query))
        
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
            
            print(f"\nContext-aware policy evolution report saved to: {output_file}")
        
        print("\nContext-Aware Policy Evolution completed successfully!")
        
    else:
        print("\nInvalid choice. Please run again and select 1, 2, 3, or 4.")
    
    print("\nThank you for using CivicAide Policy Analysis System!")

if __name__ == "__main__":
    main() 