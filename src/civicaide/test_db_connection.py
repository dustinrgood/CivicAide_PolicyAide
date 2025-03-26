#!/usr/bin/env python
"""
Test database connection for the CivicAide Policy Analysis System.
This script helps diagnose database connectivity issues.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the trace processor
from src.civicaide.trace_manager import get_trace_processor

def check_trace_exists(trace_id):
    """Check if a specific trace exists in the database"""
    trace_processor = get_trace_processor()
    
    if not trace_processor.connection:
        print("❌ Database connection is not available")
        return False
    
    try:
        # Create a cursor
        cursor = trace_processor.connection.cursor()
        
        # Check if the trace exists
        cursor.execute("SELECT trace_id, policy_query, policy_type, created_at FROM policy_aide.traces WHERE trace_id = %s", (trace_id,))
        trace = cursor.fetchone()
        
        if trace:
            print(f"✅ Trace {trace_id} found in database:")
            print(f"  Query: {trace[1]}")
            print(f"  Type: {trace[2]}")
            print(f"  Created: {trace[3]}")
            
            # Check associated spans
            cursor.execute("SELECT COUNT(*) FROM policy_aide.spans WHERE trace_id = %s", (trace_id,))
            span_count = cursor.fetchone()[0]
            print(f"  Spans: {span_count}")
            
            return True
        else:
            print(f"❌ Trace {trace_id} not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error checking trace: {e}")
        return False

def main():
    """Main entry point for testing database connection."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test database connection and check traces')
    parser.add_argument('--trace-id', help='Check if a specific trace ID exists in the database')
    args = parser.parse_args()
    
    # If checking for a specific trace
    if args.trace_id:
        print(f"Checking for trace ID: {args.trace_id}")
        check_trace_exists(args.trace_id)
        return
    
    # Otherwise run the full test
    print("Testing database connection for CivicAide Policy Analysis System")
    print("=" * 60)
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Print environment variables (masked for security)
    print("\nDatabase connection environment variables:")
    for env_var in ["user", "host", "port", "dbname"]:
        print(f"  {env_var}: {os.getenv(env_var, 'NOT SET')}")
    print(f"  password: {'SET' if os.getenv('password') else 'NOT SET'}")
    
    # Test connection
    print("\nTesting database connection...")
    if trace_processor.connection:
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        
    # Test database schema
    print("\nTesting database schema...")
    schema_ok = trace_processor.test_database_connection()
    if schema_ok:
        print("✅ Database schema looks good")
    else:
        print("❌ Database schema has issues")
    
    # Try a simple test insertion
    if trace_processor.connection:
        print("\nTrying test insertion...")
        try:
            test_trace_id = "test_trace_" + os.urandom(4).hex()
            test_span_id = "test_span_" + os.urandom(4).hex()
            
            # Record a test interaction
            trace_processor.record_agent_interaction(
                trace_id=test_trace_id,
                agent_name="Test Agent",
                input_text="Test input",
                output_text="Test output",
                model="Test model"
            )
            
            # Save trace to file and DB
            trace_file = trace_processor.save_trace_to_file_and_db("Test query", "test")
            print(f"Test trace saved to: {trace_file}")
            
            # Verify the trace exists in the database
            print("\nVerifying trace in database...")
            if check_trace_exists(test_trace_id):
                print("✅ Test insertion successful and verified")
            else:
                print("❌ Test verification failed - trace not found in database")
        except Exception as e:
            print(f"❌ Test insertion failed: {e}")
    
    print("\nDatabase connection test complete")
    
    # Print usage instructions
    print("\nTo check if a specific trace exists, run:")
    print(f"python {Path(__file__).name} --trace-id YOUR_TRACE_ID")

if __name__ == "__main__":
    main() 