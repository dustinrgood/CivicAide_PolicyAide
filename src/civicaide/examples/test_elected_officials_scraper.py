#!/usr/bin/env python
"""
Test script for the elected officials scraper.

This script demonstrates how to use the fetch_elected_officials function
to retrieve elected officials data from official government websites.
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
import dotenv

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

# Import the LocationInfo and fetch_elected_officials function
from src.civicaide.agents.context_agents import LocationInfo, fetch_elected_officials

async def test_scraper(city: str, state: str):
    """Test the elected officials scraper for a specific city."""
    print(f"\n=== Testing Elected Officials Scraper for {city}, {state} ===\n")
    
    # Create a LocationInfo object
    location = LocationInfo(
        city=city,
        state=state,
        county="Unknown",
        country="USA"
    )
    
    try:
        # Fetch elected officials data
        officials = await fetch_elected_officials(location)
        
        # Display the results
        if officials:
            print(f"Successfully retrieved {len(officials)} elected officials:")
            for i, official in enumerate(officials, 1):
                print(f"{i}. {official['title']}: {official['name']} ({official.get('term', 'Current')})")
        else:
            print(f"No elected officials found for {city}, {state}")
        
        # Save the results to a JSON file
        output_dir = Path(__file__).parent / "scraped_data"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        output_file = output_dir / f"{city.lower()}_{state.lower()}_officials.json"
        with open(output_file, 'w') as f:
            json.dump(officials, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
    
    except Exception as e:
        print(f"Error testing scraper: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run tests for several cities."""
    # List of cities to test
    test_cities = [
        ("Austin", "Texas"),
        ("New York", "New York"),
        ("Chicago", "Illinois"),
        ("Los Angeles", "California"),
        ("Seattle", "Washington")
    ]
    
    # Test each city
    for city, state in test_cities:
        await test_scraper(city, state)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    # Create the output directory if it doesn't exist
    output_dir = Path(__file__).parent / "scraped_data"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Run the tests
    asyncio.run(main()) 