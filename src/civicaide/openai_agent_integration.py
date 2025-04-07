#!/usr/bin/env python
"""
Integration of Census MCP with OpenAI's Agent SDK

This script demonstrates how to integrate the Census MCP server with OpenAI's Agent SDK.
It allows PolicyAide to leverage both the Census MCP and OpenAI's Agent for policy research.

Requirements:
    - openai-agents-python: OpenAI's Agent SDK (pip install openai-agents-python)
    - openai: OpenAI Python client (pip install openai)
    - requests: For API calls (pip install requests)
    - dotenv: For environment variables (pip install python-dotenv)
"""

import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Import OpenAI Agent SDK
try:
    from openai import OpenAI
    from openai.agents import Agent
    from openai.agents.clients import MCP
    from openai.agents.transports import MCPServerSse, MCPServerStdio
except ImportError:
    print("Error: OpenAI Agent SDK not installed.")
    print("Please install it with: pip install openai-agents-python")
    exit(1)

# Load environment variables
load_dotenv()

# Check for required API keys
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not found.")
    print("Please add it to your .env file or set it in your environment.")
    exit(1)

class CensusMCPWrapper:
    """
    A wrapper class for connecting to our Census MCP server using OpenAI's Agent SDK.
    This class converts our HTTP-based MCP server to a format compatible with the OpenAI Agent SDK.
    """
    
    def __init__(self, mcp_url="http://localhost:8050"):
        """Initialize the MCP wrapper with the URL to our Census MCP server."""
        self.mcp_url = mcp_url
        self._tools_list = None
    
    async def get_tools_list(self):
        """
        Get a list of tools from our MCP server, formatted for the OpenAI Agent SDK.
        
        Since our MCP server doesn't directly provide a "tools" endpoint like standard MCP servers,
        we'll manually define the tool schema that represents our Census data capabilities.
        """
        if self._tools_list is not None:
            return self._tools_list
            
        # Define the Census query tool that matches our MCP server's capabilities
        self._tools_list = {
            "tools": [
                {
                    "name": "census_data",
                    "description": "Get demographic, economic, and housing data from the US Census Bureau",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "A natural language query about Census data, such as 'What is the population of California?' or 'Compare poverty rates across counties in Florida'"
                            },
                            "dataset": {
                                "type": "string",
                                "description": "Optional: The specific Census dataset to query (e.g., 'acs/acs5', 'acs/acs1', 'dec/pl')"
                            },
                            "year": {
                                "type": "string",
                                "description": "Optional: The year of data to retrieve (e.g., '2022', '2021', '2020')"
                            },
                            "variables": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional: Specific Census variables to include in the query"
                            },
                            "geographic_level": {
                                "type": "string",
                                "description": "Optional: The geographic level to query (e.g., 'state', 'county', 'city')"
                            },
                            "location": {
                                "type": "string",
                                "description": "Optional: Specific location to focus on (e.g., 'Texas', 'Austin, TX', 'Travis County')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
        
        return self._tools_list
    
    async def call_tool(self, tool_name, tool_params):
        """
        Call a tool from our Census MCP server.
        
        Args:
            tool_name: The name of the tool to call (should be "census_data")
            tool_params: The parameters to pass to the tool
            
        Returns:
            The result from the Census MCP server
        """
        if tool_name != "census_data":
            return {"error": f"Unknown tool: {tool_name}. Only 'census_data' is supported."}
            
        # Convert the tool parameters to our MCP server's expected format
        import requests
        
        # Extract required and optional parameters
        query = tool_params.get("query")
        if not query:
            return {"error": "Missing required parameter: query"}
            
        # Prepare optional parameters
        params = {}
        for param in ["dataset", "year", "variables", "geographic_level", "location"]:
            if param in tool_params and tool_params[param]:
                params[param] = tool_params[param]
                
        # If geographic_level and location are specified, convert them to predicates
        if "geographic_level" in params and "location" in params:
            geo_level = params.pop("geographic_level")
            location = params.pop("location")
            
            # This is a simplified version - a real implementation would need more robust mapping
            if geo_level == "state":
                params["predicates"] = {"for": f"state:{location}"}
            elif geo_level == "county":
                # Extract state from location if possible
                parts = location.split(",")
                if len(parts) > 1:
                    county, state = parts[0].strip(), parts[1].strip()
                    params["predicates"] = {"for": f"county:{county}", "in": f"state:{state}"}
                else:
                    params["predicates"] = {"for": f"county:{location}"}
            elif geo_level == "city":
                params["predicates"] = {"for": f"place:{location}"}
        
        # Create the MCP request
        mcp_request = {
            "mcp_version": "0.1.0",
            "params": params,
            "prompt": query
        }
        
        # Call our MCP server
        try:
            response = requests.post(f"{self.mcp_url}/mcp", json=mcp_request)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Error calling Census MCP: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"Error calling Census MCP: {str(e)}"}

class OpenAICensusMCP(MCP):
    """
    An MCP implementation for OpenAI's Agent SDK that connects to our Census MCP server.
    This custom MCP class adheres to the OpenAI Agent SDK's MCP interface.
    """
    
    def __init__(self, mcp_url="http://localhost:8050"):
        """Initialize the MCP with the URL to our Census MCP server."""
        self.wrapper = CensusMCPWrapper(mcp_url)
        
    async def list_tools(self):
        """Get a list of tools from our Census MCP server."""
        return await self.wrapper.get_tools_list()
        
    async def call_tool(self, name, params, tracing_info=None):
        """Call a tool from our Census MCP server."""
        return await self.wrapper.call_tool(name, params)

async def run_census_agent():
    """
    Create and run an OpenAI Agent with our Census MCP integration.
    
    This demonstrates how to use our Census MCP server with OpenAI's Agent SDK.
    """
    # Initialize the OpenAI client with the API key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create our custom Census MCP
    census_mcp = OpenAICensusMCP(mcp_url="http://localhost:8050")
    
    # Create an Agent with our Census MCP
    agent = Agent(
        name="PolicyAide Census Assistant",
        instructions="""
        You are PolicyAide's Census Data Assistant that helps with demographic, economic, and housing data research.
        Use the Census data tool to access detailed information from the US Census Bureau.
        When analyzing policy implications, consider demographic trends, economic factors, and housing conditions.
        Provide clear, factual responses that help policymakers understand the data and its policy implications.
        """,
        model="gpt-4-turbo-preview",  # Use an appropriate model for your needs
        client=client,
        mcp_servers=[census_mcp]
    )
    
    # Example queries to demonstrate the agent
    example_queries = [
        "What is the population of Texas according to Census data?",
        "Compare poverty rates in Austin, Dallas, and Houston",
        "What are the housing affordability metrics in California?",
        "Show me educational attainment levels in Florida counties"
    ]
    
    # Run the agent with each example query
    for query in example_queries:
        print(f"\n\n===== Running agent with query: {query} =====\n")
        
        # Start the agent with the query
        thread = await agent.create_thread()
        message = await agent.add_message(thread=thread.id, role="user", content=query)
        
        # Wait for the agent to complete and get the response
        run = await agent.run_thread(thread.id)
        
        # Print the agent's response
        messages = await agent.get_messages(thread.id)
        for msg in messages:
            if msg.role == "assistant":
                print(f"Agent response: {msg.content[0].text}")
        
        # Add a separator
        print("\n" + "=" * 80)

async def run_demo():
    """Run a comprehensive demo of the OpenAI Agent with Census MCP integration."""
    print("\n===== CENSUS MCP WITH OPENAI AGENT SDK DEMO =====\n")
    print("This demo shows how to integrate our Census MCP server with OpenAI's Agent SDK.")
    print("The agent will use both our custom Census MCP and OpenAI's capabilities to answer policy research questions.")
    
    try:
        await run_census_agent()
        
        print("\n===== DEMO COMPLETE =====")
        print("\nThis integration allows PolicyAide to leverage both:")
        print("1. Our custom Census MCP for detailed demographic, economic, and housing data")
        print("2. OpenAI's Agent capabilities for policy analysis and reasoning")
        
    except Exception as e:
        print(f"\n[ERROR] Demo encountered an error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the demo
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() 