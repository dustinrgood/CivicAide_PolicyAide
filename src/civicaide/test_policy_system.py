#!/usr/bin/env python
"""
Test script for the tracing functionality in the policy evolution system
"""

import asyncio
import os
import sys
import json
import uuid
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the necessary modules
from src.agents import trace, custom_span, gen_trace_id
from src.civicaide.trace_manager import get_trace_processor

async def test_tracing():
    """Test the tracing functionality"""
    print("Testing tracing functionality...")
    
    # Generate a trace ID
    trace_id = f"test_trace_{uuid.uuid4().hex[:16]}"
    print(f"Using trace ID: {trace_id}")
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Initialize trace
    with trace("Test Trace", trace_id=trace_id) as current_trace:
        # Record the initialization
        trace_processor.record_agent_interaction(
            trace_id=trace_id,
            agent_name="Test Agent",
            input_text="Test input",
            output_text="Test output",
            span_type="test_span",
            model="test_model"
        )
        
        # Create a child span correctly
        with custom_span("Child Span", parent=current_trace) as child_span:
            print("Created child span successfully")
            
            # Create a second level child span
            with custom_span("Nested Span", parent=child_span) as nested_span:
                print("Created nested span successfully")
    
    # Save the trace data
    trace_file = trace_processor.save_trace_to_file_and_db("Test Query", "test")
    if trace_file:
        print(f"Trace data saved to: {trace_file}")
    
    print("Tracing test completed successfully!")
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_tracing())
        if result:
            print("✅ Test passed")
            return 0
        else:
            print("❌ Test failed")
            return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 