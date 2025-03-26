#!/usr/bin/env python
"""
Test script for the parent-child span relationships and token usage tracking
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

async def test_parent_child_spans():
    """Test parent-child span relationships and token usage tracking"""
    print("Testing parent-child span relationships and token usage tracking...")
    
    # Generate a trace ID
    trace_id = f"trace_{uuid.uuid4().hex[:16]}"
    print(f"Using trace ID: {trace_id}")
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Initialize trace
    with trace("Test Parent-Child Spans", trace_id=trace_id) as current_trace:
        # Record the root span
        root_span_id = trace_processor.record_agent_interaction(
            trace_id=trace_id,
            agent_name="Root Agent",
            input_text="Test input for root",
            output_text="Test output from root",
            span_type="root_span",
            model="test_model",
            tokens_used={"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25}
        )
        print(f"Created root span with ID: {root_span_id}")
        
        # Create a child span
        child_span_id = trace_processor.record_agent_interaction(
            trace_id=trace_id,
            agent_name="Child Agent",
            input_text="Test input for child",
            output_text="Test output from child",
            span_type="child_span",
            model="test_model",
            parent_span_id=root_span_id,
            tokens_used={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        print(f"Created child span with ID: {child_span_id} (parent: {root_span_id})")
        
        # Create a grandchild span
        grandchild_span_id = trace_processor.record_agent_interaction(
            trace_id=trace_id,
            agent_name="Grandchild Agent",
            input_text="Test input for grandchild",
            output_text="Test output from grandchild",
            span_type="grandchild_span",
            model="test_model",
            parent_span_id=child_span_id,
            tokens_used=50  # Test numeric token count
        )
        print(f"Created grandchild span with ID: {grandchild_span_id} (parent: {child_span_id})")
        
        # Create a second child of the root
        sibling_span_id = trace_processor.record_agent_interaction(
            trace_id=trace_id,
            agent_name="Sibling Agent",
            input_text="Test input for sibling",
            output_text="Test output from sibling",
            span_type="sibling_span",
            model="test_model",
            parent_span_id=root_span_id,
            tokens_used="75"  # Test string token count
        )
        print(f"Created sibling span with ID: {sibling_span_id} (parent: {root_span_id})")
    
    # Save the trace data
    trace_file = trace_processor.save_trace_to_file_and_db("Parent Child Test", "test")
    if trace_file:
        print(f"Trace data saved to: {trace_file}")
    
    # Query the database to verify parent-child relationships
    print("\nVerifying spans in database...")
    if trace_processor.connection:
        try:
            cursor = trace_processor.connection.cursor()
            
            # Fetch all spans in this trace with parent_span_id
            cursor.execute("""
                SELECT span_id, parent_span_id, span_type, tokens_used
                FROM policy_aide.spans 
                WHERE trace_id = %s
                ORDER BY span_id
            """, (trace_id,))
            
            spans = cursor.fetchall()
            print(f"Found {len(spans)} spans in the database:")
            
            for span_id, parent_span_id, span_type, tokens_used in spans:
                parent_info = f"(parent: {parent_span_id})" if parent_span_id else "(root)"
                tokens_info = f"tokens: {tokens_used}" if tokens_used else "no token data"
                print(f"  {span_id} - {span_type} {parent_info} - {tokens_info}")
            
            # Check if the structure is as expected
            if len(spans) == 4:
                print("✅ All spans successfully stored with proper relationships")
            else:
                print("❌ Expected 4 spans but found {len(spans)}")
                
        except Exception as e:
            print(f"Error querying database: {e}")
    
    print("Test completed!")
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(test_parent_child_spans())
        if result:
            print("✅ Parent-child span relationships test passed")
            return 0
        else:
            print("❌ Parent-child span relationships test failed")
            return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 