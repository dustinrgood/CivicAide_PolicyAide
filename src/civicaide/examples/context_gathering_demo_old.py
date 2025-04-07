#!/usr/bin/env python
"""
Context Gathering Demo for CivicAide

This script demonstrates how the automated context gathering functionality can be 
used in a user profile creation workflow and for policy-specific context gathering.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
import dotenv

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Load environment variables from local.env file
env_path = Path(__file__).parent.parent / "local.env"  # src/civicaide/local.env
if env_path.exists():
    print(f"Loading environment variables from {env_path}")
    dotenv.load_dotenv(env_path)
else:
    print(f"Warning: {env_path} not found, using existing environment variables")
    # Try alternative locations
    alt_paths = [
        Path(__file__).parent.parent.parent.parent / "local.env",  # Root folder
        Path(__file__).parent.parent.parent.parent / ".env",  # .env in root
        Path("local.env"),  # local.env in current directory
    ]
    
    for alt_path in alt_paths:
        if alt_path.exists():
            print(f"Found environment file at {alt_path}")
            dotenv.load_dotenv(alt_path)
            break

# Print environment variables to debug API key configuration
print("ENVIRONMENT VARIABLES:")
census_api_key = os.environ.get('CENSUS_API_KEY')
if census_api_key:
    print(f"CENSUS_API_KEY is set: {census_api_key[:5]}...{census_api_key[-4:]}")
else:
    print("CENSUS_API_KEY is not set in environment")

# Import data models from context_agents
from src.civicaide.agents.context_agents import (
    LocationInfo,
    DemographicData,
    EconomicData,
    GovernmentStructure,
    PolicyContext,
    BaseLocalContext,
    FullPolicyContext,
    CensusAPI
)

# Try to create a Census API instance to test if it's working
print("\nTesting Census API connection:")
try:
    census_api = CensusAPI()
    if census_api.client:
        print("Census API client successfully created")
        
        # Try a test query to show actual Census API data
        print("\nTesting Census API with real data for Austin, Texas:")
        test_location = LocationInfo(
            city="Austin",
            state="Texas",
            county="Travis",
            country="USA"
        )
        census_data = census_api.get_demographics(test_location)
        if census_data.get("population", 0) > 0:
            print(f"✅ Successfully retrieved real Census data for Austin, Texas")
            print(f"   Population: {census_data.get('population', 'N/A')}")
            print(f"   Median Age: {census_data.get('median_age', 'N/A')}")
            print(f"   Median Household Income: ${census_data.get('household_income', {}).get('median', 'N/A')}")
            print("\nNote: This data comes directly from the Census API, not our mock data\n")
        else:
            print("❌ Could not retrieve real Census data, using mock data for demo")
    else:
        print("Failed to create Census API client")
except Exception as e:
    print(f"Error initializing Census API: {str(e)}")

# Define a simple version of context gathering that doesn't rely on OpenAI
async def simple_gather_base_local_context(location: LocationInfo) -> BaseLocalContext:
    """A simplified version of gather_base_local_context that uses Census API directly."""
    print(f"Gathering context data for {location.city}, {location.state}")
    
    # Get demographic data from Census API
    census_api = CensusAPI()
    census_data = None
    try:
        if census_api.client:
            print(f"Using Census API for demographic data")
            census_data = census_api.get_demographics(location)
            print(f"Census API returned data with population: {census_data.get('population', 'N/A')}")
    except Exception as e:
        print(f"Error using Census API: {e}")
        census_data = None
    
    # Create demographics object from Census data if available, otherwise use mock data
    if census_data and census_data.get("population", 0) > 0:
        demographics = DemographicData(
            population=census_data["population"],
            median_age=census_data.get("median_age"),
            population_density=census_data.get("population_density", 3820.0),
            household_income=census_data.get("household_income", {
                "median": 71543,
                "mean": 95932
            }),
            education_levels=census_data.get("education_levels", {
                "HighSchoolOrHigher": 88.6,
                "BachelorsOrHigher": 56.5,
                "GraduateOrProfessional": 21.6
            }),
            racial_composition=census_data.get("racial_composition", {
                "White": 48.3,
                "Hispanic": 33.9,
                "Black": 7.8,
                "Asian": 7.3,
                "Other": 2.7
            })
        )
        print("Using real Census API data for demographics")
    else:
        demographics = DemographicData(
            population=964254,
            median_age=33.4,
            population_density=3820.0,
            household_income={
                "median": 71543,
                "mean": 95932
            },
            education_levels={
                "HighSchoolOrHigher": 88.6,
                "BachelorsOrHigher": 56.5,
                "GraduateOrProfessional": 21.6
            },
            racial_composition={
                "White": 48.3,
                "Hispanic": 33.9,
                "Black": 7.8,
                "Asian": 7.3,
                "Other": 2.7
            }
        )
        print("Using mock demographic data")
    
    # For economics and government data, use mock data for the demo
    # In a real implementation, this would use APIs or web search
    economics = EconomicData(
        major_industries=["Technology", "Education", "Government", "Healthcare", "Entertainment"],
        unemployment_rate=census_data.get("unemployment_rate", 3.2) if census_data else 3.2,
        poverty_rate=12.5,
        major_employers=["University of Texas", "Dell Technologies", "Apple", "IBM", "Texas State Government"]
    )
    
    government = GovernmentStructure(
        government_type="Council-Manager",
        elected_officials=[
            {"title": "Mayor", "name": "Kirk Watson"},
            {"title": "City Manager", "name": "Spencer Cronk"},
            {"title": "City Council Member", "name": "Natasha Harper-Madison"}
        ],
        departments=["Public Works", "Parks and Recreation", "Police Department", "Fire Department", "Planning and Development"],
        budget_info={"total": 4500000000, "fiscal_year": "2023-2024", "major_allocation": "Public Safety"}
    )
    
    # Create and return the full context object
    return BaseLocalContext(
        location=location,
        demographics=demographics,
        economics=economics,
        government=government
    )

# Define a simplified policy context gathering function
async def simple_gather_policy_context(policy_area: str, location: LocationInfo) -> PolicyContext:
    """A simplified version of gather_policy_specific_context that uses mock data."""
    print(f"Gathering policy context for {policy_area} in {location.city}, {location.state}")
    
    # For the demo, use mock data
    # In a real implementation, this would use APIs or web search
    return PolicyContext(
        policy_area=policy_area,
        existing_regulations=[
            "City ordinance 20110804-022 (Single-Use Carryout Bag Ordinance)",
            "Texas Health and Safety Code §361.0961 (state preemption)",
            "Texas Supreme Court ruling on bag bans (June 2018)"
        ],
        stakeholders=[
            {"name": "Austin Environmental Commission", "position": "Supportive"},
            {"name": "Texas Retail Association", "position": "Opposed"},
            {"name": "Local Environmental Groups", "position": "Strongly Supportive"}
        ],
        similar_policies=[
            {"jurisdiction": "San Francisco, CA", "description": "Complete ban on plastic bags with 10¢ fee for alternatives"},
            {"jurisdiction": "Chicago, IL", "description": "7¢ tax on all bags (plastic and paper)"},
            {"jurisdiction": "Boston, MA", "description": "Ban on thin plastic bags, 5¢ fee for thicker bags and paper"}
        ],
        recent_developments=[
            "Texas Legislature considered preemption bill HB 2416 in 2023",
            "Austin's Sustainability Office released impact report of original ban (2018)",
            "Local advocacy groups launched new campaign to reinstate bag ban (2022)"
        ]
    )

async def demo_profile_creation():
    """Demonstrate the user profile creation workflow with context gathering."""
    print("\n=== CIVICAIDE PROFILE CREATION DEMO ===\n")
    
    # Step 1: Collect basic location information from the user
    # (In a real app, this would be via a form or UI)
    print("Step 1: Collecting basic location information...")
    location = LocationInfo(
        city="Austin",
        state="Texas",
        county="Travis",
        country="USA",
        zip_codes=["78701", "78702", "78703"]
    )
    print(f"Location set to: {location.city}, {location.state}, {location.country}")
    
    # Step 2: Gather comprehensive base local context automatically
    print("\nStep 2: Gathering comprehensive local context...")
    print("(This may take a few minutes as we research multiple data sources)")
    
    # Use our simplified context gathering function that doesn't rely on OpenAI
    try:
        base_context = await simple_gather_base_local_context(location)
        print("Successfully gathered base local context.")
    except Exception as e:
        print(f"Error gathering base context: {e}")
        import traceback
        print(f"Error traceback: {traceback.format_exc()}")
        raise
    
    # Step 3: Display a summary of the gathered information
    print("\nStep 3: Profile creation complete! Here's what we learned:")
    
    print(f"\nDemographics Summary:")
    print(f"- Population: {base_context.demographics.population:,}")
    if base_context.demographics.median_age:
        print(f"- Median Age: {base_context.demographics.median_age}")
    if base_context.demographics.racial_composition:
        print("- Racial Composition: ")
        for race, percentage in base_context.demographics.racial_composition.items():
            print(f"  • {race}: {percentage:.1f}%")
    
    print(f"\nEconomic Summary:")
    print("- Major Industries:")
    for industry in base_context.economics.major_industries[:5]:  # Show just top 5
        print(f"  • {industry}")
    if base_context.economics.unemployment_rate:
        print(f"- Unemployment Rate: {base_context.economics.unemployment_rate:.1f}%")
    
    print(f"\nGovernment Structure:")
    print(f"- Type: {base_context.government.government_type}")
    print("- Key Officials:")
    for official in base_context.government.elected_officials[:3]:  # Show just top 3
        if isinstance(official, dict) and 'title' in official and 'name' in official:
            print(f"  • {official['title']}: {official['name']}")
    
    # Step 4: Save the profile for future use
    print("\nStep 4: Saving profile for future policy analysis...")
    output_dir = Path(__file__).parent / "profiles"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{location.city.lower()}_{location.state.lower()}_profile.json"
    with open(output_file, 'w') as f:
        # Convert to dict for serialization
        json.dump(base_context.model_dump(), f, indent=2)
    
    print(f"Profile saved to: {output_file}")
    
    return base_context

async def demo_policy_specific_context(base_context):
    """Demonstrate gathering policy-specific context for a particular policy area."""
    print("\n=== POLICY-SPECIFIC CONTEXT GATHERING DEMO ===\n")
    
    # Choose a policy area to analyze
    policy_area = "plastic bag ban"
    print(f"Analyzing specific context for policy area: {policy_area}")
    
    # Gather policy-specific context
    print("\nGathering current policy context data...")
    
    # Use our simplified context gathering function
    try:
        policy_context = await simple_gather_policy_context(policy_area, base_context.location)
        print(f"Successfully gathered policy context for {policy_area}.")
    except Exception as e:
        print(f"Error gathering policy context: {e}")
        import traceback
        print(f"Error traceback: {traceback.format_exc()}")
        raise

    # Display the policy-specific context
    print("\nPolicy Context Summary:")
    print(f"- Policy Area: {policy_context.policy_area}")
    
    print("\n- Existing Regulations:")
    for i, reg in enumerate(policy_context.existing_regulations[:3], 1):  # Show top 3
        print(f"  {i}. {reg}")
    
    print("\n- Key Stakeholders:")
    for i, stakeholder in enumerate(policy_context.stakeholders[:3], 1):  # Show top 3
        if isinstance(stakeholder, dict) and 'name' in stakeholder and 'position' in stakeholder:
            print(f"  {i}. {stakeholder['name']}: {stakeholder['position']}")
    
    if policy_context.similar_policies:
        print("\n- Similar Policies in Other Jurisdictions:")
        for i, policy in enumerate(policy_context.similar_policies[:3], 1):  # Show top 3
            if isinstance(policy, dict) and 'jurisdiction' in policy and 'description' in policy:
                print(f"  {i}. {policy['jurisdiction']}: {policy['description']}")
    
    # Create a full policy context by combining base and policy-specific context
    full_context = FullPolicyContext(
        base_context=base_context,
        policy_context=policy_context
    )
    
    # Save the full context
    output_dir = Path(__file__).parent / "policy_contexts"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    city = base_context.location.city.lower()
    policy_file = policy_area.replace(" ", "_").lower()
    output_file = output_dir / f"{city}_{policy_file}_context.json"
    
    with open(output_file, 'w') as f:
        json.dump(full_context.model_dump(), f, indent=2)
    
    print(f"\nFull policy context saved to: {output_file}")
    print("\nThis context data can now be used for comprehensive policy analysis and evolution.")

async def main():
    """Run the complete demo."""
    try:
        # First demonstrate profile creation
        base_context = await demo_profile_creation()
        
        print("\nWould you like to continue with policy-specific context gathering? (y/n)")
        # Note: input() is blocking, which isn't ideal in async code, but fine for this demo
        response = input().strip().lower()
        
        if response in ('y', 'yes'):
            # Then demonstrate policy-specific context gathering
            await demo_policy_specific_context(base_context)
        
        print("\n=== DEMO COMPLETE ===")
        print("The gathered context can now be used to inform policy development")
        print("with a deep understanding of local conditions and policy-specific factors.")
        
    except Exception as e:
        print(f"\n[ERROR] Demo encountered an error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nDemo did not complete successfully. Please check the error messages above.")

if __name__ == "__main__":
    # Make sure the directory exists
    Path(__file__).parent.mkdir(exist_ok=True, parents=True)
    
    # Create the profiles and policy_contexts directories if they don't exist
    for dir_name in ["profiles", "policy_contexts"]:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(exist_ok=True, parents=True)
        print(f"Ensuring directory exists: {dir_path}")
    
    # Run the async main function
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() 