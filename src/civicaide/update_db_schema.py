#!/usr/bin/env python
"""
Update database schema for the CivicAide Policy Analysis System.
This script adds new fields to the database schema to support OpenAI trace ID tracking.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the trace processor
from src.civicaide.trace_manager import get_trace_processor

def main():
    """Main entry point for updating database schema."""
    print("Updating database schema for CivicAide Policy Analysis System")
    print("=" * 60)
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Check database connection
    if not trace_processor.connection:
        print("❌ Database connection is not available")
        return
    
    print("✅ Database connection successful")
    
    # Create a cursor
    cursor = trace_processor.connection.cursor()
    
    try:
        # Check if openai_response_id column exists in spans table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'policy_aide' 
                AND table_name = 'spans' 
                AND column_name = 'openai_response_id'
            )
        """)
        column_exists = cursor.fetchone()[0]
        
        # Add openai_response_id column if it doesn't exist
        if not column_exists:
            print("Adding openai_response_id column to spans table...")
            cursor.execute("""
                ALTER TABLE policy_aide.spans
                ADD COLUMN openai_response_id VARCHAR(255)
            """)
            trace_processor.connection.commit()
            print("✅ Added openai_response_id column to spans table")
        else:
            print("✅ openai_response_id column already exists in spans table")
        
        # Check if system_instructions column exists in spans table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'policy_aide' 
                AND table_name = 'spans' 
                AND column_name = 'system_instructions'
            )
        """)
        column_exists = cursor.fetchone()[0]
        
        # Add system_instructions column if it doesn't exist
        if not column_exists:
            print("Adding system_instructions column to spans table...")
            cursor.execute("""
                ALTER TABLE policy_aide.spans
                ADD COLUMN system_instructions TEXT
            """)
            trace_processor.connection.commit()
            print("✅ Added system_instructions column to spans table")
            
            # Migrate existing system instructions from span_data
            print("Migrating existing system instructions from span_data...")
            cursor.execute("""
                UPDATE policy_aide.spans
                SET system_instructions = span_data->'content'->>'system_instructions'
                WHERE span_data->'content'->>'system_instructions' IS NOT NULL
            """)
            trace_processor.connection.commit()
            print("✅ Migrated existing system instructions")
        else:
            print("✅ system_instructions column already exists in spans table")
        
        # Check if openai_trace_data column exists in traces table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'policy_aide' 
                AND table_name = 'traces' 
                AND column_name = 'openai_trace_data'
            )
        """)
        column_exists = cursor.fetchone()[0]
        
        # Add openai_trace_data column if it doesn't exist
        if not column_exists:
            print("Adding openai_trace_data column to traces table...")
            cursor.execute("""
                ALTER TABLE policy_aide.traces
                ADD COLUMN openai_trace_data JSONB DEFAULT '{}'::jsonb
            """)
            trace_processor.connection.commit()
            print("✅ Added openai_trace_data column to traces table")
        else:
            print("✅ openai_trace_data column already exists in traces table")
        
        print("\nDatabase schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        trace_processor.connection.rollback()
    
if __name__ == "__main__":
    main() 