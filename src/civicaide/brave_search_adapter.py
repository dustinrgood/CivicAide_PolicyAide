#!/usr/bin/env python
"""
PolicyAide Adapter for Brave Search MCP

This adapter provides an interface to the Brave Search MCP server for fetching
news, local information, and other data that can be used in place of web scraping.

This adapter can be used to enhance the context gathering pipeline with real-time
information from web searches.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for Brave API key
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
if not BRAVE_API_KEY:
    logger.warning("BRAVE_API_KEY environment variable is not set. Brave Search functionality will be limited.")

class BraveSearchMCPAdapter:
    """
    Adapter class that provides an interface to the Brave Search MCP server
    for fetching news, local information, and other data.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:8051", api_key: str = None):
        """Initialize the adapter with the URL to the Brave Search MCP server."""
        self.mcp_url = mcp_url
        self.client = None  # We'll use this to maintain compatibility with other adapters
        self.api_key = api_key or BRAVE_API_KEY
        
        # Set environment variable if provided in constructor
        if self.api_key and os.getenv("BRAVE_API_KEY") != self.api_key:
            os.environ["BRAVE_API_KEY"] = self.api_key
            logger.info("Set BRAVE_API_KEY environment variable from constructor parameter")
        
        # Test connection to MCP
        try:
            response = requests.get(mcp_url)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Brave Search MCP at {mcp_url}")
                self.server_info = response.json()
                logger.info(f"MCP Server Info: {self.server_info}")
                # Set this to True to indicate that the "client" is available
                self.client = True
            else:
                logger.warning(f"Brave Search MCP returned status code {response.status_code}")
                self.server_info = {}
        except Exception as e:
            logger.error(f"Failed to connect to Brave Search MCP: {str(e)}")
            raise ConnectionError(f"Cannot connect to Brave Search MCP at {mcp_url}. Is the server running?")
    
    def query_mcp(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query the Brave Search MCP with a specific tool and parameters.
        
        Args:
            tool_name: The name of the tool to call (e.g., 'brave_web_search', 'brave_local_search')
            params: Parameters for the tool
            
        Returns:
            Dictionary containing the MCP response
        """
        if params is None:
            params = {}
            
        payload = {
            "mcp_version": "0.1.0",
            "tool_calls": [
                {
                    "id": f"{tool_name}-{datetime.now().timestamp()}",
                    "name": tool_name,
                    "parameters": params
                }
            ]
        }
        
        try:
            response = requests.post(f"{self.mcp_url}/tools/execute", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Brave Search MCP error: {response.status_code} - {response.text}")
                raise Exception(f"Brave Search MCP returned error status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error querying Brave Search MCP: {str(e)}")
            raise
    
    def get_local_news(self, location_info, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get news articles related to a location.
        
        Args:
            location_info: Object with location details (city, state, county)
            count: Number of news articles to retrieve (default: 5)
            
        Returns:
            List of news articles with title, source, date, and summary
        """
        # Extract location information
        city = getattr(location_info, "city", None)
        state = getattr(location_info, "state", None)
        county = getattr(location_info, "county", None)
        
        if not city and not state:
            logger.error("Missing required location information: city or state")
            return []
            
        # Construct the query
        if city and state:
            query = f"latest news {city} {state}"
        elif city:
            query = f"latest news {city}"
        else:
            query = f"latest news {state}"
            
        if county:
            query += f" {county} county"
            
        try:
            # Use the brave_web_search tool to get news results
            response = self.query_mcp("brave_web_search", {
                "query": query,
                "count": count
            })
            
            # Process the response
            results = []
            
            # Extract the search results
            if 'result' in response:
                for item in response['result'].get('web', {}).get('results', []):
                    # Extract relevant information from each search result
                    result = {
                        "title": item.get('title', ''),
                        "source": item.get('source', ''),
                        "date": item.get('published', ''),
                        "summary": item.get('description', ''),
                        "url": item.get('url', '')
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting news from Brave Search MCP: {str(e)}")
            return []
    
    def get_elected_officials(self, location_info) -> List[Dict[str, Any]]:
        """
        Get information about elected officials for a location.
        
        Args:
            location_info: Object with location details (city, state, county)
            
        Returns:
            List of elected officials with title, name, and other details
        """
        # Extract location information
        city = getattr(location_info, "city", None)
        state = getattr(location_info, "state", None)
        
        if not city or not state:
            logger.error("Missing required location information: city and state")
            return []
            
        # Construct the query to find elected officials
        query = f"elected officials {city} {state} mayor city council"
            
        try:
            # Use the brave_web_search tool to get information
            response = self.query_mcp("brave_web_search", {
                "query": query,
                "count": 10
            })
            
            # Extract relevant information about officials
            officials = []
            
            # This would require more sophisticated parsing in a real implementation
            # For now, we'll just extract what we can from the search results
            if 'result' in response:
                # First pass - try to identify the city's government website
                govt_site = None
                for item in response['result'].get('web', {}).get('results', []):
                    url = item.get('url', '').lower()
                    title = item.get('title', '').lower()
                    if ('cityof' in url.replace(' ', '') or 'ci.' in url or '.gov' in url) and city.lower() in url:
                        govt_site = url
                        break
                    elif ('elected officials' in title or 'city council' in title or 'mayor' in title) and city.lower() in title:
                        govt_site = url
                        break
                
                # Second pass - extract officials from description text
                for item in response['result'].get('web', {}).get('results', []):
                    description = item.get('description', '').lower()
                    
                    # Look for patterns like "Mayor [Name]" or "[Name], Mayor"
                    if 'mayor' in description:
                        # Very simplified extraction - in a real implementation, you'd use NER or more robust parsing
                        parts = description.split('mayor')
                        if len(parts) > 1:
                            name_part = parts[1].strip()
                            if name_part.startswith(' '):
                                # Pattern: "Mayor [Name]"
                                name = name_part.split('.')[0].strip().title()
                                officials.append({
                                    "title": "Mayor",
                                    "name": name,
                                    "term": "Current",
                                    "source": item.get('url', '')
                                })
                    
                    # Look for council members
                    if 'council member' in description or 'councilmember' in description:
                        # Simplified extraction
                        officials.append({
                            "title": "City Council Member",
                            "name": "Found reference to council members",
                            "term": "Current",
                            "source": item.get('url', '')
                        })
            
            # If we couldn't extract specific officials, add a placeholder with the source
            if len(officials) == 0 and govt_site:
                officials.append({
                    "title": "Mayor of " + city,
                    "name": "Current",
                    "term": "Current",
                    "source": govt_site
                })
            
            return officials
            
        except Exception as e:
            logger.error(f"Error getting elected officials from Brave Search MCP: {str(e)}")
            return []
    
    def get_local_businesses(self, location_info, category: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get information about local businesses in a specific category.
        
        Args:
            location_info: Object with location details (city, state, county)
            category: Business category (e.g., 'restaurants', 'hotels', etc.)
            count: Number of businesses to retrieve (default: 5)
            
        Returns:
            List of businesses with name, address, and other details
        """
        # Extract location information
        city = getattr(location_info, "city", None)
        state = getattr(location_info, "state", None)
        
        if not city or not state:
            logger.error("Missing required location information: city and state")
            return []
            
        # Construct the query
        query = f"{category} in {city}, {state}"
            
        try:
            # Use the brave_local_search tool to get local business results
            response = self.query_mcp("brave_local_search", {
                "query": query,
                "count": count
            })
            
            # Process the response to extract business information
            businesses = []
            
            # Extract the local search results
            if 'result' in response:
                for item in response['result'].get('local', {}).get('results', []):
                    # Extract relevant information from each search result
                    business = {
                        "name": item.get('title', ''),
                        "address": item.get('address', ''),
                        "phone": item.get('phone', ''),
                        "rating": item.get('rating', None),
                        "url": item.get('url', '')
                    }
                    businesses.append(business)
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error getting local businesses from Brave Search MCP: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    # Import or define LocationInfo
    class LocationInfo:
        def __init__(self, city, state, county=None):
            self.city = city
            self.state = state
            self.county = county
    
    # Create a test location
    test_location = LocationInfo(city="Elgin", state="Illinois", county="Kane")
    
    # Initialize the adapter
    print("Initializing Brave Search MCP Adapter...")
    adapter = BraveSearchMCPAdapter()
    
    if adapter.client:
        # Test getting local news
        print("\nFetching news for Elgin, Illinois:")
        news = adapter.get_local_news(test_location, count=3)
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   Source: {item['source']}")
            print(f"   Date: {item['date']}")
            print(f"   Summary: {item['summary'][:100]}...")
        
        # Test getting elected officials
        print("\nFetching elected officials for Elgin, Illinois:")
        officials = adapter.get_elected_officials(test_location)
        for i, official in enumerate(officials, 1):
            print(f"{i}. {official['title']}: {official['name']} ({official['term']})")
        
        # Test getting local businesses
        print("\nFetching top restaurants in Elgin, Illinois:")
        restaurants = adapter.get_local_businesses(test_location, "restaurants", count=3)
        for i, business in enumerate(restaurants, 1):
            print(f"{i}. {business['name']}")
            print(f"   Address: {business['address']}")
            print(f"   Rating: {business['rating']}")
    else:
        print("Failed to connect to Brave Search MCP. Please make sure it's running at the specified URL.") 