import json
import requests
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import os
import re
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

# MCP Models
class MCPRequest(BaseModel):
    """Model for MCP request"""
    mcp_version: str = Field(default="0.1.0")
    params: Dict[str, Any] = Field(default_factory=dict)
    prompt: str

class MCPResponse(BaseModel):
    """Model for MCP response"""
    mcp_version: str = Field(default="0.1.0")
    context: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "success"
    error: Optional[str] = None

# Census API config
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")  # Get key from environment variable
if not CENSUS_API_KEY:
    raise ValueError("CENSUS_API_KEY environment variable is not set")
    
BASE_URL = "https://api.census.gov/data"

# Common Census variables
CENSUS_VARIABLES = {
    # Population variables
    "population": "B01003_001E",
    "population_age_18_over": "B01001_007E",
    "population_age_65_over": "B01001_020E",
    
    # Demographic variables
    "median_age": "B01002_001E",
    "total_male": "B01001_002E",
    "total_female": "B01001_026E",
    
    # Race/ethnicity variables
    "white_alone": "B02001_002E",
    "black_alone": "B02001_003E",
    "asian_alone": "B02001_005E",
    "hispanic_latino": "B03003_003E",
    
    # Education variables
    "high_school_graduate": "B15003_017E",
    "bachelors_degree": "B15003_022E",
    "graduate_degree": "B15003_023E",
    
    # Income variables
    "median_household_income": "B19013_001E",
    "mean_household_income": "B19025_001E",
    "income_per_capita": "B19301_001E",
    
    # Poverty variables
    "poverty_all_people": "B17001_002E",
    "poverty_under_18": "B17001_004E",
    "poverty_65_over": "B17001_015E",
    
    # Housing variables
    "housing_units": "B25001_001E",
    "median_home_value": "B25077_001E",
    "median_rent": "B25064_001E",
    "occupied_housing_units": "B25003_001E",
    "vacant_housing_units": "B25002_003E",
    
    # Employment variables
    "employed": "B23025_004E",
    "unemployed": "B23025_005E",
    "in_labor_force": "B23025_002E",
    
    # Transportation variables
    "commute_time": "B08136_001E",
    "public_transportation": "B08301_010E",
    "work_from_home": "B08301_021E",
    
    # Healthcare variables
    "with_health_insurance": "B27001_001E",
    "no_health_insurance": "B27001_005E",
    
    # Broadband internet variables
    "with_internet_subscription": "B28002_004E",
    "no_internet_access": "B28002_013E"
}

# Dataset mapping
DATASETS = {
    "acs1": "acs/acs1",              # American Community Survey 1-year estimates
    "acs5": "acs/acs5",              # American Community Survey 5-year estimates
    "acs1profile": "acs/acs1/profile",  # ACS 1-year profiles
    "acs5profile": "acs/acs5/profile",  # ACS 5-year profiles
    "decennial": "dec/pl",           # Decennial Census (PL 94-171)
    "decennial_dp": "dec/dp",        # Decennial Census Demographic Profile
    "decennial_pes": "dec/pes",      # Decennial Post-Enumeration Survey
    "cps": "cps/basic",              # Current Population Survey Basic
    "cps_asec": "cps/asec/mar",      # Current Population Survey ASEC
}

# Geography levels
GEOGRAPHY_LEVELS = {
    "us": "us:*",
    "state": "state:*",
    "county": "county:*",
    "tract": "tract:*",
    "block_group": "block group:*",
    "place": "place:*",
    "metropolitan": "metropolitan statistical area/micropolitan statistical area:*",
    "zip": "zip code tabulation area:*"
}

def parse_location(prompt: str) -> Dict[str, str]:
    """
    Parse location information from the prompt.
    Returns a dictionary of predicates to filter Census data.
    """
    predicates = {"for": "state:*"}  # Default to all states
    
    # Extract state names
    state_pattern = r"in\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)"
    state_match = re.search(state_pattern, prompt)
    
    if state_match:
        state_name = state_match.group(1).strip()
        # Get state FIPS code (this would use a lookup table in a full implementation)
        # For demo, we'll use a simplified approach
        if state_name.lower() == "texas":
            predicates = {"for": "state:48"}
        elif state_name.lower() == "california":
            predicates = {"for": "state:06"}
        elif state_name.lower() == "new york":
            predicates = {"for": "state:36"}
        elif state_name.lower() == "florida":
            predicates = {"for": "state:12"}
        # We would add more states here in a complete implementation
    
    # Extract city names
    city_pattern = r"(for|about|in|of)\s+([A-Za-z\s]+?)(?:,|\sin\s|\s(?=population)|\s(?=demographic))"
    city_match = re.search(city_pattern, prompt.lower())
    
    if city_match:
        city_name = city_match.group(2).strip()
        # Check for specific major cities
        if "austin" in city_name.lower():
            if "for" in predicates and predicates["for"].startswith("state:"):
                # If we have a specific state, get places in that state
                state_code = predicates["for"].split(":")[1]
                if state_code == "48":  # Texas
                    predicates = {"in": "state:48", "for": "place:05000"}  # Austin, Texas FIPS place code
                else:
                    predicates = {"for": "place:*", "in": f"state:{state_code}"}
            else:
                predicates = {"in": "state:48", "for": "place:05000"}  # Default to Austin, TX
        elif "san francisco" in city_name.lower():
            predicates = {"in": "state:06", "for": "place:67000"}  # San Francisco, CA
        elif "new york city" in city_name.lower() or "new york" in city_name.lower():
            predicates = {"in": "state:36", "for": "place:51000"}  # New York City, NY
        elif "miami" in city_name.lower():
            predicates = {"in": "state:12", "for": "place:45000"}  # Miami, FL
        else:
            # For other cities, use wildcard match for place
            if "for" in predicates and predicates["for"].startswith("state:"):
                state_code = predicates["for"].split(":")[1]
                if state_code != "*":
                    predicates = {"in": f"state:{state_code}", "for": "place:*"}
                else:
                    predicates = {"for": "place:*"}
            else:
                predicates = {"for": "place:*"}
    
    # Check for county level
    if "county" in prompt.lower() or "counties" in prompt.lower():
        if "for" in predicates and predicates["for"].startswith("state:"):
            # If we have a specific state, get counties in that state
            state_code = predicates["for"].split(":")[1]
            if state_code != "*":
                predicates = {"in": f"state:{state_code}", "for": "county:*"}
            else:
                predicates = {"for": "county:*"}
        else:
            predicates = {"for": "county:*"}
    
    # If no specific place was matched but "city" is mentioned, use place level
    if "for" not in predicates or not predicates["for"].startswith("place:"):
        if "city" in prompt.lower() or "cities" in prompt.lower():
            if "for" in predicates and predicates["for"].startswith("state:"):
                # If we have a specific state, get places in that state
                state_code = predicates["for"].split(":")[1]
                if state_code != "*":
                    predicates = {"in": f"state:{state_code}", "for": "place:*"}
                else:
                    predicates = {"for": "place:*"}
            else:
                predicates = {"for": "place:*"}
    
    return predicates

def determine_dataset(prompt: str) -> str:
    """Determine which Census dataset to use based on the prompt"""
    # Default to ACS 5-year data (most comprehensive)
    dataset = "acs/acs5"
    
    # Check if we need a specific dataset
    if "current population survey" in prompt.lower() or "cps" in prompt.lower():
        if "asec" in prompt.lower() or "annual social and economic" in prompt.lower():
            dataset = DATASETS["cps_asec"]
        else:
            dataset = DATASETS["cps"]
    elif "decennial" in prompt.lower() or "census 2020" in prompt.lower():
        if "demographic profile" in prompt.lower() or "dp" in prompt.lower():
            dataset = DATASETS["decennial_dp"]
        else:
            dataset = DATASETS["decennial"]
    elif "1-year" in prompt.lower() or "1 year" in prompt.lower() or "acs1" in prompt.lower():
        if "profile" in prompt.lower():
            dataset = DATASETS["acs1profile"]
        else:
            dataset = DATASETS["acs1"]
    elif "5-year" in prompt.lower() or "5 year" in prompt.lower() or "acs5" in prompt.lower():
        if "profile" in prompt.lower():
            dataset = DATASETS["acs5profile"]
        else:
            dataset = DATASETS["acs5"]
    
    return dataset

def determine_year(prompt: str) -> str:
    """Extract year from prompt or use latest available"""
    # Default to 2022 for ACS data
    year = "2022"
    
    # Find years in the prompt
    year_pattern = r'\b(20\d{2})\b'
    year_matches = re.findall(year_pattern, prompt)
    
    if year_matches:
        # Use the first year found in the prompt
        year = year_matches[0]
    
    return year

def determine_variables(prompt: str) -> List[str]:
    """
    Determine which Census variables to include based on the prompt.
    Always includes the NAME variable for location names.
    """
    variables = ["NAME"]  # Always include location names
    
    # Check for demographic data
    if any(term in prompt.lower() for term in ["population", "people", "residents"]):
        variables.append(CENSUS_VARIABLES["population"])
    
    if any(term in prompt.lower() for term in ["age", "median age", "elderly", "young"]):
        variables.append(CENSUS_VARIABLES["median_age"])
        
    if any(term in prompt.lower() for term in ["gender", "sex", "male", "female"]):
        variables.append(CENSUS_VARIABLES["total_male"])
        variables.append(CENSUS_VARIABLES["total_female"])
        
    if any(term in prompt.lower() for term in ["race", "ethnicity", "white", "black", "hispanic", "asian"]):
        variables.append(CENSUS_VARIABLES["white_alone"])
        variables.append(CENSUS_VARIABLES["black_alone"])
        variables.append(CENSUS_VARIABLES["asian_alone"])
        variables.append(CENSUS_VARIABLES["hispanic_latino"])
    
    # Check for education data
    if any(term in prompt.lower() for term in ["education", "school", "college", "degree", "graduate"]):
        variables.append(CENSUS_VARIABLES["high_school_graduate"])
        variables.append(CENSUS_VARIABLES["bachelors_degree"])
        variables.append(CENSUS_VARIABLES["graduate_degree"])
    
    # Check for income/poverty data
    if any(term in prompt.lower() for term in ["income", "earnings", "salary", "wages"]):
        variables.append(CENSUS_VARIABLES["median_household_income"])
        variables.append(CENSUS_VARIABLES["income_per_capita"])
    
    if any(term in prompt.lower() for term in ["poverty", "poor", "low income"]):
        variables.append(CENSUS_VARIABLES["poverty_all_people"])
        variables.append(CENSUS_VARIABLES["poverty_under_18"])
        variables.append(CENSUS_VARIABLES["poverty_65_over"])
    
    # Check for housing data
    if any(term in prompt.lower() for term in ["housing", "homes", "apartments", "rent", "ownership"]):
        variables.append(CENSUS_VARIABLES["housing_units"])
        variables.append(CENSUS_VARIABLES["median_home_value"])
        variables.append(CENSUS_VARIABLES["median_rent"])
        variables.append(CENSUS_VARIABLES["vacant_housing_units"])
    
    # Check for employment data
    if any(term in prompt.lower() for term in ["employment", "unemployment", "jobs", "labor", "work"]):
        variables.append(CENSUS_VARIABLES["employed"])
        variables.append(CENSUS_VARIABLES["unemployed"])
        variables.append(CENSUS_VARIABLES["in_labor_force"])
    
    # Check for transportation data
    if any(term in prompt.lower() for term in ["transportation", "commute", "transit", "travel"]):
        variables.append(CENSUS_VARIABLES["commute_time"])
        variables.append(CENSUS_VARIABLES["public_transportation"])
        variables.append(CENSUS_VARIABLES["work_from_home"])
    
    # Check for internet data
    if any(term in prompt.lower() for term in ["internet", "broadband", "connectivity", "digital"]):
        variables.append(CENSUS_VARIABLES["with_internet_subscription"])
        variables.append(CENSUS_VARIABLES["no_internet_access"])
    
    # Health data
    if any(term in prompt.lower() for term in ["health", "insurance", "medical"]):
        variables.append(CENSUS_VARIABLES["with_health_insurance"])
        variables.append(CENSUS_VARIABLES["no_health_insurance"])
    
    # If no specific indicators were matched, provide a basic demographic profile
    if len(variables) == 1:  # Only NAME was added
        variables.extend([
            CENSUS_VARIABLES["population"],
            CENSUS_VARIABLES["median_age"],
            CENSUS_VARIABLES["median_household_income"],
            CENSUS_VARIABLES["poverty_all_people"]
        ])
    
    return variables

def parse_census_question(prompt: str) -> Dict[str, Any]:
    """Parse a natural language prompt to determine Census API parameters"""
    # Determine which dataset to use
    dataset = determine_dataset(prompt)
    
    # Determine which year to use
    year = determine_year(prompt)
    
    # Determine which geographic level to query
    predicates = parse_location(prompt)
    
    # Determine which variables to include
    variables = determine_variables(prompt)
    
    # Construct the full query parameters
    query_params = {
        "dataset": dataset,
        "year": year,
        "variables": variables,
        "predicates": predicates
    }
    
    return query_params

def query_census_api(dataset: str, year: str, variables: List[str], 
                     predicates: Dict[str, str] = None) -> List[List[str]]:
    """Query the Census API with the given parameters"""
    
    # Build the URL
    url = f"{BASE_URL}/{year}/{dataset}"
    
    # Prepare parameters
    params = {
        "get": ",".join(variables),
        "key": CENSUS_API_KEY,
    }
    
    # Add predicates (filters)
    if predicates:
        for key, value in predicates.items():
            params[key] = value
    
    # Make the request
    response = requests.get(url, params=params)
    
    # Check status
    if response.status_code != 200:
        raise Exception(f"Census API error: {response.status_code} - {response.text}")
    
    return response.json()

def format_census_data(result: List[List[str]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format census data for easier consumption by LLMs and applications.
    Converts from array format to structured objects with calculated metrics.
    """
    # Extract headers and data rows
    headers = result[0]
    data = result[1:]
    
    # Format as structured objects
    formatted_items = []
    for row in data:
        item = {headers[i]: value for i, value in enumerate(row)}
        formatted_items.append(item)
    
    # Extract variable mappings for readable labels
    variable_names = {}
    reverse_census_variables = {v: k for k, v in CENSUS_VARIABLES.items()}
    
    for variable in metadata["variables"]:
        if variable in reverse_census_variables:
            variable_names[variable] = reverse_census_variables[variable]
        else:
            variable_names[variable] = variable
    
    # Calculate summary statistics if we have multiple items
    summary = {}
    if len(formatted_items) > 0:
        for variable in metadata["variables"]:
            if variable == "NAME":
                continue
                
            # Try to calculate average, min, max for numeric variables
            try:
                values = [float(item[variable]) for item in formatted_items if variable in item and item[variable] not in ['-', 'null', None, '']]
                if values:
                    summary[variable] = {
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            except (ValueError, TypeError):
                # Skip non-numeric variables
                pass
    
    # Prepare the full context object
    formatted_data = {
        "items": formatted_items,
        "metadata": metadata,
        "variable_names": variable_names,
        "summary": summary,
        "record_count": len(formatted_items)
    }
    
    # Include additional calculated values for PolicyAide to use
    if len(formatted_items) > 0:
        calculated = {}
        
        # Calculate population density if we have population data
        pop_var = CENSUS_VARIABLES["population"]
        if pop_var in metadata["variables"]:
            calculated["total_population"] = sum([float(item[pop_var]) for item in formatted_items if pop_var in item and item[pop_var] not in ['-', 'null', None, '']])
        
        # Calculate percent in poverty if we have poverty and population data
        poverty_var = CENSUS_VARIABLES["poverty_all_people"]
        if pop_var in metadata["variables"] and poverty_var in metadata["variables"]:
            total_pop = calculated.get("total_population", 0)
            if total_pop > 0:
                total_poverty = sum([float(item[poverty_var]) for item in formatted_items if poverty_var in item and item[poverty_var] not in ['-', 'null', None, '']])
                calculated["poverty_percentage"] = (total_poverty / total_pop) * 100
        
        # Add the calculated values
        formatted_data["calculated"] = calculated
    
    return formatted_data

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP requests for Census data"""
    try:
        # Parse the prompt to determine what Census data to fetch
        query_params = parse_census_question(request.prompt)
        
        # Get additional parameters from the request if provided
        if "dataset" in request.params:
            query_params["dataset"] = request.params["dataset"]
        if "year" in request.params:
            query_params["year"] = request.params["year"]
        if "variables" in request.params:
            query_params["variables"] = request.params["variables"]
        if "predicates" in request.params:
            query_params["predicates"] = request.params["predicates"]
        
        # Query the Census API
        result = query_census_api(
            dataset=query_params["dataset"],
            year=query_params["year"],
            variables=query_params["variables"],
            predicates=query_params["predicates"]
        )
        
        # Format the results in a more structured way
        formatted_data = format_census_data(result, query_params)
        
        # Create the MCP response
        context_item = {
            "type": "census_data",
            "data": formatted_data,
            "source": f"US Census Bureau {query_params['dataset']} {query_params['year']}"
        }
        
        return MCPResponse(context=[context_item])
        
    except Exception as e:
        return MCPResponse(status="error", error=str(e), context=[])

@app.get("/")
async def root():
    """Health check and info endpoint"""
    return {
        "name": "Census Data MCP",
        "status": "online",
        "description": "MCP server for US Census Bureau data",
        "version": "0.2.0",
        "supported_datasets": list(DATASETS.keys()),
        "variable_categories": [
            "population", "demographics", "income", "poverty", 
            "education", "housing", "employment", "transportation",
            "health", "internet"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050) 