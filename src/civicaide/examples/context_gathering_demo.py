#!/usr/bin/env python
"""
Context Gathering Demo for CivicAide

This script demonstrates how the automated context gathering functionality can be 
used in a user profile creation workflow and for policy-specific context gathering.

Requirements:
    - census: Python package for Census API access (pip install census)
    - us: Python package for US state info (pip install us)
    - aiohttp: For asynchronous HTTP requests (pip install aiohttp)
    - beautifulsoup4: For web scraping (pip install beautifulsoup4)
    - pydantic: For data validation (pip install pydantic)
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
import dotenv
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import traceback

def mask_api_key(key: str) -> str:
    """Mask an API key for display, showing only first 5 and last 4 characters."""
    if not key:
        return ""
    return f"{key[:5]}...{key[-4:]}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Load environment variables from local.env file
def load_env_variables():
    """Load environment variables from local.env file."""
    # First try the local.env in the current directory
    local_env = Path("local.env")
    if local_env.exists():
        print(f"Loading environment variables from {local_env.absolute()}")
        dotenv.load_dotenv(local_env)
        
        # Verify the keys were loaded
        census_api_key = os.environ.get('CENSUS_API_KEY')
        brave_api_key = os.environ.get('BRAVE_API_KEY')
        
        if census_api_key and brave_api_key:
            print("✅ Successfully loaded API keys from local.env")
            print(f"CENSUS_API_KEY: {mask_api_key(census_api_key)}")
            print(f"BRAVE_API_KEY: {mask_api_key(brave_api_key)}")
            return True, True
        else:
            print("❌ Failed to load one or more API keys from local.env")
            if not census_api_key:
                print("   Missing CENSUS_API_KEY")
            if not brave_api_key:
                print("   Missing BRAVE_API_KEY")
            return False, False
    else:
        print(f"❌ Could not find local.env in {local_env.absolute()}")
        print("Please ensure local.env exists in the current directory with:")
        print("CENSUS_API_KEY=your_key_here")
        print("BRAVE_API_KEY=your_key_here")
        return False, False

# Print environment variables to debug API key configuration
print("ENVIRONMENT VARIABLES:")
census_api_key = os.environ.get('CENSUS_API_KEY')
if census_api_key:
    print(f"CENSUS_API_KEY is set: {mask_api_key(census_api_key)}")
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
    CensusAPI,
    fetch_elected_officials
)

# Add the import for our MCP adapters
from src.civicaide.policyaide_adapter import CensusMCPAdapter
from src.civicaide.brave_search_adapter import BraveSearchMCPAdapter

# Add a new model for current events/news
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    """A news item related to a jurisdiction."""
    title: str = Field(description="Title of the news article")
    source: str = Field(description="Source of the news article")
    date: str = Field(description="Date of publication")
    summary: str = Field(description="Brief summary of the news article")
    url: Optional[str] = Field(description="URL to the full article", default=None)

class CurrentEvents(BaseModel):
    """Current events and news related to a jurisdiction."""
    news_items: List[NewsItem] = Field(description="Recent news items about the jurisdiction")
    trending_topics: Optional[List[str]] = Field(description="Trending topics in the jurisdiction", default=None)
    upcoming_events: Optional[List[Dict[str, str]]] = Field(description="Upcoming events in the jurisdiction", default=None)

# Extend the BaseLocalContext model to include current events
class ExtendedLocalContext(BaseLocalContext):
    """Extended base local context with current events."""
    current_events: Optional[CurrentEvents] = Field(description="Current events and news", default=None)

# Check if both MCP servers are available
def check_mcp_availability():
    """Check if both Census MCP and Brave Search MCP servers are available."""
    census_mcp_available = False
    brave_mcp_available = False
    
    # Check Census MCP
    try:
        print("Checking Census MCP availability...")
        census_adapter = CensusMCPAdapter(mcp_url="http://localhost:8050")
        if census_adapter.client:
            print("✅ Census MCP is available and will be used for demographic data.")
            census_mcp_available = True
        else:
            print("❌ Census MCP client could not be initialized.")
    except Exception as e:
        print(f"❌ Census MCP is not available: {e}")
        print("   The demo will fall back to direct Census API.")
        print("   To use Census MCP, run the server with:")
        print("   1. $env:CENSUS_API_KEY = 'your-api-key'")
        print("   2. cd src/civicaide")
        print("   3. python -m uvicorn census_mcp:app --host 0.0.0.0 --port 8050")
    
    # Check Brave Search MCP
    try:
        print("\nChecking Brave Search MCP availability...")
        brave_adapter = BraveSearchMCPAdapter(mcp_url="http://localhost:8051")
        if brave_adapter.client:
            print("✅ Brave Search MCP is available and will be used for enhanced context gathering.")
            brave_mcp_available = True
        else:
            print("❌ Brave Search MCP client could not be initialized.")
    except Exception as e:
        print(f"❌ Brave Search MCP is not available: {e}")
        print("   The demo will continue using fallback mechanisms.")
        print("   To use Brave Search MCP, run the server with:")
        print("   1. $env:BRAVE_API_KEY = 'your-api-key'")
        print("   2. $env:PORT = 8051") 
        print("   3. npx @modelcontextprotocol/server-brave-search")
    
    # Provide a summary
    if census_mcp_available and brave_mcp_available:
        print("\n✅ Both MCP servers are available and will be used for enhanced context gathering.")
    elif census_mcp_available:
        print("\n⚠️ Only Census MCP is available. Some features will use fallback mechanisms.")
    elif brave_mcp_available:
        print("\n⚠️ Only Brave Search MCP is available. Demographic data will use direct Census API.")
    else:
        print("\n❌ Neither MCP server is available. The demo will use fallback mechanisms.")
        print("   For the best experience, start both MCP servers using the start_all_mcps.ps1 script:")
        print("   cd src/civicaide")
        print("   .\\start_all_mcps.ps1")
    
    return census_mcp_available, brave_mcp_available

# Function to perform a web search for news
async def mock_news_search(location: LocationInfo) -> List[NewsItem]:
    """Search for news about a location using Brave Search MCP."""
    print(f"Searching for news about {location.city}, {location.state}...")
    
    try:
        brave_adapter = BraveSearchMCPAdapter(mcp_url="http://localhost:8051")
        if brave_adapter.client:
            print("Using Brave Search MCP to find real-time news")
            news_results = brave_adapter.get_local_news(location, count=5)
            
            if news_results:
                return [
                    NewsItem(
                        title=item.get('title', 'Untitled News'),
                        source=item.get('source', 'Unknown Source'),
                        date=item.get('date', str(datetime.now().date())),
                        summary=item.get('summary', 'No summary available'),
                        url=item.get('url', None)
                    )
                    for item in news_results
                ]
        raise Exception("Brave MCP client not available")
    except Exception as e:
        print(f"Error using Brave Search MCP for news: {e}")
        print("News search unavailable - please ensure Brave Search MCP is running")
        return []

# Define a simplified version of context gathering that doesn't rely on OpenAI
async def simple_gather_base_local_context(location: LocationInfo) -> BaseLocalContext:
    """Gather base local context using Census and Brave Search MCPs."""
    print(f"Gathering base local context for {location.city}, {location.state}...")
    
    # Initialize MCPs
    census_mcp = None
    brave_mcp = None
    
    # Try to initialize Census MCP
    try:
        census_mcp = CensusMCPAdapter(mcp_url="http://localhost:8050")
        if not census_mcp.client:
            raise Exception("Census MCP client not available")
        print("✅ Using Census MCP for demographic data")
    except Exception as e:
        print(f"❌ Census MCP initialization failed: {e}")
        raise Exception("Census MCP is required for demographic data")
    
    # Try to initialize Brave Search MCP
    try:
        brave_mcp = BraveSearchMCPAdapter(mcp_url="http://localhost:8051")
        if not brave_mcp.client:
            raise Exception("Brave Search MCP client not available")
        print("✅ Using Brave Search MCP for enhanced context")
    except Exception as e:
        print(f"❌ Brave Search MCP initialization failed: {e}")
        raise Exception("Brave Search MCP is required for context gathering")
    
    # Get demographic data from Census MCP
    try:
        census_data = census_mcp.get_demographics(location)
        if not census_data or not isinstance(census_data, dict):
            raise ValueError("Invalid data format from Census MCP")
            
        demographic_data = DemographicData(
            population=census_data.get('population', 0),
            median_age=census_data.get('median_age', 0),
            population_density=census_data.get('population_density', 0),
            household_income={
                "median": census_data.get('household_income', {}).get('median', 0),
                "mean": census_data.get('household_income', {}).get('mean', 0)
            },
            education_levels=census_data.get('education_levels', {}),
            racial_composition=census_data.get('racial_composition', {}),
            source="Census MCP"
        )
        print("✅ Retrieved demographic data from Census MCP")
    except Exception as e:
        print(f"❌ Error getting demographic data: {e}")
        raise
    
    # Get economic data from Brave Search MCP
    try:
        economic_data = await brave_mcp.get_economic_data(location)
        if not economic_data:
            raise ValueError("No economic data returned from Brave Search MCP")
            
        economics = EconomicData(
            major_industries=economic_data.get('major_industries', []),
            unemployment_rate=economic_data.get('unemployment_rate', 0),
            poverty_rate=economic_data.get('poverty_rate', 0),
            major_employers=economic_data.get('major_employers', []),
            industry_percentages=economic_data.get('industry_percentages', {})
        )
        print("✅ Retrieved economic data from Brave Search MCP")
    except Exception as e:
        print(f"❌ Error getting economic data: {e}")
        raise
    
    # Get government data from Brave Search MCP
    try:
        gov_data = await brave_mcp.get_government_data(location)
        if not gov_data:
            raise ValueError("No government data returned from Brave Search MCP")
            
        government = GovernmentStructure(
            government_type=gov_data.get('government_type', ''),
            elected_officials=gov_data.get('elected_officials', []),
            departments=gov_data.get('departments', []),
            budget_info=gov_data.get('budget_info', {})
        )
        print("✅ Retrieved government data from Brave Search MCP")
    except Exception as e:
        print(f"❌ Error getting government data: {e}")
        raise
    
    # Create and return the base local context
    base_context = BaseLocalContext(
        location=location,
        demographics=demographic_data,
        economics=economics,
        government=government
    )
    
    print(f"✅ Successfully gathered base local context for {location.city}, {location.state}")
    return base_context

# Define a simplified policy context gathering function
async def simple_gather_policy_context(policy_area: str, location: LocationInfo) -> PolicyContext:
    """Gather policy-specific context using Brave Search MCP."""
    print(f"Gathering policy context for {policy_area} in {location.city}, {location.state}")
    
    try:
        brave_mcp = BraveSearchMCPAdapter(mcp_url="http://localhost:8051")
        if not brave_mcp.client:
            raise Exception("Brave Search MCP client not available")
            
        policy_data = await brave_mcp.get_policy_data(location, policy_area)
        if not policy_data:
            raise ValueError("No policy data returned from Brave Search MCP")
            
        return PolicyContext(
            policy_area=policy_area,
            existing_regulations=policy_data.get('existing_regulations', []),
            stakeholders=policy_data.get('stakeholders', []),
            similar_policies=policy_data.get('similar_policies', []),
            recent_developments=policy_data.get('recent_developments', [])
        )
    except Exception as e:
        print(f"❌ Error gathering policy context: {e}")
        raise Exception("Brave Search MCP is required for policy context gathering")

async def demo_profile_creation():
    """Demonstrate the user profile creation workflow with context gathering."""
    print("\n=== CIVICAIDE PROFILE CREATION DEMO ===\n")
    
    # First check if Brave MCP is available
    brave_mcp_available = check_mcp_availability()
    
    # Step 1: Collect basic location information from the user
    # (In a real app, this would be via a form or UI)
    print("Step 1: Collecting basic location information...")
    location = LocationInfo(
        city="Elgin",
        state="Illinois",
        county="Kane",
        country="USA",
        zip_codes=["60120", "60123", "60124"]
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
    for industry in base_context.economics.major_industries[:5]:  # Show top 5
        print(f"  • {industry}")
    
    if base_context.economics.industry_percentages:
        print("\n- Industry Distribution:")
        for industry, percentage in base_context.economics.industry_percentages.items():
            print(f"  • {industry}: {percentage:.1f}%")
    
    if base_context.economics.unemployment_rate:
        print(f"\n- Unemployment Rate: {base_context.economics.unemployment_rate:.1f}%")
    
    print(f"\nGovernment Structure:")
    print(f"- Type: {base_context.government.government_type}")
    
    if base_context.government.budget_info:
        print("\n- Budget Information:")
        budget = base_context.government.budget_info
        print(f"  • Total Budget: ${budget['total_budget']:,}")
        print(f"  • Revenue Sources: {', '.join(budget['revenue_sources'])}")
        print(f"  • Expenditure Categories: {', '.join(budget['expenditure_categories'])}")
        
        if 'transparency_score' in budget:
            print("\n- Governance Metrics:")
            print(f"  • Transparency Score: {budget['transparency_score']:.2f}")
            print(f"  • Citizen Engagement Score: {budget['citizen_engagement_score']:.2f}")
            print(f"  • Efficiency Score: {budget['efficiency_score']:.2f}")
    
    # Display elected officials
    if base_context.government.elected_officials:
        print("\n- Elected Officials:")
        for official in base_context.government.elected_officials:
            print(f"  • {official['title']}: {official['name']} ({official.get('term', 'Current')})")

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

async def save_context_profile(base_context):
    """Save the context profile to a JSON file."""
    city = base_context.location.city.lower()
    state = base_context.location.state.lower()
    
    output_dir = Path(__file__).parent / "profiles"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{city}_{state}_profile.json"
    
    with open(output_file, 'w') as f:
        json.dump(base_context.model_dump(), f, indent=2)
    
    print(f"\nContext profile saved to: {output_file}")

async def display_context_profile(base_context):
    """Display a summary of the context profile."""
    print("\nLocal Context Profile Summary:")
    
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
    for industry in base_context.economics.major_industries[:5]:  # Show top 5
        print(f"  • {industry}")
    
    if base_context.economics.industry_percentages:
        print("\n- Industry Distribution:")
        for industry, percentage in base_context.economics.industry_percentages.items():
            print(f"  • {industry}: {percentage:.1f}%")
    
    if base_context.economics.unemployment_rate:
        print(f"\n- Unemployment Rate: {base_context.economics.unemployment_rate:.1f}%")
    
    print(f"\nGovernment Structure:")
    print(f"- Type: {base_context.government.government_type}")
    
    if base_context.government.budget_info:
        print("\n- Budget Information:")
        budget = base_context.government.budget_info
        print(f"  • Total Budget: ${budget['total_budget']:,}")
        print(f"  • Revenue Sources: {', '.join(budget['revenue_sources'])}")
        print(f"  • Expenditure Categories: {', '.join(budget['expenditure_categories'])}")
        
        if 'transparency_score' in budget:
            print("\n- Governance Metrics:")
            print(f"  • Transparency Score: {budget['transparency_score']:.2f}")
            print(f"  • Citizen Engagement Score: {budget['citizen_engagement_score']:.2f}")
            print(f"  • Efficiency Score: {budget['efficiency_score']:.2f}")
    
    # Display elected officials
    if base_context.government.elected_officials:
        print("\n- Elected Officials:")
        for official in base_context.government.elected_officials:
            print(f"  • {official['title']}: {official['name']} ({official.get('term', 'Current')})")

async def main():
    """Run the complete demo."""
    print("\n=== CONTEXT GATHERING DEMO ===\n")
    
    # Load environment variables
    census_api_key_set, brave_api_key_set = load_env_variables()
    
    # Check if both MCP servers are available
    census_mcp_available, brave_mcp_available = check_mcp_availability()
    
    # Create a demonstration location
    location = LocationInfo(
        city="Austin",
        state="Texas",
        county="Travis"
    )
    
    # Display location information
    print(f"\nDemonstrating context gathering for: {location.city}, {location.state}, {location.county} County")
    
    # Generate base local context
    print("\n=== GENERATING BASE LOCAL CONTEXT ===\n")
    try:
        # Use our simplified context gathering function
        base_context = await simple_gather_base_local_context(location)
        print(f"Successfully gathered base context for {location.city}, {location.state}.")
        
        # Print a summary of the gathered context
        await display_context_profile(base_context)
        
        # Save the context profile
        await save_context_profile(base_context)
    except Exception as e:
        print(f"Error gathering base context: {e}")
        print(f"Error traceback: {traceback.format_exc()}")
        return
        
    # Generate policy-specific context
    try:
        await demo_policy_specific_context(base_context)
    except Exception as e:
        print(f"Error in policy-specific context demo: {e}")
    
    print("\n=== CONTEXT GATHERING DEMO COMPLETE ===\n")
    print("The gathered context can now be used to inform policy development")
    print("with a deep understanding of local conditions and policy-specific factors.")
    
    # Provide instructions for using MCPs
    if not census_mcp_available or not brave_mcp_available:
        print("\n=== MCP SERVER INSTRUCTIONS ===")
        print("For the best experience, start both MCP servers using the start_all_mcps.ps1 script:")
        print("cd src/civicaide")
        print(".\\start_all_mcps.ps1")
        print("\nOr start them individually:")
        print("1. Census MCP: cd src/civicaide && python -m uvicorn census_mcp:app --host 0.0.0.0 --port 8050")
        print("2. Brave Search MCP: $env:BRAVE_API_KEY='your-api-key'; $env:PORT=8051; npx @modelcontextprotocol/server-brave-search")

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
        traceback.print_exc()