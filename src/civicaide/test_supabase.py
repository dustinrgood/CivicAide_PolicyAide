#!/usr/bin/env python
"""
Test script to verify Supabase integration with trace manager
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the trace processor
from src.civicaide.trace_manager import get_trace_processor

def generate_trace_id():
    """Generate a unique trace ID"""
    return f"trace_{uuid.uuid4().hex[:24]}"

def main():
    """Main test function"""
    print("Testing Supabase trace integration...")
    
    # Get trace processor
    trace_processor = get_trace_processor()
    
    # Generate a test trace ID
    trace_id = generate_trace_id()
    print(f"Generated test trace ID: {trace_id}")
    
    # Create some test spans
    test_spans = [
        {
            "span_id": "span_1",
            "trace_id": trace_id,
            "span_type": "test_initialization",
            "started_at": datetime.now().isoformat(),
            "ended_at": datetime.now().isoformat(),
            "details": {
                "agent_name": "Test Agent",
                "message": "Initialized test process"
            }
        },
        {
            "span_id": "span_2",
            "trace_id": trace_id,
            "span_type": "test_processing",
            "started_at": datetime.now().isoformat(),
            "ended_at": datetime.now().isoformat(),
            "details": {
                "agent_name": "Test Agent",
                "message": "Processed test data"
            }
        }
    ]
    
    # Set up trace processor with test data
    trace_processor.current_trace_id = trace_id
    trace_processor.traces[trace_id] = test_spans
    
    # Save to file and Supabase
    trace_file = trace_processor.save_trace_to_file_and_db("Supabase Integration Test", "test")
    
    if trace_file:
        print(f"Test trace saved to: {trace_file}")
        print("✅ Supabase integration test completed successfully!")
    else:
        print("❌ Failed to save trace data.")

if __name__ == "__main__":
    main() 