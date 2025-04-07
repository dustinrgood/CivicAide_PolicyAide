"""
Shared utility functions for CivicAide policy system.

This module contains utility functions that are used across different policy
components, including web research, JSON processing, and error handling.
"""

import os
import sys
import json
import asyncio
import re
import random
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path

# Import the agents SDK
from agents import WebSearchTool, trace, custom_span
from agents.result import RunResult

# Web research utilities

async def execute_web_searches(
    search_queries: List[str],
    search_tool: Optional[Callable] = None,
    max_concurrent: int = 5
) -> Dict[str, str]:
    """
    Execute a list of web searches concurrently.
    
    Args:
        search_queries: List of search queries
        search_tool: Custom search function (defaults to WebSearchTool.search)
        max_concurrent: Maximum number of concurrent searches
        
    Returns:
        Dictionary mapping search queries to results
    """
    if search_tool is None:
        # Create a mock search function since WebSearchTool.search might not be available
        async def mock_search(query: str) -> str:
            print(f"[Mock Web Search] Searching for: {query}")
            # Return a simple mock result
            return f"Mock search results for '{query}'. " + \
                   f"In a real environment, this would return actual search results from the web."
        
        web_tool = WebSearchTool()
        # Use mock_search if web_tool.search doesn't exist
        search_tool = getattr(web_tool, "search", mock_search)
    
    results = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _bounded_search(query: str) -> None:
        """Run a single search with concurrency limits."""
        async with semaphore:
            try:
                with custom_span(f"Web search: {query[:30]}..."):
                    result = await search_tool(query)
                    results[query] = result
            except Exception as e:
                print(f"Error searching for '{query}': {str(e)}")
                results[query] = f"Error: {str(e)}"
    
    # Create and run tasks
    tasks = [asyncio.create_task(_bounded_search(query)) for query in search_queries]
    await asyncio.gather(*tasks)
    
    return results

# JSON handling utilities

def extract_json_from_text(text: str) -> str:
    """
    Extract JSON content from text that might contain explanatory text or code blocks.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        The extracted JSON string
        
    Note:
        This is more robust than extract_json_from_markdown as it handles more cases.
    """
    # Try to find JSON within markdown code blocks first
    if "```" in text:
        code_blocks = re.findall(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if code_blocks:
            # Use the first code block that looks like JSON
            for block in code_blocks:
                block = block.strip()
                if block.startswith("{") or block.startswith("["):
                    return block
    
    # Try to find JSON by looking for enclosing braces or brackets
    json_patterns = [
        # Array pattern
        r"\[\s*\{.*\}\s*\]",
        # Object pattern
        r"\{.*\}"
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            # Return the longest match (likely the most complete JSON)
            return max(matches, key=len)
    
    # If we can't find JSON patterns, return the original text
    # (let the JSON parser handle the error)
    return text

def safe_json_loads(text: str, default_value: Any = None) -> Any:
    """
    Safely parse JSON from text, with fallback to default value.
    
    Args:
        text: Text containing JSON
        default_value: Value to return if parsing fails
        
    Returns:
        Parsed JSON object or default_value on failure
    """
    try:
        # First try to extract JSON from the text
        json_text = extract_json_from_text(text)
        return json.loads(json_text)
    except Exception as e:
        if default_value is not None:
            return default_value
        raise ValueError(f"Failed to parse JSON: {e}\nText was: {text[:200]}...")

# Error handling utilities

class RetrySettings:
    """Settings for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize retry settings.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Factor to increase delay by on each retry
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

async def with_retry(
    func: Callable,
    *args,
    retry_settings: RetrySettings = None,
    error_callback: Optional[Callable[[Exception, int], None]] = None,
    **kwargs
) -> Any:
    """
    Execute a function with retry logic.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        retry_settings: Settings for retry behavior
        error_callback: Function to call on error
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function
        
    Raises:
        Exception: The last exception encountered if all retries fail
    """
    if retry_settings is None:
        retry_settings = RetrySettings()
    
    retry_count = 0
    last_exception = None
    
    while retry_count <= retry_settings.max_retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            retry_count += 1
            
            if error_callback:
                error_callback(e, retry_count)
            
            if retry_count > retry_settings.max_retries:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                retry_settings.base_delay * (retry_settings.backoff_factor ** (retry_count - 1)),
                retry_settings.max_delay
            )
            
            # Add some jitter to avoid thundering herd problems
            jitter = 0.1 * delay * (2 * random.random() - 1)
            delay += jitter
            
            print(f"Retry {retry_count}/{retry_settings.max_retries} after error: {str(e)}")
            print(f"Waiting {delay:.2f} seconds before retrying...")
            
            await asyncio.sleep(delay)
    
    # If we get here, all retries failed
    raise last_exception

# File handling utilities

def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def read_json_file(file_path: Union[str, Path], default_value: Any = None) -> Any:
    """
    Read JSON from a file with error handling.
    
    Args:
        file_path: Path to the JSON file
        default_value: Value to return if reading fails
        
    Returns:
        Parsed JSON content or default_value on failure
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        if default_value is not None:
            return default_value
        raise ValueError(f"Failed to read JSON file {file_path}: {e}")

def write_json_file(
    data: Any,
    file_path: Union[str, Path],
    ensure_dir: bool = True,
    indent: int = 2
) -> Path:
    """
    Write data to a JSON file with directory creation.
    
    Args:
        data: Data to write
        file_path: Path to the output file
        ensure_dir: Whether to create parent directories
        indent: Indentation level for JSON
        
    Returns:
        Path object for the file
    """
    path_obj = Path(file_path)
    
    if ensure_dir:
        path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)
    
    return path_obj 