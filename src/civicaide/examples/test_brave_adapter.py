#!/usr/bin/env python
"""
Test script for the Brave Search MCP adapter.

This script tests the Brave Search MCP adapter by fetching news, elected officials, 
and local business information for Elgin, Illinois.

Requirements:
    - Brave Search MCP server running on port 8051
    - Brave API key set as BRAVE_API_KEY environment variable
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the adapter
from src.civicaide.brave_search_adapter import BraveSearchMCPAdapter

class LocationInfo:
    def __init__(self, city, state, county=None):
        self.city = city
        self.state = state
        self.county = county

def main():
    """Test the Brave Search MCP adapter with Elgin, Illinois."""
    print("Testing Brave Search MCP adapter for Elgin, Illinois...\n")
    
    # Create the test location
    location = LocationInfo(city="Elgin", state="Illinois", county="Kane")
    
    # Initialize the adapter
    try:
        print("Initializing Brave Search MCP adapter...")
        adapter = BraveSearchMCPAdapter(mcp_url="http://localhost:8051")
        
        if not adapter.client:
            print("❌ Failed to connect to Brave Search MCP server.")
            print("   Make sure it's running on port 8051 and BRAVE_API_KEY is set.")
            return
        
        print("✅ Successfully connected to Brave Search MCP server.\n")
        
        # Test getting news
        print("Fetching news for Elgin, Illinois...")
        news = adapter.get_local_news(location, count=3)
        
        if news:
            print(f"✅ Successfully retrieved {len(news)} news articles:")
            for i, item in enumerate(news, 1):
                print(f"  {i}. {item['title']}")
                print(f"     Source: {item['source']}")
                print(f"     URL: {item['url']}")
                print(f"     Summary: {item['summary'][:100]}...")
        else:
            print("❌ No news articles found.")
        
        print("\n" + "-" * 50 + "\n")
        
        # Test getting elected officials
        print("Fetching elected officials for Elgin, Illinois...")
        officials = adapter.get_elected_officials(location)
        
        if officials:
            print(f"✅ Successfully retrieved {len(officials)} elected officials:")
            for i, official in enumerate(officials, 1):
                print(f"  {i}. {official['title']}: {official['name']} ({official['term']})")
                if 'source' in official:
                    print(f"     Source: {official['source']}")
        else:
            print("❌ No elected officials found.")
        
        print("\n" + "-" * 50 + "\n")
        
        # Test getting local businesses
        print("Fetching top restaurants in Elgin, Illinois...")
        restaurants = adapter.get_local_businesses(location, "restaurants", count=3)
        
        if restaurants:
            print(f"✅ Successfully retrieved {len(restaurants)} restaurants:")
            for i, business in enumerate(restaurants, 1):
                print(f"  {i}. {business['name']}")
                print(f"     Address: {business['address']}")
                print(f"     Rating: {business['rating']}")
        else:
            print("❌ No restaurants found.")
        
    except ConnectionRefusedError:
        print("❌ Connection refused when connecting to Brave Search MCP at http://localhost:8051")
        print("   Please ensure the server is running with:")
        print("   1. $env:BRAVE_API_KEY = 'your-api-key'")
        print("   2. $env:PORT = 8051")
        print("   3. npx @modelcontextprotocol/server-brave-search")
    except Exception as e:
        print(f"❌ Error testing Brave Search MCP adapter: {str(e)}")

if __name__ == "__main__":
    main() 