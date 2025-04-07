#!/usr/bin/env python
"""
Integrated Demo for CivicAide

This script demonstrates a complete policy workflow using the new modular components.
It shows how a user would:
1. Use the component selector to choose the right policy component
2. Gather local context using the context agents
3. Visualize the process stages
4. Execute a complete policy workflow
"""

import os
import sys
import json
import asyncio
from pathlib import Path
import streamlit as st

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import our components
from src.civicaide.component_selector import (
    ComponentSelector, UserProfile, PolicyNeed,
    UserExpertise, TimeAvailable, ComponentType
)
from src.civicaide.agents import (
    LocationInfo,
    gather_base_local_context,
    create_full_policy_context
)
from src.civicaide.process_visualizer import (
    get_process_by_type,
    render_process_streamlit,
    ProcessStage,
    PolicyProcess
)

# Demo configuration
DEMO_POLICY_QUERY = "plastic bag ban"
DEMO_LOCATION = LocationInfo(
    city="Austin",
    state="Texas",
    county="Travis",
    country="USA",
    zip_codes=["78701", "78702", "78703"]
)

async def select_component_demo():
    """Demonstrate the component selector functionality."""
    print("\n=== Step 1: Component Selection ===\n")
    print("Let's help you choose the right policy component for your needs.")
    
    # Create a sample user profile
    profile = UserProfile(
        primary_needs=[
            PolicyNeed.LOCAL_CONTEXT, 
            PolicyNeed.COMPREHENSIVE_SOLUTION,
            PolicyNeed.STAKEHOLDER_ANALYSIS
        ],
        expertise_level=UserExpertise.INTERMEDIATE,
        time_available=TimeAvailable.EXTENSIVE,
        has_local_context=False,
        has_research=True
    )
    
    # Initialize component selector
    selector = ComponentSelector()
    
    # Get recommendation
    print("Based on your needs and constraints...")
    recommendation = selector.recommend_component(profile)
    
    # Display recommendation
    component_details = selector.get_component_description(recommendation.component_type)
    
    print(f"\nRecommended Component: {component_details['name']}")
    print(f"Description: {component_details['description']}")
    
    print("\nWhy this component:")
    for reason in recommendation.reasons:
        print(f"• {reason}")
    
    if recommendation.limitations:
        print("\nLimitations to consider:")
        for limitation in recommendation.limitations:
            print(f"• {limitation}")
    
    print("\nNext steps:")
    for step in recommendation.next_steps:
        print(f"• {step}")
    
    print(f"\nConfidence in recommendation: {recommendation.confidence:.0%}")
    
    return recommendation.component_type

async def gather_context_demo():
    """Demonstrate the context gathering functionality."""
    print("\n=== Step 2: Context Gathering ===\n")
    print(f"Gathering context information for {DEMO_LOCATION.city}, {DEMO_LOCATION.state}")
    
    # Simulate the context gathering process
    print("\nGathering demographic information...")
    print("Gathering economic information...")
    print("Gathering government structure information...")
    
    # In a real scenario, this would call the actual gather_base_local_context function
    # For demo purposes, we'll create a simulated result
    
    # Simulated context data
    base_context = {
        "location": {
            "city": DEMO_LOCATION.city,
            "state": DEMO_LOCATION.state,
            "country": DEMO_LOCATION.country,
        },
        "demographics": {
            "population": 964254,
            "median_age": 33.4,
            "racial_composition": {
                "White": 68.3,
                "Hispanic or Latino": 33.9,
                "Black or African American": 7.6,
                "Asian": 7.8,
                "Other": 15.4
            }
        },
        "economics": {
            "major_industries": [
                "Technology",
                "Education",
                "Government",
                "Healthcare",
                "Entertainment"
            ],
            "unemployment_rate": 3.2,
            "poverty_rate": 12.9
        },
        "government": {
            "government_type": "Council-Manager",
            "elected_officials": [
                {"title": "Mayor", "name": "Example Mayor"},
                {"title": "City Manager", "name": "Example Manager"},
                {"title": "City Council", "name": "10 members"}
            ]
        }
    }
    
    print("\nContext gathering complete!")
    print(f"Population: {base_context['demographics']['population']:,}")
    print(f"Major industries: {', '.join(base_context['economics']['major_industries'][:3])}")
    print(f"Government type: {base_context['government']['government_type']}")
    
    # Gather policy-specific context
    print("\nGathering policy-specific context for: plastic bag ban")
    print("Searching for existing regulations...")
    print("Identifying key stakeholders...")
    print("Finding similar policies in other jurisdictions...")
    
    # Simulated policy context
    policy_context = {
        "policy_area": "Environmental Regulation - Plastic Bag Ban",
        "existing_regulations": [
            "City waste management ordinance from 2015",
            "State recycling guidelines updated in 2020",
            "County plastic waste reduction initiative"
        ],
        "stakeholders": [
            {"name": "Local Retailers", "position": "Mixed, concerned about costs"},
            {"name": "Environmental Groups", "position": "Strongly supportive"},
            {"name": "Plastic Industry", "position": "Opposed, citing economic impact"},
            {"name": "Residents", "position": "Generally supportive with some concerns"}
        ],
        "similar_policies": [
            {"jurisdiction": "San Francisco, CA", "description": "Complete ban implemented in 2007"},
            {"jurisdiction": "Portland, OR", "description": "Ban with paper bag fee"},
            {"jurisdiction": "Chicago, IL", "description": "Tax-based approach instead of ban"}
        ]
    }
    
    print("\nPolicy context gathering complete!")
    print(f"Existing regulations: Found {len(policy_context['existing_regulations'])}")
    print(f"Key stakeholders: Identified {len(policy_context['stakeholders'])}")
    print(f"Similar policies: Found {len(policy_context['similar_policies'])} in other cities")
    
    return base_context, policy_context

def visualize_process_demo(process_type: str):
    """Demonstrate the process visualization."""
    print("\n=== Step 3: Process Visualization ===\n")
    print(f"Visualizing the process for: {process_type}")
    
    # Get the process definition
    process = get_process_by_type(process_type)
    
    if not process:
        print(f"Unknown process type: {process_type}")
        return
    
    # Print process information
    print(f"\nProcess: {process.name}")
    print(f"Description: {process.description}")
    print(f"Number of stages: {len(process.stages)}")
    
    # List the stages
    print("\nProcess stages:")
    for i, stage in enumerate(process.stages, 1):
        print(f"{i}. {stage.name} ({stage.estimated_time})")
        print(f"   - {stage.description}")
    
    # Calculate total time
    min_time = sum(int(stage.estimated_time.split('-')[0].split()[0]) for stage in process.stages)
    max_time = sum(int(stage.estimated_time.split('-')[-1].split()[0]) if '-' in stage.estimated_time 
                   else int(stage.estimated_time.split()[0]) for stage in process.stages)
    
    print(f"\nTotal estimated time: {min_time}-{max_time} minutes")
    
    # Simulate process execution
    print("\nSimulating process execution...")
    
    # Start with the first stage
    process.set_current_stage(process.stages[0].id)
    print(f"Starting stage: {process.get_stage_by_id(process.current_stage_id).name}")
    
    # Advance through each stage
    for _ in range(len(process.stages)):
        current_stage = process.get_stage_by_id(process.current_stage_id)
        print(f"Working on: {current_stage.name}")
        print(f"  {current_stage.description}")
        
        # Simulate stage completion
        next_stage = process.advance_to_next_stage()
        
        if next_stage:
            print(f"Completed. Moving to next stage: {next_stage.name}")
        else:
            print("Process complete!")
            break
    
    # Show progress
    progress = process.get_progress_percentage()
    print(f"\nOverall progress: {progress:.0f}%")

async def execute_policy_workflow_demo(process_type: str, base_context, policy_context):
    """Demonstrate a complete policy workflow execution."""
    print("\n=== Step 4: Complete Policy Workflow ===\n")
    print(f"Executing {process_type} workflow for: {DEMO_POLICY_QUERY}")
    
    # Set up the context
    print(f"Using context from {DEMO_LOCATION.city}, {DEMO_LOCATION.state}")
    print(f"Policy area: {policy_context['policy_area']}")
    
    # Determine which workflow to execute
    if process_type == "research":
        await execute_research_workflow_demo()
    elif process_type == "analysis":
        await execute_analysis_workflow_demo(base_context, policy_context)
    elif process_type == "evolution":
        await execute_evolution_workflow_demo(base_context, policy_context)
    elif process_type == "integrated":
        await execute_integrated_workflow_demo(base_context, policy_context)
    else:
        print(f"No specific workflow implementation for {process_type}")

async def execute_research_workflow_demo():
    """Demonstrate the research workflow."""
    print("\nExecuting Policy Research workflow...")
    
    # Simulate the research planning step
    print("\n1. Research Planning")
    print("Identifying key questions and information sources")
    print("Generated 5 search queries for policy exploration")
    
    # Simulate web search
    print("\n2. Web Research")
    print("Searching for information on plastic bag bans worldwide")
    print("Searching for environmental impact studies")
    print("Searching for economic impact on retailers")
    print("Searching for consumer behavior studies")
    print("Searching for implementation challenges")
    
    # Simulate synthesis
    print("\n3. Research Synthesis")
    print("Organizing findings into structured data")
    print("Identifying key patterns and insights")
    
    # Simulate final output
    print("\n4. Final Summary")
    print("\nRESEARCH SUMMARY:")
    print("""
    Plastic bag bans have been implemented in over 70 jurisdictions worldwide with varying approaches.
    Environmental impact studies show significant reduction in plastic waste, with 60-80% decreases
    in plastic bag litter in waterways after implementation. Economic impacts on retailers are 
    generally minimal after an initial adjustment period, with costs ranging from $3,000-$6,000 
    for small businesses. Consumer behavior adapts within 3-6 months in most locations, with 
    reusable bag usage increasing by 65-90%.
    
    KEY DATA POINTS:
    • San Francisco's ban (2007) reduced plastic bag waste by 72%
    • Average transition period for retailers: 4.5 months
    • Implementation costs are offset by reduced bag purchases within 1-2 years
    • Most successful implementations include public education campaigns
    
    CASE STUDIES:
    • Ireland: Tax approach (€0.22 per bag) reduced usage by 90%
    • California: Statewide ban with paper bag fee (10¢) model
    • South Korea: Phased approach over 3 years with increasing restrictions
    """)

async def execute_analysis_workflow_demo(base_context, policy_context):
    """Demonstrate the analysis workflow."""
    print("\nExecuting Policy Analysis workflow...")
    
    # Simulate proposal generation
    print("\n1. Proposal Generation")
    print("Generating multiple policy approaches")
    
    proposals = [
        {
            "title": "Complete Ban with Paper Bag Fee",
            "description": "Ban all single-use plastic bags with a $0.10 fee for paper bags to encourage reusable bags."
        },
        {
            "title": "Phased Implementation with Education",
            "description": "Gradual 3-year rollout starting with large retailers, coupled with public education campaign."
        },
        {
            "title": "Tax-Based Approach",
            "description": "Implement a $0.15 tax on all single-use bags (plastic and paper) to encourage reusable bags."
        }
    ]
    
    for i, proposal in enumerate(proposals, 1):
        print(f"  {i}. {proposal['title']}: {proposal['description']}")
    
    # Simulate evaluation
    print("\n2. Proposal Evaluation")
    print("Evaluating and scoring each proposal")
    
    evaluated_proposals = [
        {"title": proposals[0]["title"], "score": 8.2, "description": proposals[0]["description"]},
        {"title": proposals[1]["title"], "score": 7.5, "description": proposals[1]["description"]},
        {"title": proposals[2]["title"], "score": 6.8, "description": proposals[2]["description"]}
    ]
    
    for proposal in evaluated_proposals:
        print(f"  {proposal['title']}: Score {proposal['score']}/10")
    
    # Simulate judge selection
    print("\n3. Proposal Selection")
    print("Selecting the best proposal based on evaluation")
    
    winner = evaluated_proposals[0]
    print(f"  Selected: {winner['title']} (Score: {winner['score']}/10)")
    
    # Simulate refinement
    print("\n4. Proposal Refinement")
    print("Refining and improving the selected proposal")
    
    refined_proposal = {
        "title": winner["title"],
        "description": winner["description"],
        "implementation_steps": [
            "1. Pass city ordinance with 6-month implementation window",
            "2. Develop retailer guidance materials and training",
            "3. Launch public awareness campaign 3 months before enforcement",
            "4. Begin enforcement with grace period for first month",
            "5. Conduct quarterly assessment of impact and compliance"
        ],
        "stakeholder_impacts": {
            "Retailers": "Initial adjustment costs offset by reduced bag expenses within 18 months",
            "Residents": "Need to adapt to bringing reusable bags, minimal financial impact",
            "Environment": "Estimated 70% reduction in plastic bag waste within first year",
            "City Government": "Implementation costs of approximately $120,000 for education and enforcement"
        }
    }
    
    print("  Refined proposal now includes implementation steps and stakeholder impact analysis")
    
    # Simulate final report
    print("\n5. Final Report")
    
    print("\nPOLICY ANALYSIS REPORT:")
    print(f"""
    RECOMMENDATION: {refined_proposal['title']}
    
    {refined_proposal['description']}
    
    IMPLEMENTATION PLAN:
    {refined_proposal['implementation_steps'][0]}
    {refined_proposal['implementation_steps'][1]}
    {refined_proposal['implementation_steps'][2]}
    {refined_proposal['implementation_steps'][3]}
    {refined_proposal['implementation_steps'][4]}
    
    STAKEHOLDER IMPACTS:
    • Retailers: {refined_proposal['stakeholder_impacts']['Retailers']}
    • Residents: {refined_proposal['stakeholder_impacts']['Residents']}
    • Environment: {refined_proposal['stakeholder_impacts']['Environment']}
    • City Government: {refined_proposal['stakeholder_impacts']['City Government']}
    
    Based on the analysis of multiple approaches and considering the specific context of {base_context['location']['city']}, 
    this policy option provides the optimal balance of environmental impact, feasibility, and stakeholder acceptance.
    """)

async def execute_evolution_workflow_demo(base_context, policy_context):
    """Demonstrate the evolution workflow."""
    print("\nExecuting Policy Evolution workflow...")
    
    # Simulate context analysis
    print("\n1. Context Analysis")
    print(f"Analyzing local context for {base_context['location']['city']}, {base_context['location']['state']}")
    print(f"Population: {base_context['demographics']['population']:,}")
    print(f"Government type: {base_context['government']['government_type']}")
    print(f"Major industries: {', '.join(base_context['economics']['major_industries'][:3])}")
    
    # Simulate background research
    print("\n2. Background Research")
    print("Researching plastic bag regulations and impacts")
    print("Found 14 relevant academic studies")
    print("Analyzed 8 case studies from similar jurisdictions")
    
    # Simulate initial proposals
    print("\n3. Initial Proposals")
    print("Generating diverse initial policy proposals")
    
    initial_proposals = [
        {"id": "prop_1", "title": "Complete Ban with Paper Bag Fee", 
         "description": "Ban all single-use plastic bags with a $0.10 fee for paper bags."},
        {"id": "prop_2", "title": "Phased Implementation Approach", 
         "description": "Three-year phased implementation starting with large retailers."},
        {"id": "prop_3", "title": "Tax-Based Approach", 
         "description": "Implement a $0.15 tax on all single-use bags."},
        {"id": "prop_4", "title": "Retailer Incentive Program", 
         "description": "Create incentives for retailers to voluntarily eliminate plastic bags."},
        {"id": "prop_5", "title": "Public-Private Partnership", 
         "description": "Partner with business community on joint transition program."},
        {"id": "prop_6", "title": "Narrow Ban on Thin Plastic", 
         "description": "Ban only thin plastic bags under 4 mils thickness."}
    ]
    
    for i, prop in enumerate(initial_proposals, 1):
        print(f"  {i}. {prop['title']}: {prop['description']}")
    
    # Simulate tournament
    print("\n4. Proposal Tournament")
    print("Evaluating proposals through head-to-head comparison")
    print("Running tournament with 15 comparisons...")
    
    tournament_winners = [initial_proposals[0], initial_proposals[1], initial_proposals[4]]
    print("Top 3 proposals after tournament:")
    for i, prop in enumerate(tournament_winners, 1):
        print(f"  {i}. {prop['title']}")
    
    # Simulate evolution
    print("\n5. Policy Evolution")
    print("Evolving top proposals to create improved versions")
    
    evolved_proposals = [
        {
            "id": "evolved_1",
            "title": "Two-Phase Ban with Fee Structure", 
            "description": "Comprehensive plastic bag ban implemented in two phases with escalating paper bag fees.",
            "rationale": "Combines benefits of complete ban and phased implementation with economic incentives."
        },
        {
            "id": "evolved_2",
            "title": "Public-Private Transition Initiative", 
            "description": "Mandated ban with business-led implementation committee and support program.",
            "rationale": "Leverages stakeholder collaboration while ensuring regulatory certainty."
        }
    ]
    
    for i, prop in enumerate(evolved_proposals, 1):
        print(f"  {i}. {prop['title']}: {prop['description']}")
    
    # Simulate final evaluation
    print("\n6. Final Evaluation")
    print("Evaluating evolved proposals to select the best")
    
    winner = evolved_proposals[0]
    print(f"  Selected: {winner['title']}")
    
    # Simulate comprehensive report
    print("\n7. Comprehensive Report")
    
    print("\nPOLICY EVOLUTION REPORT:")
    print(f"""
    RECOMMENDED POLICY: {winner['title']}
    
    {winner['description']}
    
    SUMMARY:
    Through an evolutionary process comparing multiple policy approaches, this recommendation
    represents a synthesis of the most effective elements from several models. The two-phase 
    approach balances implementation feasibility with environmental impact, while the fee
    structure provides economic incentives aligned with behavior change goals.
    
    KEY CONSIDERATIONS:
    • Environmental Impact: Estimated 75-85% reduction in plastic bag waste
    • Economic Impact: Minimal disruption with costs distributed over transition period
    • Stakeholder Acceptance: Addresses key concerns from retail and environmental stakeholders
    • Implementation Complexity: Moderate, requires careful planning and communication
    
    IMPLEMENTATION STEPS:
    1. Ordinance Development (3 months)
    2. Stakeholder Education Program (3 months)
    3. Phase 1 Implementation - Large Retailers (6 months)
    4. Evaluation and Adjustment Period (3 months)
    5. Phase 2 Implementation - All Retailers (6 months)
    
    This policy approach is specifically designed for {base_context['location']['city']}'s unique
    characteristics, including its {base_context['demographics']['population']:,} population,
    {base_context['government']['government_type']} government structure, and the presence of
    {base_context['economics']['major_industries'][0]} and {base_context['economics']['major_industries'][1]}
    as major local industries.
    """)

async def execute_integrated_workflow_demo(base_context, policy_context):
    """Demonstrate the integrated workflow."""
    print("\nExecuting Integrated Policy System workflow...")
    
    # Simulate research planning
    print("\n1. Research Planning")
    print("Planning the policy research approach")
    print("Identified 6 key research questions")
    
    # Simulate policy research
    print("\n2. Policy Research")
    print("Conducting research on plastic bag ban approaches")
    print("Researching environmental impacts")
    print("Researching economic considerations")
    print("Researching stakeholder concerns")
    
    # Summarize research findings
    print("Research summary: Plastic bag bans reduce waste by 70-90% with minimal economic impact after adjustment.")
    
    # Simulate proposal generation
    print("\n3. Proposal Generation")
    print("Generating policy proposals based on research")
    
    proposals = [
        "Complete ban with paper bag fee",
        "Phased implementation approach",
        "Tax-based incentive system"
    ]
    
    for i, proposal in enumerate(proposals, 1):
        print(f"  {i}. {proposal}")
    
    # Simulate proposal evaluation
    print("\n4. Proposal Evaluation")
    print("Evaluating proposals using research insights")
    
    # Simulate proposal refinement
    print("\n5. Proposal Refinement")
    print("Refining the best policy proposal")
    
    refined_proposal = """Complete Ban with Paper Bag Fee
    
    A comprehensive ban on single-use plastic bags at all retail establishments,
    with a $0.10 fee on paper bags to encourage reusable alternatives. Implementation
    will occur in two phases over 9 months, with large retailers (>10,000 sq ft)
    transitioning in the first phase.
    """
    
    print(f"Refined proposal complete with implementation details")
    
    # Simulate integrated report
    print("\n6. Integrated Report")
    
    print("\nINTEGRATED POLICY REPORT:")
    print(f"""
    POLICY RECOMMENDATION:
    Complete Ban with Paper Bag Fee
    
    RESEARCH FINDINGS:
    • Environmental Impact: Studies show 70-90% reduction in plastic bag waste
    • Economic Impact: Initial transition costs offset within 1-2 years
    • Consumer Behavior: 85% compliance achieved within 6 months
    • Case Studies: 12 similar jurisdictions analyzed with positive outcomes
    
    IMPLEMENTATION STRATEGY:
    • Phase 1: Large retailers (>10,000 sq ft) - 3 month preparation, then enforcement
    • Phase 2: All retailers - 6 months after ordinance passage
    • Public Education: 3-month campaign beginning 30 days before Phase 1
    • Enforcement: Progressive approach with warnings first month, then fines
    
    STAKEHOLDER CONSIDERATIONS:
    • Retailers: Provided with implementation toolkit and training materials
    • Consumers: Educational materials and free reusable bag distribution events
    • Environmental Groups: Engaged as partners in educational campaign
    • Low-Income Residents: Exemption program for SNAP/WIC recipients
    
    This integrated analysis connects the research findings directly with policy development,
    ensuring that the recommendation is based on evidence and addresses the specific context
    of {base_context['location']['city']}.
    """)

async def main():
    """Run the complete demo."""
    try:
        print("\n=== CIVICAIDE INTEGRATED DEMO ===\n")
        print("This demo shows how the modular components work together in a complete policy workflow.")
        
        # Step 1: Component selection
        component_type = await select_component_demo()
        
        # Step 2: Context gathering
        base_context, policy_context = await gather_context_demo()
        
        # Step 3: Process visualization
        # Convert component_type enum to string
        process_type = component_type.name.lower()
        visualize_process_demo(process_type)
        
        # Step 4: Policy workflow execution
        await execute_policy_workflow_demo(process_type, base_context, policy_context)
        
        print("\n=== DEMO COMPLETE ===")
        print("This demonstrates how the modular components work together to create a")
        print("comprehensive, user-friendly policy development system.")
        
    except Exception as e:
        print(f"Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 