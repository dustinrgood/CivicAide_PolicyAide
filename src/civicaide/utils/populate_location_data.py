#!/usr/bin/env python
"""
Script to populate the location database with data from Census API.

This script fetches data for states, counties, and places from the Census API
and stores it in JSON files and a SQLite database for use in the CivicAide app.
"""

import os
import logging
import argparse
import traceback
from pathlib import Path

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure output goes to console
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import our module
import sys
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent
sys.path.insert(0, str(project_root))

# Print debugging information
logger.info(f"Script path: {script_path}")
logger.info(f"Project root: {project_root}")
logger.info(f"Python path: {sys.path}")

try:
    # First try direct relative import
    try:
        # Import our location data utilities using relative import
        from location_data import (
            ensure_data_directory,
            save_government_structures,
            fetch_states,
            fetch_counties,
            fetch_places,
            create_location_database,
            get_states_for_dropdown,
            get_counties_for_dropdown,
            get_places_for_dropdown,
            CENSUS_API_KEY,
            DATA_DIR
        )
        logger.info("Successfully imported modules using relative import")
    except ImportError:
        # Fall back to absolute import
        from src.civicaide.utils.location_data import (
            ensure_data_directory,
            save_government_structures,
            fetch_states,
            fetch_counties,
            fetch_places,
            create_location_database,
            get_states_for_dropdown,
            get_counties_for_dropdown,
            get_places_for_dropdown,
            CENSUS_API_KEY,
            DATA_DIR
        )
        logger.info("Successfully imported modules using absolute import")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def check_api_key():
    """Check if Census API key is set."""
    if not CENSUS_API_KEY:
        logger.warning("CENSUS_API_KEY environment variable is not set.")
        logger.warning("You can get a Census API key at: https://api.census.gov/data/key_signup.html")
        logger.warning("Set it using: export CENSUS_API_KEY=your_api_key")
        return False
    logger.info(f"Using Census API key: {CENSUS_API_KEY[:5]}...{CENSUS_API_KEY[-4:] if len(CENSUS_API_KEY) > 8 else ''}")
    return True

def populate_all_data():
    """Populate all location data."""
    logger.info("Starting data population process...")
    
    try:
        # Create data directory
        ensure_data_directory()
        logger.info(f"Data directory: {DATA_DIR}")
        
        # Save government structures
        save_government_structures()
        logger.info("Saved government structures data.")
    except Exception as e:
        logger.error(f"Error setting up data directory or government structures: {e}")
        logger.error(traceback.format_exc())
        return False
    
    # Check API key
    if not check_api_key():
        logger.error("Cannot continue without Census API key.")
        return False
    
    try:
        # Fetch states
        logger.info("Fetching states data...")
        states = fetch_states()
        logger.info(f"Fetched {len(states)} states.")
        
        # Fetch counties for all states
        logger.info("Fetching counties data...")
        counties = fetch_counties()
        logger.info(f"Fetched {len(counties)} counties.")
        
        # Fetch places for all states (can take a while)
        logger.info("Fetching places data (this may take a few minutes)...")
        places = fetch_places()
        logger.info(f"Fetched {len(places)} places.")
        
        # Create SQLite database
        logger.info("Creating SQLite database...")
        create_location_database()
        logger.info("Database creation complete.")
    except Exception as e:
        logger.error(f"Error fetching data from Census API: {e}")
        logger.error(traceback.format_exc())
        return False
    
    try:
        # Test dropdown data functions
        logger.info("Testing dropdown data functions...")
        
        # Get states for dropdown
        states_dropdown = get_states_for_dropdown()
        logger.info(f"Generated dropdown data for {len(states_dropdown)} states.")
        
        # Get counties for a sample state (California)
        california_fips = "06"  # California
        counties_dropdown = get_counties_for_dropdown(california_fips)
        logger.info(f"Generated dropdown data for {len(counties_dropdown)} counties in California.")
        
        # Get places for a sample state with search
        places_dropdown = get_places_for_dropdown(california_fips, "San")
        logger.info(f"Generated dropdown data for {len(places_dropdown)} places in California matching 'San'.")
    except Exception as e:
        logger.error(f"Error testing dropdown functions: {e}")
        logger.error(traceback.format_exc())
        return False
    
    logger.info("Data population complete!")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Populate location data for CivicAide app.")
    parser.add_argument("--force", action="store_true", help="Force re-download of all data")
    args = parser.parse_args()
    
    if args.force:
        # If force flag is set, remove existing data files
        try:
            # Try both import methods
            try:
                from location_data import (
                    STATES_CACHE_PATH, COUNTIES_CACHE_PATH, PLACES_CACHE_PATH,
                    LOCATION_DB_PATH, GOV_STRUCTURES_PATH, DATA_DIR
                )
            except ImportError:
                from src.civicaide.utils.location_data import (
                    STATES_CACHE_PATH, COUNTIES_CACHE_PATH, PLACES_CACHE_PATH,
                    LOCATION_DB_PATH, GOV_STRUCTURES_PATH, DATA_DIR
                )
            
            files_to_remove = [
                STATES_CACHE_PATH,
                COUNTIES_CACHE_PATH,
                PLACES_CACHE_PATH,
                LOCATION_DB_PATH,
                GOV_STRUCTURES_PATH
            ]
            
            for file_path in files_to_remove:
                if file_path.exists():
                    logger.info(f"Removing {file_path}")
                    file_path.unlink()
        except Exception as e:
            logger.error(f"Error removing existing data files: {e}")
            logger.error(traceback.format_exc())
    
    # Populate all data
    success = populate_all_data()
    
    if success:
        logger.info("Location data population completed successfully.")
        sys.exit(0)
    else:
        logger.error("Location data population failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 