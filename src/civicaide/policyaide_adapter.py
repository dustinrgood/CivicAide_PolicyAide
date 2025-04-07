#!/usr/bin/env python
"""
PolicyAide Adapter for Census MCP

This adapter provides a bridge between PolicyAide's existing code and our Census MCP.
It allows PolicyAide to use the Census MCP as an alternative or supplement to the 
direct Census API calls in the context_agents.py file.

The adapter implements the same interface as the existing Census API client,
making it a drop-in replacement that leverages our MCP backend.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CensusMCPAdapter:
    """
    Adapter class that provides the same interface as PolicyAide's CensusAPI class
    but uses our Census MCP server instead of direct Census API calls.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:8050"):
        """Initialize the adapter with the URL to our Census MCP server."""
        self.mcp_url = mcp_url
        self.client = None  # We'll use this to maintain compatibility with the original interface
        
        # Test connection to MCP
        try:
            response = requests.get(mcp_url)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Census MCP at {mcp_url}")
                self.server_info = response.json()
                logger.info(f"MCP Version: {self.server_info.get('version')}")
                # Set this to True to indicate that the "client" is available
                self.client = True
            else:
                logger.warning(f"Census MCP returned status code {response.status_code}")
                self.server_info = {}
        except Exception as e:
            logger.error(f"Failed to connect to Census MCP: {str(e)}")
            raise ConnectionError(f"Cannot connect to Census MCP at {mcp_url}. Is the server running?")
    
    def query_mcp(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query the Census MCP with a natural language prompt and optional parameters.
        
        Args:
            prompt: Natural language query about Census data
            params: Optional parameters to customize the query
            
        Returns:
            Dictionary containing the MCP response
        """
        if params is None:
            params = {}
            
        payload = {
            "mcp_version": "0.1.0",
            "params": params,
            "prompt": prompt
        }
        
        try:
            response = requests.post(f"{self.mcp_url}/mcp", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Census MCP error: {response.status_code} - {response.text}")
                raise Exception(f"Census MCP returned error status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error querying Census MCP: {str(e)}")
            raise
    
    def get_demographics(self, location_info) -> Dict[str, Any]:
        """
        Get demographic data for a location using the Census MCP.
        This method maintains the same interface as the original CensusAPI.get_demographics method.
        
        Args:
            location_info: Object with location details (city, state, county)
            
        Returns:
            Dictionary with demographic data in the expected format
        """
        # Extract location information
        city = getattr(location_info, "city", None)
        state = getattr(location_info, "state", None)
        county = getattr(location_info, "county", None)
        
        if not state:
            logger.error("Missing required location information: state")
            return {}
            
        # Construct the prompt
        if city:
            prompt = f"Comprehensive demographic data for {city}, {state}"
        else:
            prompt = f"Comprehensive demographic data for {state}"
            
        if county:
            prompt += f" in {county} county"
            
        # Define the variables we want to retrieve
        # These match the variables used in the original CensusAPI
        variables = [
            "B01003_001E",  # Total population
            "B01002_001E",  # Median age
            "B19013_001E",  # Median household income
            "B19025_001E",  # Mean household income
            "B17001_002E",  # Poverty count
            "B02001_002E",  # White population
            "B02001_003E",  # Black population
            "B02001_005E",  # Asian population
            "B03003_003E",  # Hispanic/Latino population
            "B15003_022E",  # Bachelor's degree
            "B15003_023E",  # Graduate degree
            "B15003_017E",  # High school graduate
        ]
        
        # Query the MCP
        params = {
            "variables": variables,
            "dataset": "acs/acs5",  # Use 5-year ACS data for most reliable estimates
            "year": "2022"          # Use the most recent year available
        }
        
        # Add specific geographic parameters
        if city:
            # For specific cities we know, provide the exact FIPS place code
            if city.lower() == "austin" and state.lower() == "texas":
                params["predicates"] = {"in": "state:48", "for": "place:05000"}
            elif city.lower() == "san francisco" and state.lower() == "california":
                params["predicates"] = {"in": "state:06", "for": "place:67000"}
            elif city.lower() == "new york" and state.lower() == "new york":
                params["predicates"] = {"in": "state:36", "for": "place:51000"}
            elif city.lower() == "miami" and state.lower() == "florida":
                params["predicates"] = {"in": "state:12", "for": "place:45000"}
            elif city.lower() == "elgin" and state.lower() == "illinois":
                params["predicates"] = {"in": "state:17", "for": "place:23074"}  # Elgin, Illinois FIPS place code
            else:
                # For other cities, we'll let the MCP try to determine the place
                params["geographic_level"] = "place"
                params["location"] = f"{city}, {state}"
        elif county:
            params["geographic_level"] = "county"
            params["location"] = f"{county}, {state}"
        else:
            params["geographic_level"] = "state"
            params["location"] = state
        
        try:
            response = self.query_mcp(prompt, params)
            
            # Check if we got a valid response
            if response.get("status") == "error":
                logger.error(f"Census MCP error: {response.get('error')}")
                return {}
                
            # Extract the context with the census data
            context_items = response.get("context", [])
            if not context_items:
                logger.warning("No context items in Census MCP response")
                return {}
                
            census_data = context_items[0].get("data", {})
            
            # Now transform the MCP response into the format expected by PolicyAide
            result = {}
            
            # Extract items and variable mappings
            items = census_data.get("items", [])
            
            # Find the location data (should match our city/state)
            location_data = None
            for item in items:
                name = item.get("NAME", "").lower()
                if city and city.lower() in name and state.lower() in name:
                    location_data = item
                    break
                elif not city and county and county.lower() in name and state.lower() in name:
                    location_data = item
                    break
                elif not city and not county and state.lower() in name:
                    location_data = item
                    break
                    
            # If we didn't find a specific match, use the first item if available
            if not location_data and items:
                location_data = items[0]
                
            # If we have location data, extract demographic information
            if location_data:
                # Map Census variable codes to our expected format
                var_mapping = {
                    "B01003_001E": "population",
                    "B01002_001E": "median_age",
                    "B19013_001E": "median_household_income",
                    "B19025_001E": "mean_household_income"
                }
                
                # Extract basic demographic data
                for census_var, our_var in var_mapping.items():
                    if census_var in location_data:
                        try:
                            result[our_var] = float(location_data[census_var])
                        except (ValueError, TypeError):
                            pass
                
                # Extract racial composition
                race_vars = {
                    "B02001_002E": "White",
                    "B02001_003E": "Black",
                    "B02001_005E": "Asian",
                    "B03003_003E": "Hispanic"
                }
                
                if "B01003_001E" in location_data:
                    try:
                        total_pop = float(location_data["B01003_001E"])
                        if total_pop > 0:
                            racial_composition = {}
                            for census_var, race_name in race_vars.items():
                                if census_var in location_data:
                                    try:
                                        race_pop = float(location_data[census_var])
                                        racial_composition[race_name] = (race_pop / total_pop) * 100
                                    except (ValueError, TypeError):
                                        pass
                            if racial_composition:
                                result["racial_composition"] = racial_composition
                    except (ValueError, TypeError):
                        pass
                
                # Extract education levels
                edu_vars = {
                    "B15003_017E": "HighSchoolOrHigher",
                    "B15003_022E": "BachelorsOrHigher",
                    "B15003_023E": "GraduateOrProfessional"
                }
                
                if "B01003_001E" in location_data:
                    try:
                        total_pop = float(location_data["B01003_001E"])
                        if total_pop > 0:
                            education_levels = {}
                            for census_var, edu_name in edu_vars.items():
                                if census_var in location_data:
                                    try:
                                        edu_pop = float(location_data[census_var])
                                        education_levels[edu_name] = (edu_pop / total_pop) * 100
                                    except (ValueError, TypeError):
                                        pass
                            if education_levels:
                                result["education_levels"] = education_levels
                    except (ValueError, TypeError):
                        pass
                
                # Format household income as expected by PolicyAide
                if "median_household_income" in result or "mean_household_income" in result:
                    household_income = {}
                    if "median_household_income" in result:
                        household_income["median"] = result.pop("median_household_income")
                    if "mean_household_income" in result:
                        household_income["mean"] = result.pop("mean_household_income")
                    result["household_income"] = household_income
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting demographics from Census MCP: {str(e)}")
            return {}

# Usage example with the original LocationInfo model
if __name__ == "__main__":
    # Import or define LocationInfo
    class LocationInfo:
        def __init__(self, city, state, county=None):
            self.city = city
            self.state = state
            self.county = county
    
    # Create test locations
    test_locations = [
        LocationInfo(city="Elgin", state="Illinois", county="Kane"),
        LocationInfo(city="Austin", state="Texas", county="Travis"),
        LocationInfo(city="San Francisco", state="California"),
        LocationInfo(city="New York", state="New York"),
        LocationInfo(city="Miami", state="Florida", county="Miami-Dade")
    ]
    
    # Initialize adapter
    print("Initializing Census MCP Adapter...")
    adapter = CensusMCPAdapter()
    
    # Test with each location
    for location in test_locations:
        print(f"\nTesting with location: {location.city}, {location.state}")
        try:
            # Get demographics using the adapter
            demographics = adapter.get_demographics(location)
            
            # Print the results
            if demographics:
                print(f"Demographics for {location.city}, {location.state}:")
                
                if "population" in demographics:
                    print(f"  Population: {int(demographics.get('population', 0)):,}")
                
                if "median_age" in demographics:
                    print(f"  Median Age: {demographics.get('median_age', 0):.1f}")
                
                if "household_income" in demographics:
                    income = demographics.get("household_income", {})
                    if "median" in income:
                        print(f"  Median Household Income: ${int(income.get('median', 0)):,}")
                    if "mean" in income:
                        print(f"  Mean Household Income: ${int(income.get('mean', 0)):,}")
                
                if "racial_composition" in demographics:
                    print("  Racial Composition:")
                    for race, percentage in demographics.get("racial_composition", {}).items():
                        print(f"    {race}: {percentage:.1f}%")
                
                if "education_levels" in demographics:
                    print("  Education Levels:")
                    for level, percentage in demographics.get("education_levels", {}).items():
                        print(f"    {level}: {percentage:.1f}%")
            else:
                print(f"No demographic data found for {location.city}, {location.state}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
            
    print("\nTest complete.") 