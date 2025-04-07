#!/usr/bin/env python
"""
Test WebSearchTool Fix

This script tests whether the fix for WebSearchTool.search works.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.civicaide.agents.utils import execute_web_searches

async def test_web_search():
    """Test the web search functionality."""
    print("Testing web search...")
    
    # Define some test queries
    queries = [
        "population of Austin, Texas",
        "major industries in Austin, Texas",
        "government of Austin, Texas"
    ]
    
    # Execute the searches
    results = await execute_web_searches(queries)
    
    # Print the results
    print("\nSearch Results:")
    for query, result in results.items():
        print(f"\nQuery: {query}")
        print(f"Result: {result[:200]}...")  # Print just the first 200 chars

if __name__ == "__main__":
    asyncio.run(test_web_search()) 