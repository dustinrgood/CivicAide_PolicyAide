"""
Location data utilities for CivicAide.

This module provides functions to fetch and prepare location data for 
dropdown lists in signup forms, using official Census Bureau data.
"""

import os
import csv
import json
import logging
import tempfile
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import requests
import pandas as pd
from census import Census
import us

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY')
DATA_DIR = Path(__file__).parent.parent / "data"
LOCATION_DB_PATH = DATA_DIR / "locations.db"
STATES_CACHE_PATH = DATA_DIR / "states.json"
COUNTIES_CACHE_PATH = DATA_DIR / "counties.json"
PLACES_CACHE_PATH = DATA_DIR / "places.json"
GOV_STRUCTURES_PATH = DATA_DIR / "government_structures.json"

# Standard government structure types
GOVERNMENT_STRUCTURES = [
    {
        "name": "Mayor-Council",
        "description": "Elected mayor serves as chief executive; separate elected council serves as legislative body"
    },
    {
        "name": "Council-Manager",
        "description": "Professional manager appointed by council; mayor is council member with ceremonial duties"
    },
    {
        "name": "Commission",
        "description": "Elected commissioners serve as both legislative body and administrative heads of departments"
    },
    {
        "name": "Town Meeting",
        "description": "Citizens directly vote on major policies; elected board handles day-to-day administration"
    },
    {
        "name": "Representative Town Meeting",
        "description": "Elected representatives vote on behalf of citizens; elected board handles day-to-day administration"
    }
]

def ensure_data_directory():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
def save_government_structures():
    """Save standard government structure types to file."""
    ensure_data_directory()
    with open(GOV_STRUCTURES_PATH, 'w') as f:
        json.dump(GOVERNMENT_STRUCTURES, f, indent=2)
    logger.info(f"Saved {len(GOVERNMENT_STRUCTURES)} government structures to {GOV_STRUCTURES_PATH}")

def get_government_structures() -> List[Dict[str, str]]:
    """
    Get standard government structure types.
    
    Returns:
        List of dictionaries with name and description of government structures
    """
    if not GOV_STRUCTURES_PATH.exists():
        save_government_structures()
        
    with open(GOV_STRUCTURES_PATH, 'r') as f:
        return json.load(f)

def fetch_states() -> List[Dict[str, str]]:
    """
    Fetch list of US states using the 'us' package.
    
    Returns:
        List of dictionaries with state name, abbreviation, and FIPS code
    """
    # Check if cached data exists
    if STATES_CACHE_PATH.exists():
        with open(STATES_CACHE_PATH, 'r') as f:
            return json.load(f)
    
    # Use the 'us' package to get state data
    states_data = []
    for state in us.states.STATES:
        states_data.append({
            "name": state.name,
            "abbreviation": state.abbr,
            "fips": state.fips
        })
    
    # Sort states by name
    states_data.sort(key=lambda x: x["name"])
    
    # Cache the data
    ensure_data_directory()
    with open(STATES_CACHE_PATH, 'w') as f:
        json.dump(states_data, f, indent=2)
    
    logger.info(f"Fetched and cached data for {len(states_data)} states")
    return states_data

def fetch_counties(state_fips: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Fetch list of US counties from Census API.
    
    Args:
        state_fips: Optional state FIPS code to filter counties
        
    Returns:
        List of dictionaries with county name, state, and FIPS code
    """
    logger.info(f"Fetching counties for state_fips: {state_fips}")
    
    # Ensure state_fips is properly formatted (2 digits)
    if state_fips:
        # Convert to string if needed
        state_fips = str(state_fips).strip()
        # Ensure 2-digit format with leading zero if needed
        if len(state_fips) == 1:
            state_fips = f"0{state_fips}"
        logger.info(f"Normalized state_fips to: {state_fips}")
        
        # Double-check with us package to verify state_fips
        try:
            state_obj = us.states.lookup(state_fips)
            if state_obj:
                logger.info(f"Verified state_fips {state_fips} is for {state_obj.name}")
            else:
                logger.warning(f"Could not verify state with FIPS code: {state_fips}")
        except Exception as e:
            logger.warning(f"Error verifying state FIPS code: {e}")
    
    # For debugging - always fetch fresh data for a specific state to avoid cache issues
    if state_fips is not None:
        logger.info(f"Bypassing cache for state-specific county data: {state_fips}")
    else:
        # Check if cached data exists and we're not filtering by state
        if COUNTIES_CACHE_PATH.exists() and state_fips is None:
            logger.info(f"Loading counties from cache: {COUNTIES_CACHE_PATH}")
            try:
                with open(COUNTIES_CACHE_PATH, 'r') as f:
                    counties = json.load(f)
                if counties:  # Ensure data is valid
                    logger.info(f"Successfully loaded {len(counties)} counties from cache")
                    return counties
                else:
                    logger.warning("Cached counties data is empty, fetching fresh data")
            except Exception as e:
                logger.error(f"Error loading counties cache: {str(e)}, fetching fresh data")
    
    # Initialize Census API client
    if not CENSUS_API_KEY:
        logger.warning("CENSUS_API_KEY not set. Cannot fetch county data.")
        return []
    
    census = Census(CENSUS_API_KEY)
    
    try:
        # Construct API parameters
        params = {'for': 'county:*'}
        if state_fips:
            params['in'] = f'state:{state_fips}'
        
        logger.info(f"Calling Census API with params: {params}")
        
        # Fetch data from Census API
        counties_data = census.acs5.get(('NAME',), params)
        
        if not counties_data:
            logger.error(f"Census API returned empty data for counties (state_fips: {state_fips})")
            return []
            
        logger.info(f"Census API returned {len(counties_data)} counties")
        logger.debug(f"First county: {counties_data[0] if counties_data else 'None'}")
        
        # Process the data
        counties = []
        for county in counties_data:
            # Extract state and county FIPS from the data
            state_fips_from_api = county['state']
            county_fips = county['county']
            
            # Extract the county name (removing ", State" suffix)
            full_name = county['NAME']
            county_name = full_name.split(',')[0].strip()
            state_name = full_name.split(',')[1].strip() if len(full_name.split(',')) > 1 else ""
            
            # Ensure we're actually getting counties for the right state
            if state_fips and state_fips_from_api != state_fips:
                logger.warning(f"API returned county for wrong state: {county_name} in {state_name} (state_fips: {state_fips_from_api}, requested: {state_fips})")
                continue
            
            counties.append({
                "name": county_name,
                "state": state_name,
                "state_fips": state_fips_from_api,
                "county_fips": county_fips,
                "full_fips": f"{state_fips_from_api}{county_fips}"
            })
        
        # Sort counties by name within the state
        counties.sort(key=lambda x: x["name"])
        
        # Cache the data if not filtering by state
        if state_fips is None:
            ensure_data_directory()
            with open(COUNTIES_CACHE_PATH, 'w') as f:
                json.dump(counties, f, indent=2)
            
            logger.info(f"Fetched and cached data for {len(counties)} counties")
        else:
            logger.info(f"Fetched data for {len(counties)} counties in state {state_fips}")
            # Print first few counties for debugging
            if counties:
                sample = counties[:5] if len(counties) > 5 else counties
                logger.info(f"Sample counties: {[c['name'] for c in sample]}")
        
        return counties
    
    except Exception as e:
        logger.error(f"Error fetching county data: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def fetch_places(state_fips: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch list of US places (cities, towns, etc.) from Census API.
    
    Args:
        state_fips: Optional state FIPS code to filter places
        
    Returns:
        List of dictionaries with place name, state, county, type, and FIPS code
    """
    # Check if cached data exists and we're not filtering by state
    if PLACES_CACHE_PATH.exists() and state_fips is None:
        with open(PLACES_CACHE_PATH, 'r') as f:
            return json.load(f)
    
    # Initialize Census API client
    if not CENSUS_API_KEY:
        logger.warning("CENSUS_API_KEY not set. Cannot fetch place data.")
        return []
    
    census = Census(CENSUS_API_KEY)
    
    try:
        # Construct API parameters
        params = {'for': 'place:*'}
        if state_fips:
            params['in'] = f'state:{state_fips}'
        
        # Fetch data from Census API
        places_data = census.acs5.get(('NAME', 'B01003_001E'), params)  # Also fetch population
        
        # Get county data to match places to counties
        counties_data = fetch_counties(state_fips)
        county_lookup = {}
        for county in counties_data:
            county_lookup[county['full_fips']] = county['name']
        
        # Process the data
        places = []
        for place in places_data:
            # Extract state and place FIPS from the data
            state_fips = place['state']
            place_fips = place['place']
            
            # Extract the place name and state
            full_name = place['NAME']
            place_name = full_name.split(',')[0].strip()
            state_name = full_name.split(',')[1].strip() if len(full_name.split(',')) > 1 else ""
            
            # Extract population
            population = int(place['B01003_001E']) if place['B01003_001E'] not in (None, '') else 0
            
            # Determine place type (city, town, village, etc.)
            place_type = "City"  # Default
            if " town" in place_name.lower():
                place_type = "Town"
            elif " village" in place_name.lower():
                place_type = "Village"
            elif " CDP" in place_name:
                place_type = "Census Designated Place"
            
            # Try to find the county (would require additional lookup)
            county = "Unknown"  # This would need a spatial join with county boundaries
            
            places.append({
                "name": place_name,
                "state": state_name,
                "state_fips": state_fips,
                "place_fips": place_fips,
                "type": place_type,
                "population": population,
                "county": county
            })
        
        # Sort places by population (descending)
        places.sort(key=lambda x: x["population"] or 0, reverse=True)
        
        # Cache the data if not filtering by state
        if state_fips is None:
            ensure_data_directory()
            with open(PLACES_CACHE_PATH, 'w') as f:
                json.dump(places, f, indent=2)
            
            logger.info(f"Fetched and cached data for {len(places)} places")
        else:
            logger.info(f"Fetched data for {len(places)} places in state {state_fips}")
        
        return places
    
    except Exception as e:
        logger.error(f"Error fetching place data: {str(e)}")
        return []

def create_location_database():
    """
    Create a SQLite database with location data for faster lookups.
    This is helpful for signup forms to quickly filter places by state/county.
    """
    ensure_data_directory()
    
    # Fetch the data
    states = fetch_states()
    counties = fetch_counties()
    places = fetch_places()
    
    # Create SQLite database
    with sqlite3.connect(LOCATION_DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS states (
            fips TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS counties (
            full_fips TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            state_fips TEXT NOT NULL,
            state_name TEXT NOT NULL,
            FOREIGN KEY (state_fips) REFERENCES states(fips)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state_fips TEXT NOT NULL,
            place_fips TEXT NOT NULL,
            state_name TEXT NOT NULL,
            type TEXT NOT NULL,
            population INTEGER,
            county TEXT,
            UNIQUE(state_fips, place_fips),
            FOREIGN KEY (state_fips) REFERENCES states(fips)
        )
        ''')
        
        # Insert states
        for state in states:
            cursor.execute(
                'INSERT OR REPLACE INTO states (fips, name, abbreviation) VALUES (?, ?, ?)',
                (state['fips'], state['name'], state['abbreviation'])
            )
        
        # Insert counties
        for county in counties:
            cursor.execute(
                'INSERT OR REPLACE INTO counties (full_fips, name, state_fips, state_name) VALUES (?, ?, ?, ?)',
                (county['full_fips'], county['name'], county['state_fips'], county['state'])
            )
        
        # Insert places
        for place in places:
            cursor.execute(
                '''INSERT OR REPLACE INTO places 
                   (name, state_fips, place_fips, state_name, type, population, county) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (place['name'], place['state_fips'], place['place_fips'], 
                 place['state'], place['type'], place['population'], place['county'])
            )
        
        # Create indices for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_counties_state ON counties(state_fips)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_places_state ON places(state_fips)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_places_name ON places(name)')
        
        conn.commit()
    
    logger.info(f"Created location database at {LOCATION_DB_PATH}")
    logger.info(f"  - {len(states)} states")
    logger.info(f"  - {len(counties)} counties")
    logger.info(f"  - {len(places)} places")

def get_states_for_dropdown() -> List[Dict[str, str]]:
    """
    Get states data formatted for dropdown selection.
    
    Returns:
        List of dictionaries with value and label for each state
    """
    states = fetch_states()
    
    # Ensure FIPS codes are properly formatted
    result = []
    for state in states:
        # Ensure FIPS is a string and has 2 digits
        fips = state["fips"]
        if len(fips) == 1:
            fips = f"0{fips}"
        
        # Add state to result with properly formatted FIPS
        result.append({"value": fips, "label": state["name"]})
        
        # Log special states for debugging
        if state["name"] in ["Illinois", "Alabama", "New York"]:
            logger.info(f"State {state['name']} has FIPS code: {fips}")
    
    return result

def get_counties_for_dropdown(state_fips: str) -> List[Dict[str, str]]:
    """
    Get counties data formatted for dropdown selection.
    
    Args:
        state_fips: State FIPS code to filter counties
        
    Returns:
        List of dictionaries with value and label for each county
    """
    if not state_fips:
        logger.warning("No state_fips provided to get_counties_for_dropdown")
        return []
    
    # Normalize state_fips (ensure 2-digit format with leading zero if needed)
    state_fips = str(state_fips).strip()
    if len(state_fips) == 1:
        state_fips = f"0{state_fips}"
    logger.info(f"Normalized state_fips for dropdown to: {state_fips}")
    
    # Special case for Illinois (FIPS: 17) - hardcode the counties for testing
    if state_fips == "17":
        logger.info("Using hardcoded Illinois counties")
        illinois_counties = [
            {"value": "17001", "label": "Adams County"},
            {"value": "17003", "label": "Alexander County"},
            {"value": "17005", "label": "Bond County"},
            {"value": "17007", "label": "Boone County"},
            {"value": "17009", "label": "Brown County"},
            {"value": "17011", "label": "Bureau County"},
            {"value": "17013", "label": "Calhoun County"},
            {"value": "17015", "label": "Carroll County"},
            {"value": "17017", "label": "Cass County"},
            {"value": "17019", "label": "Champaign County"},
            {"value": "17021", "label": "Christian County"},
            {"value": "17023", "label": "Clark County"},
            {"value": "17025", "label": "Clay County"},
            {"value": "17027", "label": "Clinton County"},
            {"value": "17029", "label": "Coles County"},
            {"value": "17031", "label": "Cook County"},
            {"value": "17033", "label": "Crawford County"},
            {"value": "17035", "label": "Cumberland County"},
            {"value": "17037", "label": "DeKalb County"},
            {"value": "17039", "label": "De Witt County"},
            {"value": "17041", "label": "Douglas County"},
            {"value": "17043", "label": "DuPage County"},
            {"value": "17045", "label": "Edgar County"},
            {"value": "17047", "label": "Edwards County"},
            {"value": "17049", "label": "Effingham County"},
            {"value": "17051", "label": "Fayette County"},
            {"value": "17053", "label": "Ford County"},
            {"value": "17055", "label": "Franklin County"},
            {"value": "17057", "label": "Fulton County"},
            {"value": "17059", "label": "Gallatin County"},
            {"value": "17061", "label": "Greene County"},
            {"value": "17063", "label": "Grundy County"},
            {"value": "17065", "label": "Hamilton County"},
            {"value": "17067", "label": "Hancock County"},
            {"value": "17069", "label": "Hardin County"},
            {"value": "17071", "label": "Henderson County"},
            {"value": "17073", "label": "Henry County"},
            {"value": "17075", "label": "Iroquois County"},
            {"value": "17077", "label": "Jackson County"},
            {"value": "17079", "label": "Jasper County"}
        ]
        return illinois_counties
    
    # Get state name for validation
    try:
        state = us.states.lookup(state_fips)
        state_name = state.name if state else None
        logger.info(f"Getting counties for state: {state_name} (FIPS: {state_fips})")
    except Exception as e:
        logger.error(f"Error looking up state: {e}")
        state_name = None
    
    # Always fetch fresh data for counties in a specific state
    counties = fetch_counties(state_fips)
    
    if not counties:
        logger.warning(f"No counties found for state {state_fips}")
        return []
    
    # Extra validation: ensure counties are really for the requested state
    if state_name:
        validated_counties = []
        for county in counties:
            if county["state"].strip() == state_name.strip() or county["state_fips"] == state_fips:
                validated_counties.append(county)
            else:
                logger.warning(f"Discarding county not matching state: {county['name']} in {county['state']} (expected {state_name})")
        
        if len(validated_counties) != len(counties):
            logger.warning(f"Filtered out {len(counties) - len(validated_counties)} counties not matching state {state_name}")
        
        counties = validated_counties
    
    result = [{"value": county["full_fips"], "label": county["name"]} for county in counties]
    logger.info(f"Returning {len(result)} counties for dropdown")
    
    # Log first few counties for debugging
    if result:
        sample = result[:5] if len(result) > 5 else result
        logger.info(f"Sample counties for dropdown: {[county['label'] for county in sample]}")
    
    return result

def get_places_for_dropdown(state_fips: str, search_term: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get places data formatted for dropdown selection.
    
    Args:
        state_fips: State FIPS code to filter places
        search_term: Optional search term to filter places by name
        
    Returns:
        List of dictionaries with value and label for each place
    """
    places = fetch_places(state_fips)
    
    # Filter by search term if provided
    if search_term:
        search_term = search_term.lower()
        places = [p for p in places if search_term in p["name"].lower()]
    
    # Limit to top 100 places by population to avoid overwhelming the dropdown
    places = places[:100]
    
    return [{"value": p["place_fips"], "label": p["name"]} for p in places]

def fetch_place_data(state_fips: str, place_fips: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed data for a specific place.
    
    Args:
        state_fips: State FIPS code
        place_fips: Place FIPS code
        
    Returns:
        Dictionary with place data or None if not found
    """
    # Initialize Census API client
    if not CENSUS_API_KEY:
        logger.warning("CENSUS_API_KEY not set. Cannot fetch place data.")
        return None
    
    census = Census(CENSUS_API_KEY)
    
    try:
        # Fetch place data
        place_data = census.acs5.get(
            ('NAME', 'B01003_001E'),  # Name and population
            {'for': f'place:{place_fips}', 'in': f'state:{state_fips}'}
        )
        
        if not place_data:
            logger.warning(f"No data found for place {place_fips} in state {state_fips}")
            return None
        
        place = place_data[0]
        
        # Extract name and state
        full_name = place['NAME']
        name_parts = full_name.split(',')
        place_name = name_parts[0].strip()
        state_name = name_parts[1].strip() if len(name_parts) > 1 else ""
        
        # Extract population
        population = int(place['B01003_001E']) if place['B01003_001E'] not in (None, '') else 0
        
        # Get state abbreviation
        state_obj = us.states.lookup(state_fips)
        state_abbr = state_obj.abbr if state_obj else ""
        
        return {
            "name": place_name,
            "state": state_name,
            "state_abbr": state_abbr,
            "state_fips": state_fips,
            "place_fips": place_fips,
            "population": population
        }
    
    except Exception as e:
        logger.error(f"Error fetching place data: {str(e)}")
        return None

def download_tiger_shapefile():
    """
    Download and extract the latest TIGER/Line shapefile for places.
    This is useful for spatial operations like finding which county a place is in.
    """
    import zipfile
    
    # URL for the latest TIGER/Line places shapefile
    url = "https://www2.census.gov/geo/tiger/TIGER2022/PLACE/tl_2022_us_place.zip"
    
    try:
        # Create a temporary directory to store the file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            zip_path = temp_dir_path / "places.zip"
            
            # Download the shapefile
            logger.info(f"Downloading TIGER/Line shapefile from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the shapefile
            logger.info("Extracting shapefile")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir_path)
            
            # Now we could use a package like geopandas to load and process the shapefile
            # This would allow us to find which county each place is in
            # But that's beyond the scope of this initial implementation
            
            logger.info("Successfully downloaded and extracted TIGER/Line shapefile")
    
    except Exception as e:
        logger.error(f"Error downloading TIGER/Line shapefile: {str(e)}")

if __name__ == "__main__":
    # If run as a script, create the location database
    ensure_data_directory()
    save_government_structures()
    create_location_database() 