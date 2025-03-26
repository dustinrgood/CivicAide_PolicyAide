#!/usr/bin/env python
"""
Script to check Supabase connection and ensure credentials are loaded correctly
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Try multiple potential .env locations
env_paths = [
    Path(__file__).parent / "local.env",             # src/civicaide/local.env
    Path(__file__).parent.parent.parent / ".env",    # Root .env
    Path(__file__).parent / ".env",                  # src/civicaide/.env
]

def check_connection():
    """Check if we can connect to the Supabase PostgreSQL database"""
    # Try loading from multiple potential paths
    for env_path in env_paths:
        if env_path.exists():
            print(f"\n=== Trying to load environment from: {env_path} ===")
            load_dotenv(env_path, override=True)
            
            # Check if credentials are loaded
            db_creds = {
                "user": os.getenv("user"),
                "password": os.getenv("password"),
                "host": os.getenv("host"),
                "port": os.getenv("port"),
                "dbname": os.getenv("dbname")
            }
            
            # Print loaded credentials (hide password)
            print("Loaded credentials:")
            for key, value in db_creds.items():
                if key != "password":
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {'SET' if value else 'NOT SET'}")
            
            # Try connecting to the database
            if all(db_creds.values()):
                try:
                    print("\nAttempting to connect to Supabase database...")
                    conn = psycopg2.connect(**db_creds)
                    print("✅ Successfully connected to database!")
                    
                    # Try a simple query
                    cursor = conn.cursor()
                    
                    # Check policy_aide.traces
                    print("\nChecking tables...")
                    
                    try:
                        cursor.execute("SELECT COUNT(*) FROM policy_aide.traces")
                        trace_count = cursor.fetchone()[0]
                        print(f"✅ policy_aide.traces exists with {trace_count} rows")
                    except Exception as e:
                        print(f"❌ Error accessing policy_aide.traces: {e}")
                    
                    # Check policy_aide.spans
                    try:
                        cursor.execute("SELECT COUNT(*) FROM policy_aide.spans")
                        span_count = cursor.fetchone()[0]
                        print(f"✅ policy_aide.spans exists with {span_count} rows")
                    except Exception as e:
                        print(f"❌ Error accessing policy_aide.spans: {e}")
                    
                    # Print a sample trace if any exist
                    if trace_count > 0:
                        try:
                            cursor.execute("""
                                SELECT trace_id, policy_query, policy_type, created_at 
                                FROM policy_aide.traces 
                                ORDER BY created_at DESC LIMIT 1
                            """)
                            trace = cursor.fetchone()
                            print(f"\nMost recent trace:")
                            print(f"  ID: {trace[0]}")
                            print(f"  Query: {trace[1]}")
                            print(f"  Type: {trace[2]}")
                            print(f"  Created: {trace[3]}")
                            
                            # Get spans for this trace
                            cursor.execute(f"""
                                SELECT span_id, span_type, agent_name
                                FROM policy_aide.spans
                                WHERE trace_id = '{trace[0]}'
                                LIMIT 5
                            """)
                            spans = cursor.fetchall()
                            print(f"\n  Spans for this trace ({len(spans)} shown):")
                            for span in spans:
                                print(f"    {span[0]} | {span[1]} | {span[2]}")
                        except Exception as e:
                            print(f"Error retrieving sample trace: {e}")
                    
                    conn.close()
                    return True
                except Exception as e:
                    print(f"❌ Failed to connect using credentials from {env_path}")
                    print(f"Error: {e}")
            else:
                print(f"❌ Missing one or more required database credentials in {env_path}")
        else:
            print(f"❓ Environment file not found: {env_path}")
    
    # If we get here, all connection attempts failed
    print("\n❌ Failed to connect to Supabase database from any environment file")
    print("\nCheck your local.env file has the following variables:")
    print("  user=postgres.lgsyjrdurhanlymmqndk")
    print("  host=aws-0-us-east-1.pooler.supabase.com")
    print("  port=6543")
    print("  dbname=postgres")
    print("  password=YOUR_DATABASE_PASSWORD")
    return False

if __name__ == "__main__":
    print("==== Supabase Connection Test ====")
    check_connection()
    print("\n=================================")
    print("If connection failed, ensure your local.env file has the correct credentials.")
    print("You can find them in the Supabase dashboard under Project Settings > Database > Connection Info.") 