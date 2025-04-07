# Integrating Census MCP with PolicyAide

This guide explains how to integrate the Census MCP server with PolicyAide's existing codebase.

## Integration Options

There are two primary ways to integrate the Census MCP with PolicyAide:

1. **Drop-in Replacement**: Use the `CensusMCPAdapter` as a direct replacement for the existing `CensusAPI` class
2. **OpenAI Agent Integration**: Incorporate the Census MCP as a tool available to PolicyAide's OpenAI Agent

## Option 1: Drop-in Replacement

The `CensusMCPAdapter` class is designed to be a drop-in replacement for PolicyAide's existing `CensusAPI` class. It implements the same interface but uses our Census MCP server instead of direct Census API calls.

### Step 1: Import the Adapter

In your PolicyAide codebase, import the adapter:

```python
from policyaide_adapter import CensusMCPAdapter
```

### Step 2: Replace the CensusAPI Class

Find where the original `CensusAPI` class is initialized in your code and replace it with our adapter:

```python
# Original code
# census_api = CensusAPI()

# New code
census_api = CensusMCPAdapter(mcp_url="http://localhost:8050")
```

### Step 3: Use as Normal

The adapter maintains the same interface as the original `CensusAPI` class, so you can use it exactly the same way:

```python
# This code works with both the original CensusAPI and our CensusMCPAdapter
demographics = census_api.get_demographics(location)
```

## Option 2: OpenAI Agent Integration

You can also integrate the Census MCP as a tool available to PolicyAide's OpenAI Agent. This allows the agent to use the Census MCP to get data while maintaining its reasoning capabilities.

### Step 1: Add MCP to Requirements

Make sure to add the OpenAI Agent SDK to your requirements:

```
openai>=1.0.0
openai-agents-python
```

### Step 2: Import the Census MCP Integration

Import the Census MCP integration in your agent setup code:

```python
from openai_agent_integration import OpenAICensusMCP
```

### Step 3: Add the Census MCP to Your Agent

When creating your agent, add the Census MCP as an MCP server:

```python
# Create our custom Census MCP
census_mcp = OpenAICensusMCP(mcp_url="http://localhost:8050")

# Create an Agent with our Census MCP
agent = Agent(
    name="PolicyAide Assistant",
    instructions="""
    You are PolicyAide's assistant that helps with policy research and analysis.
    Use the Census data tool to access demographic, economic, and housing information.
    Provide clear, factual responses that help policymakers understand data and policy implications.
    """,
    model="gpt-4-turbo-preview",
    client=client,
    mcp_servers=[census_mcp]  # Add the Census MCP here
)
```

## Hybrid Approach

For maximum flexibility, you can use both integration methods:

1. Use the `CensusMCPAdapter` for direct access to Census data in your code
2. Use the OpenAI Agent integration to allow the agent to access Census data in conversations

This provides both programmatic access for your backend code and conversational access for user interactions.

## Example Implementation

See the following files for examples:

- `policyaide_adapter.py`: Drop-in replacement for the CensusAPI class
- `openai_agent_integration.py`: Integration with OpenAI's Agent SDK

## Test Drive

To test the integration, you can use the provided examples:

### Testing the Adapter

```bash
python policyaide_adapter.py
```

### Testing the OpenAI Agent Integration

```bash
python openai_agent_integration.py
```

## Production Deployment Considerations

When deploying to production, consider:

1. **Reliability**: Deploy the Census MCP server with proper monitoring and auto-recovery
2. **Scaling**: Use load balancing if high query volume is expected
3. **Security**: Secure the MCP server with API keys or other authentication
4. **Caching**: Implement response caching to reduce redundant Census API calls
5. **Fallback**: Implement fallback to direct Census API if the MCP server is unavailable

## Next Steps for Enhancement

Future enhancements could include:

1. **Improved City Detection**: Enhance location parsing for more accurate city-level data
2. **Expanded Variables**: Add support for more Census variables based on PolicyAide needs
3. **Time Series Analysis**: Add support for historical data comparison
4. **Cross-Dataset Integration**: Combine data from multiple Census datasets
5. **Visualization Integration**: Connect the MCP with data visualization tools 