#!/usr/bin/env python
"""
Test script to verify capturing and retrieving agent interactions with full input/output content
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the trace processor
from src.civicaide.trace_manager import get_trace_processor

def generate_trace_id():
    """Generate a unique trace ID"""
    return f"trace_{uuid.uuid4().hex[:24]}"

def main():
    """Main test function"""
    print("Testing agent interaction tracing with full content...")
    
    # Get trace processor
    trace_processor = get_trace_processor()
    
    # Generate a test trace ID
    trace_id = generate_trace_id()
    print(f"Generated test trace ID: {trace_id}")
    
    # Create a simulated policy analysis workflow with content
    
    # 1. Create root span
    root_span = {
        "span_id": "span_1",
        "trace_id": trace_id,
        "span_type": "policy_analysis",
        "started_at": datetime.now().isoformat(),
        "ended_at": datetime.now().isoformat(),
        "details": {
            "agent_name": "System",
            "message": "Started policy analysis workflow"
        }
    }
    
    # Add the root span to the trace
    trace_processor.add_span(trace_id, root_span)
    
    # 2. Record the research agent interaction
    research_prompt = """
    You are a Policy Research Agent. Analyze the following policy question:
    
    Question: How can cities reduce single-use plastic waste?
    
    Please provide research from successful implementations of such policies.
    """
    
    research_output = """
    Based on my research on reducing single-use plastic waste in cities, here are some key findings:
    
    1. Plastic Bag Bans: Over 400 municipalities have implemented plastic bag bans or fees, with San Francisco being the first major U.S. city in 2007. These policies typically reduce plastic bag use by 70-90%.
    
    2. Straw Restrictions: Cities like Seattle and Miami Beach have restricted plastic straws, requiring businesses to provide alternatives only upon request.
    
    3. Comprehensive Approaches: Cities like Berkeley, CA have created "Disposable-Free Dining" ordinances requiring food vendors to use compostable foodware and charge for disposable cups.
    
    4. Public Water Stations: Cities like London and Paris have invested in public water refill stations to reduce bottled water consumption.
    
    5. Incentive Programs: Some cities offer tax incentives to businesses that eliminate single-use plastics or implement reusable packaging systems.
    
    Case studies of successful implementations include:
    • Portland, Oregon achieved 52% reduction in plastic bag litter after their ban
    • Ireland's plastic bag tax reduced consumption by over 90%
    • Vancouver's comprehensive strategy targets straws, cups, bags, and takeout containers with a phased approach
    
    Most successful approaches combine regulations with public education campaigns and collaboration with local businesses.
    """
    
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="Research Agent",
        input_text=research_prompt,
        output_text=research_output,
        span_type="research_analysis",
        parent_span_id="span_1", 
        model="gpt-4-turbo",
        tokens_used={"input": 124, "output": 1200},
        metadata={"source": "internal knowledge"}
    )
    
    # 3. Record the policy generation agent interaction
    generation_prompt = """
    You are a Policy Generation Agent. Based on the research provided, generate a specific policy proposal for reducing single-use plastic waste:
    
    Research findings: 
    - Plastic bag bans reduce usage by 70-90%
    - Straw restrictions have been implemented in several cities
    - Comprehensive approaches covering multiple items are most effective
    - Public water stations reduce bottled water consumption
    - Incentive programs for businesses improve compliance
    
    Generate a specific policy proposal for a city of approximately 100,000 people.
    """
    
    generation_output = """
    # Comprehensive Single-Use Plastic Reduction Ordinance
    
    ## Core Components:
    
    1. **Phased Plastic Bag Ban**:
       - Phase 1 (Months 1-3): Mandatory $0.10 fee on all single-use bags
       - Phase 2 (Month 4+): Complete ban on single-use plastic bags
       - Exemptions for certain medical and food safety uses
    
    2. **Food Service Restrictions**:
       - Plastic straws, stirrers and utensils available by request only
       - 6-month transition to certified compostable alternatives
       - $0.25 fee on disposable cups (retained by businesses)
    
    3. **Public Infrastructure Investment**:
       - Install 25 water bottle refill stations in public areas
       - Provide 20 public composting bins paired with recycling stations
    
    4. **Business Incentive Program**:
       - 5% discount on business license fees for plastic-free operations
       - Recognition program with window decals for compliant businesses
       - Small business adaptation grants ($500-2000) for up to 50 businesses
    
    5. **Implementation**:
       - 3-month education period before enforcement
       - Dedicated webpage with resources and alternatives
       - Community workshops hosted monthly during transition
       - Enforcement through existing code compliance system
    
    ## Budget Requirements:
    - Water refill stations: $75,000
    - Public composting bins: $40,000
    - Business adaptation grants: $75,000
    - Education campaign: $30,000
    - Total: $220,000 initial investment
    
    ## Expected Outcomes:
    - 85% reduction in plastic bag waste within one year
    - 45% reduction in plastic straw/utensil waste
    - 30% reduction in disposable cup usage
    - Creation of 5-10 jobs in alternative products sector
    """
    
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="Policy Generation Agent",
        input_text=generation_prompt,
        output_text=generation_output,
        span_type="policy_generation",
        parent_span_id="span_1",
        model="gpt-4-turbo",
        tokens_used={"input": 198, "output": 1650},
        metadata={"temperature": 0.7}
    )
    
    # 4. Record the policy evaluation agent interaction
    evaluation_prompt = """
    You are a Policy Evaluation Agent. Evaluate the following policy proposal for reducing single-use plastic waste:
    
    Proposal:
    # Comprehensive Single-Use Plastic Reduction Ordinance
    
    ## Core Components:
    1. Phased Plastic Bag Ban with fees then complete ban
    2. Food Service Restrictions on straws, utensils with fees on cups
    3. Public Infrastructure Investment for water refill and composting
    4. Business Incentive Program including license fee discounts
    5. Implementation with education period before enforcement
    
    Budget: $220,000 initial investment
    
    Evaluate this policy for: 1) Feasibility, 2) Effectiveness, 3) Economic Impact, 4) Equity, and 5) Political Viability.
    """
    
    evaluation_output = """
    # Policy Evaluation: Comprehensive Single-Use Plastic Reduction Ordinance
    
    ## 1. Feasibility: 8/10
    - The phased approach makes implementation realistic and allows adaptation
    - Infrastructure costs ($220,000) are reasonable for a city of 100,000
    - Timeline is appropriately paced with education period
    - The enforcement through existing code compliance avoids new bureaucracy
    - Potential challenge: Ensuring adequate staffing for education campaign
    
    ## 2. Effectiveness: 9/10
    - Comprehensive approach addresses multiple plastic waste streams
    - Combines proven strategies (bans, fees, infrastructure)
    - Targets highest-volume single-use items (bags, cups, straws)
    - The phased approach with education increases likelihood of compliance
    - Expected outcomes align with documented results in similar jurisdictions
    
    ## 3. Economic Impact: 7/10
    - Short-term costs to businesses for transitioning to alternatives
    - Business adaptation grants partially offset transition costs
    - Potential for local economic development in alternative products
    - Fee retention by businesses provides compensation for increased costs
    - Consumers will face modest increased costs
    
    ## 4. Equity: 6/10
    - Bag and cup fees could disproportionately impact lower-income residents
    - No explicit provisions addressing accessibility needs for disabled persons
    - Water refill stations have positive equity impact if strategically located
    - Recommended improvement: Add fee exemptions for SNAP/WIC recipients
    - Recommended improvement: Explicitly address disability accessibility concerns
    
    ## 5. Political Viability: 7/10
    - Business incentive program helps build commercial support
    - Recognition program creates positive publicity opportunities
    - Education-first approach before enforcement reduces resistance
    - Phased implementation demonstrates responsiveness to stakeholder concerns
    - Potential opposition from specific industry groups remains likely
    
    ## Overall Assessment: 7.4/10
    This policy proposal is comprehensive, well-structured, and incorporates best practices from successful implementations. The phased approach with emphasis on education and business support increases feasibility and political viability. Recommended refinements focus on addressing equity concerns and ensuring accessibility for all residents.
    """
    
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="Policy Evaluation Agent",
        input_text=evaluation_prompt,
        output_text=evaluation_output,
        span_type="policy_evaluation",
        parent_span_id="span_1",
        model="gpt-4-turbo",
        tokens_used={"input": 220, "output": 1920},
        metadata={"evaluation_criteria": ["feasibility", "effectiveness", "economic_impact", "equity", "political_viability"]}
    )
    
    # 5. Record the stakeholder analysis agent interaction
    stakeholder_prompt = """
    You are a Stakeholder Analysis Agent. Analyze how the following stakeholders would be affected by and respond to this plastic reduction policy:
    
    1. Local retailers and restaurants
    2. Environmental advocacy groups
    3. Low-income residents
    4. Elderly and disabled populations
    5. Local government (implementation)
    
    Policy summary:
    - Phased ban on plastic bags with initial fees
    - Restrictions on straws, utensils, cups with fees
    - Water refill stations and composting bins
    - Business incentives and adaptation grants
    """
    
    stakeholder_output = """
    # Stakeholder Impact Analysis
    
    ## 1. Local Retailers and Restaurants
    
    **Impacts:**
    - Operational changes to sourcing, inventory, and staff training
    - Initial cost increases for alternative products (30-100% higher)
    - Administrative burden of collecting and reporting fees
    - Potential customer complaints during transition
    
    **Response:**
    - Small/independent businesses likely to request longer transition periods
    - Chain establishments will have concerns about city-specific regulations
    - Most will appreciate the business adaptation grants but may consider them insufficient
    - Restaurant association likely to request input on implementation timeline
    
    **Mitigation Strategies:**
    - Clear bulk purchasing guides for alternatives
    - Standardized signage and customer communication materials
    - Webinars specifically addressing frequently asked questions
    - Consider extended timelines for businesses under certain revenue thresholds
    
    ## 2. Environmental Advocacy Groups
    
    **Impacts:**
    - Advancement of environmental policy goals
    - Opportunity for community education and engagement
    - Potential platform for broader sustainability initiatives
    
    **Response:**
    - Strong support for the policy overall
    - Will likely advocate for more aggressive timeline or expanded scope
    - Will offer volunteer support for education and monitoring
    - May critique exemptions as loopholes
    
    **Engagement Strategies:**
    - Invite participation in educational workshops
    - Leverage their networks for public communication
    - Task them with specific roles in implementation
    
    ## 3. Low-Income Residents
    
    **Impacts:**
    - Disproportionate financial burden from bag and cup fees
    - Potential challenges accessing alternatives (reusable bags)
    - Benefits from improved environmental conditions in typically underserved areas
    
    **Response:**
    - Mixed, with financial concerns being primary
    - Support for environmental goals but concern about implementation
    - May feel excluded from policy development process
    
    **Mitigation Strategies:**
    - Distribute free reusable bags through community centers, food banks
    - Implement fee exemptions for SNAP/WIC recipients
    - Ensure water refill stations in all neighborhoods
    - Targeted outreach in multiple languages
    
    ## 4. Elderly and Disabled Populations
    
    **Impacts:**
    - Potential accessibility challenges with alternatives
    - Some individuals require flexible straws for medical reasons
    - Fixed-income seniors sensitive to additional costs
    
    **Response:**
    - Concern about "by request only" provisions
    - Advocacy groups may highlight ADA considerations
    - Request for explicit exemptions for medical necessities
    
    **Mitigation Strategies:**
    - Clear medical exemption provisions
    - Ensure staff training includes sensitivity to invisible disabilities
    - Consultation with disability rights organizations on implementation
    - Develop specific guidance for caregivers and care facilities
    
    ## 5. Local Government (Implementation)
    
    **Impacts:**
    - Administrative burden of education and enforcement
    - Budgetary impact of infrastructure and grants
    - Political implications of policy success/failure
    
    **Response:**
    - Departments will request clear implementation guidelines
    - Concerns about enforcement capacity with existing staff
    - Budget office will request performance metrics
    
    **Implementation Considerations:**
    - Designate specific department responsibility with adequate staffing
    - Develop clear performance metrics and reporting structure
    - Create interdepartmental working group for coordination
    - Establish regular stakeholder feedback mechanism
    """
    
    trace_processor.record_agent_interaction(
        trace_id=trace_id,
        agent_name="Stakeholder Analysis Agent",
        input_text=stakeholder_prompt,
        output_text=stakeholder_output,
        span_type="stakeholder_analysis",
        parent_span_id="span_1",
        model="gpt-4-turbo",
        tokens_used={"input": 186, "output": 2500},
        metadata={"stakeholders": ["retailers", "environmental_groups", "low_income", "elderly_disabled", "government"]}
    )
    
    # Save the complete trace
    trace_file = trace_processor.save_trace_to_file_and_db("Single-use plastic reduction policy analysis", "content_test")
    
    if trace_file:
        print(f"Test trace with full content saved to: {trace_file}")
        print("✅ Agent interaction content capture test completed successfully!")
        
        # Display the structure of what was saved
        print("\nSample of saved content structure:")
        with open(trace_file, 'r') as f:
            data = json.load(f)
            print(f"  Trace ID: {data['trace_id']}")
            print(f"  Query: {data['query']}")
            print(f"  Number of spans: {len(data['spans'])}")
            
            # Show example of first agent interaction
            agent_span = next((s for s in data['spans'] if s.get('span_type') == 'research_analysis'), None)
            if agent_span:
                print("\nExample Agent Interaction Content:")
                print(f"  Agent: {agent_span['details']['agent_name']}")
                print(f"  Span Type: {agent_span['span_type']}")
                print(f"  Model: {agent_span['content']['model']}")
                print(f"  Input length: {len(agent_span['content']['input'])} characters")
                print(f"  Output length: {len(agent_span['content']['output'])} characters")
                print(f"  Tokens used: {agent_span['content']['tokens_used']}")
    else:
        print("❌ Failed to save trace data with content.")

if __name__ == "__main__":
    main() 