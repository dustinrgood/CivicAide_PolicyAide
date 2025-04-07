"""
Context gathering agents for CivicAide policy system.

This module contains agent definitions and utilities specialized for gathering local context
information through APIs and web searches.

Requirements:
    - census: Python package for Census API access (pip install census)
    - us: Python package for US state info (pip install us)
"""

import os
import sys
import json
import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Import base agents and utilities
from src.civicaide.agents.base_agents import (
    web_search_agent,
    extract_json_from_markdown,
    parse_agent_output_as_json
)
from src.civicaide.agents.utils import (
    execute_web_searches,
    safe_json_loads,
    with_retry
)

# Import the agents SDK
from agents import Agent, Runner, WebSearchTool
from pydantic import BaseModel, Field

# Data models for context information

class LocationInfo(BaseModel):
    """Information about a location."""
    city: str = Field(description="City name")
    state: Optional[str] = Field(description="State or province name")
    county: Optional[str] = Field(description="County name")
    country: str = Field(description="Country name", default="USA")
    zip_codes: Optional[List[str]] = Field(description="ZIP or postal codes in the jurisdiction", default=None)
    
    class Config:
        json_schema_extra = {
            "required": ["city"]
        }

class DemographicData(BaseModel):
    """Demographic information for a jurisdiction."""
    population: int = Field(description="Total population")
    median_age: Optional[float] = Field(description="Median age of residents")
    population_density: Optional[float] = Field(description="Population per square mile/km")
    household_income: Optional[Dict[str, float]] = Field(description="Income distribution metrics")
    education_levels: Optional[Dict[str, float]] = Field(description="Education attainment percentages")
    racial_composition: Optional[Dict[str, float]] = Field(description="Racial/ethnic composition percentages")
    
    class Config:
        json_schema_extra = {
            "required": ["population"]
        }

class EconomicData(BaseModel):
    """Economic information for a jurisdiction."""
    major_industries: List[str] = Field(description="Major industries in the area")
    unemployment_rate: Optional[float] = Field(description="Unemployment rate")
    poverty_rate: Optional[float] = Field(description="Poverty rate")
    major_employers: Optional[List[str]] = Field(description="Major employers")
    industry_percentages: Optional[Dict[str, float]] = Field(description="Percentage distribution of industries")
    
    class Config:
        json_schema_extra = {
            "required": ["major_industries"]
        }

class GovernmentStructure(BaseModel):
    """Information about local government structure."""
    government_type: str = Field(description="Type of local government (e.g., mayor-council, council-manager)")
    elected_officials: List[Dict[str, str]] = Field(description="Key elected positions")
    departments: Optional[List[str]] = Field(description="Major government departments")
    budget_info: Optional[Dict[str, Any]] = Field(description="Budget information")
    
    class Config:
        json_schema_extra = {
            "required": ["government_type", "elected_officials"]
        }

class PolicyContext(BaseModel):
    """Information specific to a policy domain."""
    policy_area: str = Field(description="Policy area (e.g., environment, transportation)")
    existing_regulations: List[str] = Field(description="Existing regulations in this area")
    stakeholders: List[Dict[str, str]] = Field(description="Key stakeholders and their positions")
    recent_developments: Optional[List[str]] = Field(description="Recent developments in this policy area")
    similar_policies: Optional[List[Dict[str, str]]] = Field(description="Similar policies in other jurisdictions")
    
    class Config:
        json_schema_extra = {
            "required": ["policy_area", "existing_regulations", "stakeholders"]
        }

class BaseLocalContext(BaseModel):
    """Base local context information for a jurisdiction."""
    location: LocationInfo
    demographics: DemographicData
    economics: EconomicData
    government: GovernmentStructure
    
    class Config:
        json_schema_extra = {
            "required": ["location", "demographics", "economics", "government"]
        }

class FullPolicyContext(BaseModel):
    """Complete context for policy analysis, combining base context and policy-specific context."""
    base_context: BaseLocalContext
    policy_context: PolicyContext
    
    class Config:
        json_schema_extra = {
            "required": ["base_context", "policy_context"]
        }

# Context gathering agents

census_data_agent = Agent(
    name="Census Data Agent",
    instructions=(
        "You retrieve and summarize demographic data from the U.S. Census and other sources based on "
        "location information. Focus on presenting key demographic indicators including population, "
        "age distribution, income levels, education, and racial/ethnic composition. Format your response "
        "as structured JSON matching the DemographicData schema."
    ),
    model="gpt-4o",
    output_type=DemographicData
)

economic_data_agent = Agent(
    name="Economic Data Agent",
    instructions=(
        "You retrieve and analyze economic data for a specific jurisdiction. Identify major industries, "
        "unemployment rates, poverty rates, and significant employers in the area. Use information from "
        "BLS, BEA, and local economic development resources. Return data as structured JSON matching "
        "the EconomicData schema."
    ),
    model="gpt-4o",
    output_type=EconomicData
)

government_structure_agent = Agent(
    name="Government Structure Agent",
    instructions=(
        "You research and describe the structure of a local government. Identify the type of government, "
        "key elected positions, major departments, and basic budget information. Use information from "
        "official government websites and other reliable sources. Return data as structured JSON matching "
        "the GovernmentStructure schema."
    ),
    model="gpt-4o",
    output_type=GovernmentStructure,
    tools=[WebSearchTool()]
)

policy_context_agent = Agent(
    name="Policy Context Agent",
    instructions=(
        "You research the context around a specific policy area in a particular jurisdiction. Identify "
        "existing regulations, key stakeholders and their positions, recent developments, and similar "
        "policies in other jurisdictions. Use information from news sources, government websites, and "
        "other reliable sources. Return data as structured JSON matching the PolicyContext schema."
    ),
    model="gpt-4o",
    output_type=PolicyContext,
    tools=[WebSearchTool()]
)

profile_creation_agent = Agent(
    name="Profile Creation Agent",
    instructions=(
        "You create a comprehensive profile of a local jurisdiction based on gathered data. Synthesize "
        "demographic, economic, and governmental information into a cohesive profile that can inform "
        "policy development. Generate insights about the community's unique characteristics and needs. "
        "Return the profile as structured JSON matching the BaseLocalContext schema."
    ),
    model="gpt-4o",
    output_type=BaseLocalContext
)

# API integrations for data gathering

class CensusAPI:
    """
    Integration with the U.S. Census API.
    
    This class provides methods to retrieve demographic data from the Census API.
    Uses the census Python package (https://github.com/datamade/census) as a wrapper.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Census API client.
        
        Args:
            api_key: The Census API key. If not provided, it will attempt to use an 
                    environment variable CENSUS_API_KEY.
        """
        self.api_key = api_key or os.environ.get('CENSUS_API_KEY')
        if not self.api_key:
            print("[CensusAPI] WARNING: No Census API key provided. Using limited access mode.")
            # The Census API allows some requests without an API key, but they are rate-limited
            self.api_key = None
        else:
            print(f"[CensusAPI] Initialized with API key: {self.api_key[:5]}...{self.api_key[-4:]}")
        
        try:
            from census import Census
            self.client = Census(self.api_key)
            print("[CensusAPI] Successfully created Census client")
        except ImportError:
            print("[CensusAPI] WARNING: census package not installed. Please install with pip install census")
            self.client = None
        except Exception as e:
            print(f"[CensusAPI] Error creating Census client: {str(e)}")
            self.client = None
            
        # Also try to import the us package for state FIPS codes
        try:
            import us
            self.us = us
            print("[CensusAPI] Successfully imported 'us' package")
        except ImportError:
            print("[CensusAPI] WARNING: us package not installed. Please install with pip install us")
            self.us = None
    
    def get_demographics(self, location: LocationInfo) -> Dict[str, Any]:
        """
        Get demographic data for a location.
        
        Args:
            location: Location information
            
        Returns:
            Dictionary with demographic data
        """
        print(f"[CensusAPI] Getting demographics for {location.city}, {location.state or location.country}")
        
        if not self.client:
            print("[CensusAPI] No Census client available, using fallback")
            # Fallback to web search if Census API not available
            return self._get_demographics_fallback(location)
            
        try:
            # Get state FIPS code
            state_fips = self._get_state_fips(location.state)
            print(f"[CensusAPI] State FIPS code for {location.state}: {state_fips}")
            
            if not state_fips:
                print(f"[CensusAPI] Could not find FIPS code for state: {location.state}")
                return self._get_demographics_fallback(location)
                
            # Get place (city) data if we have one
            if location.city:
                print(f"[CensusAPI] Looking up city: {location.city}")
                # Check if we can find the place through a query
                places = self.client.acs5.get(
                    ('NAME', 'B01003_001E'),  # Total population
                    {'for': 'place:*', 'in': f'state:{state_fips}'}
                )
                print(f"[CensusAPI] Found {len(places)} places in state {state_fips}")
                
                # Find the place that matches our city name
                place_data = None
                for place in places:
                    if location.city.lower() in place['NAME'].lower():
                        place_data = place
                        place_fips = place['place']
                        print(f"[CensusAPI] Found matching place: {place['NAME']} with FIPS {place_fips}")
                        break
                
                if place_data:
                    print(f"[CensusAPI] Getting detailed demographic data for {place['NAME']}")
                    # Get detailed demographic data for the place
                    demographic_data = self._get_demographic_variables(state_fips, place_fips)
                    print(f"[CensusAPI] Successfully retrieved demographics for {location.city}")
                    print(f"[CensusAPI] Population: {demographic_data.get('population', 'N/A')}")
                    print(f"[CensusAPI] Median Age: {demographic_data.get('median_age', 'N/A')}")
                    return demographic_data
                else:
                    print(f"[CensusAPI] Could not find exact match for city: {location.city}")
            
            # Fallback to county level if we have a county
            if location.county:
                print(f"[CensusAPI] Looking up county: {location.county}")
                counties = self.client.acs5.get(
                    ('NAME', 'B01003_001E'),  # Total population
                    {'for': 'county:*', 'in': f'state:{state_fips}'}
                )
                print(f"[CensusAPI] Found {len(counties)} counties in state {state_fips}")
                
                # Find the county that matches our county name
                county_data = None
                for county in counties:
                    if location.county.lower() in county['NAME'].lower():
                        county_data = county
                        county_fips = county['county']
                        print(f"[CensusAPI] Found matching county: {county['NAME']} with FIPS {county_fips}")
                        break
                        
                if county_data:
                    print(f"[CensusAPI] Getting detailed demographic data for {county['NAME']}")
                    # Get detailed demographic data for the county
                    demographic_data = self._get_demographic_variables(state_fips, county_fips, geo_type='county')
                    print(f"[CensusAPI] Successfully retrieved demographics for {location.county}")
                    print(f"[CensusAPI] Population: {demographic_data.get('population', 'N/A')}")
                    return demographic_data
                else:
                    print(f"[CensusAPI] Could not find exact match for county: {location.county}")
            
            # Fallback to state level otherwise
            print(f"[CensusAPI] Falling back to state level data for {location.state}")
            demographic_data = self._get_demographic_variables(state_fips, geo_type='state')
            print(f"[CensusAPI] Successfully retrieved demographics for state {location.state}")
            print(f"[CensusAPI] Population: {demographic_data.get('population', 'N/A')}")
            return demographic_data
            
        except Exception as e:
            print(f"[CensusAPI] Error getting Census data: {str(e)}")
            import traceback
            print(f"[CensusAPI] Traceback: {traceback.format_exc()}")
            return self._get_demographics_fallback(location)
    
    def _get_state_fips(self, state_name: Optional[str]) -> Optional[str]:
        """Get FIPS code for a state name."""
        if not state_name:
            print("[CensusAPI] No state name provided")
            return None
            
        if self.us:
            # Try to use the us package
            try:
                print(f"[CensusAPI] Looking up state FIPS using 'us' package: {state_name}")
                state = self.us.states.lookup(state_name)
                print(f"[CensusAPI] Found state: {state.name} with FIPS {state.fips}")
                return state.fips
            except Exception as e:
                print(f"[CensusAPI] Error looking up state with 'us' package: {str(e)}")
                pass
                
        # Hardcoded common states as fallback
        print(f"[CensusAPI] Using hardcoded state FIPS lookup for: {state_name}")
        state_map = {
            "alabama": "01", "alaska": "02", "arizona": "04", "arkansas": "05",
            "california": "06", "colorado": "08", "connecticut": "09", "delaware": "10",
            "district of columbia": "11", "florida": "12", "georgia": "13", "hawaii": "15",
            "idaho": "16", "illinois": "17", "indiana": "18", "iowa": "19",
            "kansas": "20", "kentucky": "21", "louisiana": "22", "maine": "23",
            "maryland": "24", "massachusetts": "25", "michigan": "26", "minnesota": "27",
            "mississippi": "28", "missouri": "29", "montana": "30", "nebraska": "31",
            "nevada": "32", "new hampshire": "33", "new jersey": "34", "new mexico": "35",
            "new york": "36", "north carolina": "37", "north dakota": "38", "ohio": "39",
            "oklahoma": "40", "oregon": "41", "pennsylvania": "42", "rhode island": "44",
            "south carolina": "45", "south dakota": "46", "tennessee": "47", "texas": "48",
            "utah": "49", "vermont": "50", "virginia": "51", "washington": "53",
            "west virginia": "54", "wisconsin": "55", "wyoming": "56"
        }
        
        fips = state_map.get(state_name.lower())
        if fips:
            print(f"[CensusAPI] Found hardcoded FIPS for {state_name}: {fips}")
        else:
            print(f"[CensusAPI] Could not find FIPS code for state: {state_name}")
        return fips
    
    def _get_demographic_variables(self, state_fips: str, geo_fips: Optional[str] = None, geo_type: str = 'place') -> Dict[str, Any]:
        """Get demographic variables for a geographic area."""
        print(f"[CensusAPI] Getting demographic variables for {geo_type} in state {state_fips}")
        
        # Define parameters based on geography type
        if geo_type == 'state':
            params = {'for': f'state:{state_fips}'}
            print(f"[CensusAPI] Using state geography: {params}")
        elif geo_type == 'county':
            params = {'for': f'county:{geo_fips}', 'in': f'state:{state_fips}'}
            print(f"[CensusAPI] Using county geography: {params}")
        else:  # place (city)
            params = {'for': f'place:{geo_fips}', 'in': f'state:{state_fips}'}
            print(f"[CensusAPI] Using place geography: {params}")
        
        # Key demographic variables
        variables = (
            'NAME',  # Geography name
            'B01003_001E',  # Total population
            'B01002_001E',  # Median age
            'B19013_001E',  # Median household income
            'B02001_002E',  # White population
            'B02001_003E',  # Black/African American population
            'B02001_004E',  # American Indian/Alaska Native population
            'B02001_005E',  # Asian population
            'B02001_006E',  # Native Hawaiian/Pacific Islander population
            'B02001_007E',  # Other race population
            'B02001_008E',  # Two or more races population
            'B03003_003E',  # Hispanic or Latino population
            'B23025_005E',  # Unemployment count
            'B23025_002E',  # Labor force count (for unemployment rate calculation)
            # Corrected Education Variables (B15003 - Population 25+)
            'B15003_001E',  # Total population 25 years and over
            'B15003_017E',  # High school graduate (includes equivalency)
            'B15003_019E',  # Some college, less than 1 year
            'B15003_020E',  # Some college, 1 or more years, no degree
            'B15003_021E',  # Associate's degree
            'B15003_022E',  # Bachelor's degree
            'B15003_023E',  # Master's degree
            'B15003_024E',  # Professional school degree
            'B15003_025E',  # Doctorate degree
        )
        
        print(f"[CensusAPI] Requesting {len(variables)} variables from Census API")
        
        # Get data from Census API
        try:
            data = self.client.acs5.get(variables, params)
            print(f"[CensusAPI] Successfully retrieved data with {len(data)} results")
        except Exception as e:
            print(f"[CensusAPI] Error retrieving Census data: {str(e)}")
            return {}
        
        if not data:
            print("[CensusAPI] No data returned from Census API")
            return {}
            
        # Process the data into the format we need
        entry = data[0]  # There should be only one result for the specific geography
        print(f"[CensusAPI] Processing data for: {entry.get('NAME', 'Unknown location')}")
        
        # Calculate rates and percentages
        total_pop = int(entry['B01003_001E']) if entry['B01003_001E'] not in (None, '') else 0
        print(f"[CensusAPI] Total population: {total_pop}")
        
        # Calculate racial composition percentages
        racial_comp = {}
        if total_pop > 0:
            print("[CensusAPI] Calculating racial composition percentages")
            white = int(entry['B02001_002E']) if entry['B02001_002E'] not in (None, '') else 0
            black = int(entry['B02001_003E']) if entry['B02001_003E'] not in (None, '') else 0
            native = int(entry['B02001_004E']) if entry['B02001_004E'] not in (None, '') else 0
            asian = int(entry['B02001_005E']) if entry['B02001_005E'] not in (None, '') else 0
            pacific = int(entry['B02001_006E']) if entry['B02001_006E'] not in (None, '') else 0
            other = int(entry['B02001_007E']) if entry['B02001_007E'] not in (None, '') else 0
            multi = int(entry['B02001_008E']) if entry['B02001_008E'] not in (None, '') else 0
            hispanic = int(entry['B03003_003E']) if entry['B03003_003E'] not in (None, '') else 0
            
            # Census counts Hispanic as an ethnicity, not a race, so we need to adjust
            # This is simplified and not perfectly accurate
            non_hispanic_white = white - (white * hispanic / total_pop)
            
            racial_comp = {
                "White": round(non_hispanic_white * 100 / total_pop, 1),
                "Hispanic": round(hispanic * 100 / total_pop, 1),
                "Black": round(black * 100 / total_pop, 1),
                "Asian": round(asian * 100 / total_pop, 1),
                "Native": round(native * 100 / total_pop, 1),
                "Pacific Islander": round(pacific * 100 / total_pop, 1),
                "Other": round(other * 100 / total_pop, 1),
                "Multiracial": round(multi * 100 / total_pop, 1)
            }
            print(f"[CensusAPI] Racial composition: {racial_comp}")
        
        # Calculate unemployment rate
        unemployment_rate = None
        labor_force = int(entry['B23025_002E']) if entry['B23025_002E'] not in (None, '') else 0
        unemployed = int(entry['B23025_005E']) if entry['B23025_005E'] not in (None, '') else 0
        if labor_force > 0:
            unemployment_rate = round(unemployed * 100 / labor_force, 1)
            print(f"[CensusAPI] Unemployment rate: {unemployment_rate}%")
        
        # Calculate education levels
        education_levels = {}
        edu_pop = int(entry['B15003_001E']) if entry['B15003_001E'] not in (None, '') else 0
        if edu_pop > 0:
            print(f"[CensusAPI] Calculating education levels from population 25+: {edu_pop}")
            hs_grad_ged = int(entry.get('B15003_017E', 0) or 0)
            some_college_lt1 = int(entry.get('B15003_019E', 0) or 0)
            some_college_1plus = int(entry.get('B15003_020E', 0) or 0)
            associates = int(entry.get('B15003_021E', 0) or 0)
            bachelors = int(entry.get('B15003_022E', 0) or 0)
            masters = int(entry.get('B15003_023E', 0) or 0)
            professional = int(entry.get('B15003_024E', 0) or 0)
            doctorate = int(entry.get('B15003_025E', 0) or 0)
            
            # Calculate cumulative counts
            hs_or_higher = hs_grad_ged + some_college_lt1 + some_college_1plus + associates + bachelors + masters + professional + doctorate
            bachelors_or_higher = bachelors + masters + professional + doctorate
            graduate_or_professional = masters + professional + doctorate
            
            education_levels = {
                "HighSchoolOrHigher": round(hs_or_higher * 100 / edu_pop, 1),
                "BachelorsOrHigher": round(bachelors_or_higher * 100 / edu_pop, 1),
                "GraduateOrProfessional": round(graduate_or_professional * 100 / edu_pop, 1)
            }
            print(f"[CensusAPI] Education levels: {education_levels}")
        
        # Median income
        median_income = int(entry['B19013_001E']) if entry['B19013_001E'] not in (None, '') else None
        print(f"[CensusAPI] Median household income: ${median_income if median_income else 'N/A'}")
        
        # Median age
        median_age = float(entry['B01002_001E']) if entry['B01002_001E'] not in (None, '') else None
        print(f"[CensusAPI] Median age: {median_age if median_age else 'N/A'}")
        
        # Format the result
        result = {
            "population": total_pop,
            "median_age": median_age,
            "racial_composition": racial_comp,
            "education_levels": education_levels,
            "unemployment_rate": unemployment_rate,
            "household_income": {
                "median": median_income
            }
        }
        
        print(f"[CensusAPI] Successfully processed demographic data")
        return result
            
    def _get_demographics_fallback(self, location: LocationInfo) -> Dict[str, Any]:
        """Fallback method to get demographic data via web search if Census API fails."""
        print(f"[CensusAPI] Using web search fallback for demographic data on {location.city}, {location.state}")
        
        location_str = f"{location.city}, {location.state or location.country}"
        
        # Define searches
        demographic_searches = [
            f"population demographics of {location_str}",
            f"median age in {location_str}",
            f"racial composition of {location_str}",
            f"education levels in {location_str}",
            f"median household income in {location_str}"
        ]
        
        try:
            # Run searches asynchronously (need async context or run_in_executor)
            # For simplicity here, let's assume we can run it synchronously or adapt later
            # This part needs adjustment based on how async is handled in the calling context
            # We might need to make this method async or use asyncio.run()
            print(f"[CensusAPI Fallback] Executing web searches...")
            
            # Placeholder: Directly call the agent (requires async context)
            # This will likely fail if called from a non-async context
            # A better approach might be to signal failure and let the caller handle the web search.
            # For now, returning empty dict to avoid breaking sync flow.
            print("[CensusAPI Fallback] Web search integration needs async handling. Returning empty data for now.")
            fallback_data = {}
            
            # TODO: Properly integrate async web search and agent call here.
            # Example (if async context available):
            # demographic_results = await execute_web_searches(demographic_searches)
            # demographic_input = "Location: " + location_str + "\n\nResearch findings:\n" + "\n\n".join(demographic_results.values())
            # demographic_result = await Runner.run(census_data_agent, demographic_input)
            # if demographic_result.final_output:
            #     data_model = demographic_result.final_output_as(DemographicData)
            #     fallback_data = data_model.model_dump() # Convert pydantic model to dict
            # else:
            #     print("[CensusAPI Fallback] Agent failed to produce output.")
            #     fallback_data = {}

        except Exception as e:
            print(f"[CensusAPI Fallback] Error during web search fallback: {str(e)}")
            fallback_data = {}

        # Return empty data structure matching expected keys but with default values
        return {
            "population": fallback_data.get("population", 0),
            "median_age": fallback_data.get("median_age"),
            "racial_composition": fallback_data.get("racial_composition", {}),
            "education_levels": fallback_data.get("education_levels", {}),
            "unemployment_rate": fallback_data.get("unemployment_rate"), # Might need separate economic search
            "household_income": fallback_data.get("household_income", {"median": None})
        }

# Helper functions for context gathering

async def gather_base_local_context(location_info: LocationInfo) -> BaseLocalContext:
    """
    Gather base local context information for a jurisdiction.
    
    Args:
        location_info: Basic location information
        
    Returns:
        Comprehensive base local context
    """
    location_str = f"{location_info.city}, {location_info.state or location_info.country}"
    
    # First try to use Census API for demographic data if possible
    census_api = CensusAPI()
    census_demo_data = None
    
    try:
        if census_api.client:
            print(f"Using Census API to gather demographic data for {location_str}")
            census_demo_data = census_api.get_demographics(location_info)
    except Exception as e:
        print(f"Error using Census API: {str(e)}")
        census_demo_data = None
    
    # If Census API worked, use that data
    if census_demo_data and census_demo_data.get("population", 0) > 0:
        demographics = DemographicData(
            population=census_demo_data["population"],
            median_age=census_demo_data.get("median_age"),
            population_density=census_demo_data.get("population_density"),
            household_income=census_demo_data.get("household_income"),
            education_levels=census_demo_data.get("education_levels"),
            racial_composition=census_demo_data.get("racial_composition")
        )
    else:
        # Fallback to web search for demographic data
        print(f"Falling back to web search for demographic data for {location_str}")
        
        # Demographic searches
        demographic_searches = [
            f"population demographics of {location_str}",
            f"median age in {location_str}",
            f"racial composition of {location_str}",
            f"education levels in {location_str}"
        ]
        
        # Execute searches
        demographic_results = await execute_web_searches(demographic_searches)
        
        # Process demographic data
        demographic_input = "Location: " + location_str + "\n\nResearch findings:\n" + "\n\n".join(demographic_results.values())
        demographic_result = await Runner.run(census_data_agent, demographic_input)
        demographics = demographic_result.final_output_as(DemographicData)
    
    # Economic data search
    economic_searches = [
        f"major industries in {location_str}",
        f"unemployment rate in {location_str}",
        f"major employers in {location_str}",
        f"poverty rate in {location_str}"
    ]
    
    # Government structure searches
    government_searches = [
        f"government structure of {location_str}",
        f"mayor and city council of {location_str}",
        f"departments in {location_str} government",
        f"budget of {location_str}"
    ]
    
    # Execute searches
    economic_results = await execute_web_searches(economic_searches)
    government_results = await execute_web_searches(government_searches)
    
    # Process economic data
    economic_input = "Location: " + location_str + "\n\nResearch findings:\n" + "\n\n".join(economic_results.values())
    economic_result = await Runner.run(economic_data_agent, economic_input)
    economics = economic_result.final_output_as(EconomicData)
    
    # Process government data
    government_input = "Location: " + location_str + "\n\nResearch findings:\n" + "\n\n".join(government_results.values())
    government_result = await Runner.run(government_structure_agent, government_input)
    government = government_result.final_output_as(GovernmentStructure)
    
    # Combine into base local context
    return BaseLocalContext(
        location=location_info,
        demographics=demographics,
        economics=economics,
        government=government
    )

async def gather_policy_specific_context(
    policy_area: str,
    location_info: LocationInfo
) -> PolicyContext:
    """
    Gather policy-specific context information.
    
    Args:
        policy_area: The policy area to research
        location_info: Basic location information
        
    Returns:
        Policy-specific context information
    """
    location_str = f"{location_info.city}, {location_info.state or location_info.country}"
    
    # Policy-specific searches
    policy_searches = [
        f"existing {policy_area} regulations in {location_str}",
        f"{policy_area} stakeholders in {location_str}",
        f"recent {policy_area} developments in {location_str}",
        f"similar {policy_area} policies in other cities"
    ]
    
    # Execute searches
    policy_results = await execute_web_searches(policy_searches)
    
    # Process policy context
    policy_input = "\n".join([
        f"Policy area: {policy_area}",
        f"Location: {location_str}",
        "Research findings:",
        "\n\n".join(policy_results.values())
    ])
    
    # Process policy context data
    policy_result = await Runner.run(policy_context_agent, policy_input)
    return policy_result.final_output_as(PolicyContext)

async def create_full_policy_context(
    base_context: BaseLocalContext,
    policy_area: str
) -> FullPolicyContext:
    """
    Create a full policy context by combining base context with policy-specific context.
    
    Args:
        base_context: Base local context information
        policy_area: Policy area to gather specific context for
        
    Returns:
        Full policy context
    """
    # Gather policy-specific context
    policy_context = await gather_policy_specific_context(
        policy_area,
        base_context.location
    )
    
    # Combine contexts
    return FullPolicyContext(
        base_context=base_context,
        policy_context=policy_context
    )

def _remove_duplicate_officials(officials: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate entries from the list of officials.
    
    Args:
        officials: List of officials with potential duplicates
        
    Returns:
        Deduplicated list of officials
    """
    # Use a set to track seen officials (title + name)
    seen = set()
    unique_officials = []
    
    for official in officials:
        # Create a unique identifier for this official
        key = (official["title"], official["name"])
        
        # Only add if we haven't seen this official before
        if key not in seen:
            seen.add(key)
            unique_officials.append(official)
    
    return unique_officials

async def fetch_elected_officials(location: LocationInfo) -> List[Dict[str, str]]:
    """
    Fetch elected officials data from official government websites.
    
    Args:
        location: LocationInfo object containing city, state information
        
    Returns:
        List of dictionaries containing information about elected officials
    """
    import aiohttp
    from bs4 import BeautifulSoup
    import re
    import logging
    
    logging.info(f"Fetching elected officials for {location.city}, {location.state}")
    
    # Initialize the list to store officials
    officials = []
    
    try:
        # Determine which URL to use based on the location
        if location.city.lower() == "austin" and location.state.lower() == "texas":
            # Austin, Texas city council URL 
            url = "https://www.austintexas.gov/department/city-council"
            mayor_url = "https://www.austintexas.gov/department/mayor"
            
            async with aiohttp.ClientSession() as session:
                # Fetch the Mayor's page first
                try:
                    async with session.get(mayor_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find the mayor's name
                            mayor_name = None
                            # Try different selectors to find the mayor's name
                            mayor_heading = soup.find(['h1', 'h2', 'h3'], string=re.compile('Mayor', re.IGNORECASE))
                            if mayor_heading:
                                mayor_info = mayor_heading.find_next(['p', 'div'])
                                if mayor_info:
                                    mayor_text = mayor_info.get_text().strip()
                                    # Match name pattern (typically "Mayor FirstName LastName")
                                    match = re.search(r'Mayor\s+([A-Za-z\s\.\-]+)', mayor_text)
                                    if match:
                                        mayor_name = match.group(1).strip()
                            
                            # Alternative: try to find on a profile section
                            if not mayor_name:
                                profile_section = soup.find('div', class_=re.compile('profile|bio|about', re.IGNORECASE))
                                if profile_section:
                                    strong_tags = profile_section.find_all('strong')
                                    for tag in strong_tags:
                                        if 'mayor' in tag.get_text().lower():
                                            mayor_name = tag.get_text().replace('Mayor', '').strip()
                                            break
                            
                            # If still not found, try a less specific approach
                            if not mayor_name:
                                # Look for the mayor's name in the title or heading
                                title_tag = soup.find('title')
                                if title_tag and 'mayor' in title_tag.get_text().lower():
                                    title_text = title_tag.get_text()
                                    match = re.search(r'Mayor\s+([A-Za-z\s\.\-]+)', title_text, re.IGNORECASE)
                                    if match:
                                        mayor_name = match.group(1).strip()
                            
                            # Add the mayor if we found them
                            if mayor_name:
                                officials.append({
                                    "title": "Mayor",
                                    "name": mayor_name,
                                    "term": "Current"
                                })
                                logging.info(f"Found Mayor: {mayor_name}")
                            else:
                                logging.warning("Could not find mayor's name on the website")
                        else:
                            logging.warning(f"Failed to fetch mayor data: Status {response.status}")
                except Exception as e:
                    logging.error(f"Error fetching mayor data: {str(e)}")
                
                # Now fetch the City Council page
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Look for council members in various potential HTML structures
                            
                            # Method 1: Look for council member links
                            council_links = soup.find_all('a', href=re.compile(r'district-\d+|council-member', re.IGNORECASE))
                            for link in council_links:
                                link_text = link.get_text().strip()
                                
                                # Parse district and name
                                district_match = re.search(r'district\s*(\d+)', link_text, re.IGNORECASE)
                                if district_match:
                                    district = district_match.group(1)
                                    
                                    # Try to find the name
                                    name_elem = link.find_next(['h2', 'h3', 'h4', 'strong', 'p'])
                                    if name_elem:
                                        name = name_elem.get_text().strip()
                                        # Clean up the name (remove titles, etc.)
                                        name = re.sub(r'council\s*member|district\s*\d+', '', name, flags=re.IGNORECASE).strip()
                                        
                                        # Validate the name - it should be a proper name with at least first and last
                                        name_parts = [part for part in name.split() if part.lower() not in ('district', 'council', 'member', 'the', 'city')]
                                        if len(name_parts) >= 2 and all(part[0].isupper() for part in name_parts if part):
                                            officials.append({
                                                "title": f"City Council Member (District {district})",
                                                "name": ' '.join(name_parts),
                                                "term": "Current"
                                            })
                                            logging.info(f"Found Council Member: {' '.join(name_parts)} (District {district})")
                            
                            # Method 2: Look for a table or list of council members
                            if not any(official['title'].startswith('City Council Member') for official in officials):
                                # Try to find a table with council members
                                council_tables = soup.find_all('table')
                                for table in council_tables:
                                    rows = table.find_all('tr')
                                    for row in rows:
                                        row_text = row.get_text()
                                        district_match = re.search(r'district\s*(\d+)', row_text, re.IGNORECASE)
                                        if district_match:
                                            district = district_match.group(1)
                                            # Try to extract name by removing district reference
                                            name = re.sub(r'district\s*\d+', '', row_text, flags=re.IGNORECASE).strip()
                                            # Validate the name
                                            name_parts = [part for part in name.split() if part.lower() not in ('district', 'council', 'member', 'the', 'city')]
                                            if len(name_parts) >= 2 and all(part[0].isupper() for part in name_parts if part):
                                                officials.append({
                                                    "title": f"City Council Member (District {district})",
                                                    "name": ' '.join(name_parts),
                                                    "term": "Current"
                                                })
                                                logging.info(f"Found Council Member: {' '.join(name_parts)} (District {district})")
                            
                            # Method 3: Look for district headings
                            if not any(official['title'].startswith('City Council Member') for official in officials):
                                district_headings = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'district\s*\d+', re.IGNORECASE))
                                for heading in district_headings:
                                    heading_text = heading.get_text()
                                    district_match = re.search(r'district\s*(\d+)', heading_text, re.IGNORECASE)
                                    if district_match:
                                        district = district_match.group(1)
                                        name_elem = heading.find_next(['p', 'div', 'span'])
                                        if name_elem:
                                            name = name_elem.get_text().strip()
                                            # Validate the name
                                            name_parts = [part for part in name.split() if part.lower() not in ('district', 'council', 'member', 'the', 'city')]
                                            if len(name_parts) >= 2 and all(part[0].isupper() for part in name_parts if part):
                                                officials.append({
                                                    "title": f"City Council Member (District {district})",
                                                    "name": ' '.join(name_parts),
                                                    "term": "Current"
                                                })
                                                logging.info(f"Found Council Member: {' '.join(name_parts)} (District {district})")
                            
                            # Add City Manager if we can find them
                            try:
                                # Fetch the City Manager page or look for City Manager info
                                cm_url = "https://www.austintexas.gov/department/city-manager"
                                async with session.get(cm_url) as cm_response:
                                    if cm_response.status == 200:
                                        cm_html = await cm_response.text()
                                        cm_soup = BeautifulSoup(cm_html, 'html.parser')
                                        
                                        # Try to find City Manager name
                                        cm_name = None
                                        cm_heading = cm_soup.find(['h1', 'h2', 'h3'], string=re.compile('City Manager', re.IGNORECASE))
                                        if cm_heading:
                                            cm_info = cm_heading.find_next(['p', 'div'])
                                            if cm_info:
                                                cm_text = cm_info.get_text().strip()
                                                # Match name pattern
                                                match = re.search(r'City Manager\s+([A-Za-z\s\.\-]+)', cm_text)
                                                if match:
                                                    cm_name = match.group(1).strip()
                                        
                                        # If found, add to officials
                                        if cm_name:
                                            officials.append({
                                                "title": "City Manager",
                                                "name": cm_name,
                                                "term": "Current"
                                            })
                                            logging.info(f"Found City Manager: {cm_name}")
                            except Exception as e:
                                logging.error(f"Error fetching City Manager data: {str(e)}")
                except Exception as e:
                    logging.error(f"Error fetching council data: {str(e)}")
        
        elif location.city.lower() == "new york" and location.state.lower() == "new york":
            # New York City officials
            url = "https://www.nyc.gov/content/html/om/html/administration.html"
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find the mayor
                            mayor_section = soup.find(['h1', 'h2', 'h3'], string=re.compile('Mayor', re.IGNORECASE))
                            if mayor_section:
                                mayor_info = mayor_section.find_next(['p', 'div', 'span'])
                                if mayor_info:
                                    mayor_name = mayor_info.get_text().strip()
                                    # Clean up name if needed
                                    mayor_name = re.sub(r'mayor|hon\.', '', mayor_name, flags=re.IGNORECASE).strip()
                                    
                                    officials.append({
                                        "title": "Mayor",
                                        "name": mayor_name,
                                        "term": "Current"
                                    })
                                    logging.info(f"Found Mayor: {mayor_name}")
                            
                            # Find other officials (comptroller, public advocate, etc.)
                            other_titles = ['Comptroller', 'Public Advocate', 'Corporation Counsel']
                            for title in other_titles:
                                title_section = soup.find(['h1', 'h2', 'h3', 'h4'], string=re.compile(title, re.IGNORECASE))
                                if title_section:
                                    info = title_section.find_next(['p', 'div', 'span'])
                                    if info:
                                        name = info.get_text().strip()
                                        # Clean up name if needed - fix escape sequence
                                        name = re.sub(fr'{title}|hon\.', '', name, flags=re.IGNORECASE).strip()
                                        
                                        officials.append({
                                            "title": title,
                                            "name": name,
                                            "term": "Current"
                                        })
                                        logging.info(f"Found {title}: {name}")
                            
                            # Also try to find city council president
                            council_president = soup.find(['h1', 'h2', 'h3', 'h4'], 
                                                        string=re.compile('Council President|Speaker of the Council', re.IGNORECASE))
                            if council_president:
                                info = council_president.find_next(['p', 'div', 'span'])
                                if info:
                                    name = info.get_text().strip()
                                    # Clean up name
                                    name = re.sub(r'council president|speaker|hon\.', '', name, flags=re.IGNORECASE).strip()
                                    
                                    officials.append({
                                        "title": "City Council Speaker",
                                        "name": name,
                                        "term": "Current"
                                    })
                                    logging.info(f"Found City Council Speaker: {name}")
                except Exception as e:
                    logging.error(f"Error fetching NYC officials: {str(e)}")
                
                # Also try to fetch borough presidents
                try:
                    borough_url = "https://www.nyc.gov/site/bpweb/index.page"
                    async with session.get(borough_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find borough president sections
                            borough_sections = soup.find_all(['h2', 'h3'], string=re.compile('Borough President', re.IGNORECASE))
                            for section in borough_sections:
                                # Try to determine which borough
                                borough = None
                                for b in ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']:
                                    if b.lower() in section.get_text().lower():
                                        borough = b
                                        break
                                
                                if borough:
                                    # Try to find the name
                                    name_elem = section.find_next(['p', 'div', 'span'])
                                    if name_elem:
                                        name = name_elem.get_text().strip()
                                        # Clean up name
                                        name = re.sub(r'borough president|hon\.', '', name, flags=re.IGNORECASE).strip()
                                        
                                        officials.append({
                                            "title": f"{borough} Borough President",
                                            "name": name,
                                            "term": "Current"
                                        })
                                        logging.info(f"Found {borough} Borough President: {name}")
                except Exception as e:
                    logging.error(f"Error fetching NYC borough presidents: {str(e)}")
        
        # Add more city-specific scrapers here for other locations
        # elif location.city.lower() == "chicago" and location.state.lower() == "illinois":
        #     # Implementation for Chicago
        
        else:
            # Generic approach for other cities using web search
            logging.info(f"No city-specific scraper for {location.city}, using generic approach")
            import json
            
            # Construct a search query
            query = f"{location.city} {location.state} elected officials mayor city council official website"
            
            async with aiohttp.ClientSession() as session:
                # First try: direct scraping of common city website patterns
                try:
                    # Try common URL patterns for city websites
                    # Handle spaces in city names for URL construction
                    city_slug = location.city.lower().replace(' ', '')
                    state_slug = location.state.lower().replace(' ', '')
                    
                    potential_urls = [
                        f"https://www.{city_slug}.gov",
                        f"https://www.{city_slug}{state_slug}.gov",
                        f"https://www.cityof{city_slug}.gov",
                        f"https://www.cityof{city_slug}.org",
                        f"https://www.{city_slug}.org"
                    ]
                    
                    if ' ' in location.city:
                        # Add additional patterns for cities with spaces
                        city_with_dash = location.city.lower().replace(' ', '-')
                        potential_urls.extend([
                            f"https://www.{city_with_dash}.gov",
                            f"https://www.cityof{city_with_dash}.gov",
                            f"https://www.cityof{city_with_dash}.org", 
                            f"https://www.{city_with_dash}.org"
                        ])
                    
                    for url in potential_urls:
                        try:
                            logging.info(f"Trying URL: {url}")
                            async with session.get(url, timeout=5) as response:
                                if response.status == 200:
                                    html = await response.text()
                                    soup = BeautifulSoup(html, 'html.parser')
                                    
                                    # Look for mayor
                                    mayor_links = soup.find_all('a', string=re.compile('Mayor|mayor'))
                                    for link in mayor_links:
                                        # Extract the mayor name if possible
                                        link_text = link.get_text().strip()
                                        if "mayor" in link_text.lower() and len(link_text.split()) > 1:
                                            # This might contain the mayor's name
                                            name = re.sub(r'mayor|office of the', '', link_text, flags=re.IGNORECASE).strip()
                                            # Validate name - it should look like a person's name
                                            name_parts = name.split()
                                            if len(name_parts) >= 2 and all(part[0].isupper() for part in name_parts if len(part) > 1):
                                                officials.append({
                                                    "title": "Mayor",
                                                    "name": name,
                                                    "term": "Current"
                                                })
                                                logging.info(f"Found Mayor: {name}")
                                                break
                                    
                                    # Look for council members
                                    council_links = soup.find_all('a', string=re.compile('Council|council|Alderman|alderman'))
                                    for link in council_links:
                                        if "city council" in link.get_text().lower() and link.get('href'):
                                            # Follow this link to the council page
                                            council_url = link.get('href')
                                            if not council_url.startswith('http'):
                                                # Handle relative URLs
                                                if council_url.startswith('/'):
                                                    council_url = f"{url}{council_url}"
                                                else:
                                                    council_url = f"{url}/{council_url}"
                                                    
                                            async with session.get(council_url) as council_response:
                                                if council_response.status == 200:
                                                    council_html = await council_response.text()
                                                    council_soup = BeautifulSoup(council_html, 'html.parser')
                                                    
                                                    # Look for council member names
                                                    for tag in council_soup.find_all(['h2', 'h3', 'h4', 'p', 'div']):
                                                        tag_text = tag.get_text().strip()
                                                        district_match = re.search(r'district\s*(\d+|[IVX]+)', tag_text, re.IGNORECASE)
                                                        ward_match = re.search(r'ward\s*(\d+|[IVX]+)', tag_text, re.IGNORECASE)
                                                        
                                                        if district_match or ward_match:
                                                            # This might be a council member
                                                            if district_match:
                                                                district = district_match.group(1)
                                                                title_type = "District" 
                                                            else:
                                                                district = ward_match.group(1)
                                                                title_type = "Ward"
                                                                
                                                            # Try to extract the name using a more robust pattern
                                                            # Looking for first and last name with capitals
                                                            tag_text = tag_text.strip()
                                                            name_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)')
                                                            name_matches = name_pattern.findall(tag_text)
                                                            
                                                            if name_matches:
                                                                # Use the longest match as the name
                                                                name = max(name_matches, key=len)
                                                                # Validate it's not just "City Council" or similar
                                                                if "city" not in name.lower() and "council" not in name.lower() and len(name.split()) >= 2:
                                                                    officials.append({
                                                                        "title": f"City Council Member ({title_type} {district})",
                                                                        "name": name,
                                                                        "term": "Current"
                                                                    })
                                                                    logging.info(f"Found Council Member: {name} ({title_type} {district})")
                                    
                                    # If we've found at least a mayor and a council member, consider it a success
                                    if any(o['title'] == 'Mayor' for o in officials) and \
                                       any('Council Member' in o['title'] for o in officials):
                                        break
                        except Exception as e:
                            logging.warning(f"Error trying URL {url}: {str(e)}")
                except Exception as e:
                    logging.warning(f"Error in direct website scraping: {str(e)}")
                
                # Second try: use search API if no officials found
                if not officials:
                    search_url = "https://api.bing.microsoft.com/v7.0/search"
                    headers = {
                        "Ocp-Apim-Subscription-Key": os.environ.get("BING_SEARCH_API_KEY", "")
                    }
                    
                    # Skip if no API key is available
                    if not headers["Ocp-Apim-Subscription-Key"]:
                        logging.warning("No Bing Search API key available. Using fallback data.")
                        return _get_fallback_officials(location)
                    
                    params = {
                        "q": query,
                        "count": 5,
                        "offset": 0,
                        "mkt": "en-US"
                    }
                    
                    try:
                        async with session.get(search_url, headers=headers, params=params) as response:
                            if response.status != 200:
                                logging.warning(f"Failed to search for officials: Status {response.status}")
                                return _get_fallback_officials(location)
                            
                            search_results = await response.json()
                            
                            # Process search results to find official websites
                            for result in search_results.get("webPages", {}).get("value", []):
                                url = result.get("url", "")
                                # Look for .gov domains or official city websites
                                if ".gov" in url or f"{location.city.lower().replace(' ', '')}" in url.lower().replace(' ', ''):
                                    try:
                                        async with session.get(url, timeout=10) as page_response:
                                            if page_response.status == 200:
                                                html = await page_response.text()
                                                soup = BeautifulSoup(html, 'html.parser')
                                                
                                                # Look for common patterns of official listings
                                                for heading in soup.find_all(['h1', 'h2', 'h3', 'h4'], 
                                                                          string=re.compile('(Mayor|Council|Officials|Elected)', re.IGNORECASE)):
                                                    # Extract the section following this heading
                                                    section = heading.find_next(['ul', 'div', 'table'])
                                                    if not section:
                                                        continue
                                                    
                                                    # Extract names from list items
                                                    for item in section.find_all(['li', 'tr']):
                                                        text = item.get_text().strip()
                                                        # Try to identify patterns like "Mayor: John Doe" or "John Doe, Mayor"
                                                        mayor_match = re.search(r'Mayor[:\s]*(.*)', text, re.IGNORECASE)
                                                        council_match = re.search(r'Council\s*Member[:\s]*(.*)', text, re.IGNORECASE)
                                                        district_match = re.search(r'District\s*(\d+)[:\s]*(.*)', text, re.IGNORECASE)
                                                        
                                                        if mayor_match:
                                                            mayor_name = mayor_match.group(1).strip()
                                                            # Validate name
                                                            if len(mayor_name.split()) >= 2 and all(part[0].isupper() for part in mayor_name.split() if len(part) > 1):
                                                                officials.append({
                                                                    "title": "Mayor",
                                                                    "name": mayor_name,
                                                                    "term": "Current"
                                                                })
                                                        elif council_match:
                                                            council_name = council_match.group(1).strip()
                                                            # Validate name
                                                            if len(council_name.split()) >= 2 and all(part[0].isupper() for part in council_name.split() if len(part) > 1):
                                                                officials.append({
                                                                    "title": "City Council Member",
                                                                    "name": council_name,
                                                                    "term": "Current"
                                                                })
                                                        elif district_match:
                                                            district = district_match.group(1)
                                                            name = district_match.group(2).strip()
                                                            # Validate name
                                                            if len(name.split()) >= 2 and all(part[0].isupper() for part in name.split() if len(part) > 1):
                                                                officials.append({
                                                                    "title": f"City Council Member (District {district})",
                                                                    "name": name,
                                                                    "term": "Current"
                                                                })
                                                
                                                # If we found at least the mayor and one council member, stop searching
                                                if len(officials) >= 2:
                                                    break
                                    except Exception as e:
                                        logging.warning(f"Error processing search result URL {url}: {str(e)}")
                    except Exception as e:
                        logging.error(f"Error in search API: {str(e)}")
        
        # If we couldn't find any officials, use fallback data
        if not officials:
            logging.warning("No officials found. Using fallback data.")
            return _get_fallback_officials(location)
        
        # Remove any duplicate entries
        officials = _remove_duplicate_officials(officials)
        
        return officials
    
    except Exception as e:
        logging.error(f"Error fetching elected officials: {str(e)}")
        import traceback
        traceback.print_exc()
        return _get_fallback_officials(location)

def _get_fallback_officials(location: LocationInfo) -> List[Dict[str, str]]:
    """
    Provide fallback officials data when web scraping fails.
    
    Args:
        location: LocationInfo object with city and state
        
    Returns:
        List of dictionaries with fallback officials data
    """
    # Austin, Texas fallback data
    if location.city.lower() == "austin" and location.state.lower() == "texas":
        return [
            {"title": "Mayor", "name": "Kirk Watson", "term": "2022-2026"},
            {"title": "City Manager", "name": "Spencer Cronk", "term": "2018-present"},
            {"title": "City Council Member (District 1)", "name": "Natasha Harper-Madison", "term": "2019-2024"},
            {"title": "City Council Member (District 2)", "name": "Vanessa Fuentes", "term": "2021-2025"},
            {"title": "City Council Member (District 3)", "name": "Sabino Renteria", "term": "2015-2023"},
            {"title": "City Council Member (District 4)", "name": "Chito Vela", "term": "2022-2026"},
            {"title": "City Council Member (District 5)", "name": "Ryan Alter", "term": "2023-2027"},
            {"title": "City Council Member (District 6)", "name": "Mackenzie Kelly", "term": "2021-2025"},
            {"title": "City Council Member (District 7)", "name": "Leslie Pool", "term": "2021-2025"},
            {"title": "City Council Member (District 8)", "name": "Paige Ellis", "term": "2023-2027"},
            {"title": "City Council Member (District 9)", "name": "Zo Qadri", "term": "2023-2027"},
            {"title": "City Council Member (District 10)", "name": "Alison Alter", "term": "2021-2025"},
            {"title": "City Clerk", "name": "Myrna Rios", "term": "2020-2026"},
            {"title": "City Auditor", "name": "Corrie Stokes", "term": "2019-2025"},
            {"title": "Municipal Court Presiding Judge", "name": "Sherry Statman", "term": "2022-2026"}
        ]
    
    # New York City fallback data
    elif location.city.lower() == "new york" and location.state.lower() == "new york":
        return [
            {"title": "Mayor", "name": "Eric Adams", "term": "2022-2026"},
            {"title": "Public Advocate", "name": "Jumaane Williams", "term": "2019-2025"},
            {"title": "Comptroller", "name": "Brad Lander", "term": "2022-2026"},
            {"title": "City Council Speaker", "name": "Adrienne Adams", "term": "2022-2026"},
            {"title": "Manhattan Borough President", "name": "Mark Levine", "term": "2022-2026"},
            {"title": "Brooklyn Borough President", "name": "Antonio Reynoso", "term": "2022-2026"},
            {"title": "Queens Borough President", "name": "Donovan Richards", "term": "2020-2024"},
            {"title": "Bronx Borough President", "name": "Vanessa Gibson", "term": "2022-2026"},
            {"title": "Staten Island Borough President", "name": "Vito Fossella", "term": "2022-2026"}
        ]
    
    # Chicago, Illinois fallback data
    elif location.city.lower() == "chicago" and location.state.lower() == "illinois":
        return [
            {"title": "Mayor", "name": "Brandon Johnson", "term": "2023-2027"},
            {"title": "City Clerk", "name": "Anna Valencia", "term": "2023-2027"},
            {"title": "City Treasurer", "name": "Melissa Conyears-Ervin", "term": "2019-2023"},
            {"title": "City Council President", "name": "Scott Waguespack", "term": "2019-2023"},
            {"title": "City Council Member (Ward 1)", "name": "Daniel La Spata", "term": "2019-2023"},
            {"title": "City Council Member (Ward 2)", "name": "Brian Hopkins", "term": "2015-2023"},
            {"title": "City Council Member (Ward 3)", "name": "Pat Dowell", "term": "2007-2023"},
            {"title": "City Council Member (Ward 4)", "name": "Sophia King", "term": "2016-2023"},
            {"title": "City Council Member (Ward 5)", "name": "Leslie Hairston", "term": "1999-2023"}
        ]
    
    # Los Angeles, California fallback data
    elif location.city.lower() == "los angeles" and location.state.lower() == "california":
        return [
            {"title": "Mayor", "name": "Karen Bass", "term": "2022-2026"},
            {"title": "City Attorney", "name": "Hydee Feldstein Soto", "term": "2022-2026"},
            {"title": "City Controller", "name": "Kenneth Mejia", "term": "2022-2026"},
            {"title": "City Council President", "name": "Paul Krekorian", "term": "2020-2024"},
            {"title": "City Council Member (District 1)", "name": "Eunisses Hernandez", "term": "2022-2026"},
            {"title": "City Council Member (District 2)", "name": "Paul Krekorian", "term": "2020-2024"},
            {"title": "City Council Member (District 3)", "name": "Bob Blumenfield", "term": "2020-2024"},
            {"title": "City Council Member (District 4)", "name": "Nithya Raman", "term": "2020-2024"},
            {"title": "City Council Member (District 5)", "name": "Katy Yaroslavsky", "term": "2022-2026"}
        ]
    
    # Seattle, Washington fallback data
    elif location.city.lower() == "seattle" and location.state.lower() == "washington":
        return [
            {"title": "Mayor", "name": "Bruce Harrell", "term": "2022-2026"},
            {"title": "City Attorney", "name": "Ann Davison", "term": "2022-2026"},
            {"title": "City Council President", "name": "Debora Juarez", "term": "2020-2024"},
            {"title": "City Council Member (District 1)", "name": "Lisa Herbold", "term": "2019-2023"},
            {"title": "City Council Member (District 2)", "name": "Tammy Morales", "term": "2020-2024"},
            {"title": "City Council Member (District 3)", "name": "Kshama Sawant", "term": "2019-2023"},
            {"title": "City Council Member (District 4)", "name": "Alex Pedersen", "term": "2020-2024"},
            {"title": "City Council Member (District 5)", "name": "Debora Juarez", "term": "2020-2024"},
            {"title": "City Council Member (District 6)", "name": "Dan Strauss", "term": "2020-2024"},
            {"title": "City Council Member (District 7)", "name": "Andrew Lewis", "term": "2020-2024"}
        ]
    
    # Generic fallback data for other cities
    return [
        {"title": "Mayor", "name": f"Mayor of {location.city}", "term": "Current"},
        {"title": "City Manager", "name": f"City Manager", "term": "Current"},
        {"title": "City Council Member (At Large)", "name": "Council Member 1", "term": "Current"},
        {"title": "City Council Member (At Large)", "name": "Council Member 2", "term": "Current"},
        {"title": "City Council Member (At Large)", "name": "Council Member 3", "term": "Current"}
    ] 