import os
import json
from datetime import datetime
from pathlib import Path
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import uuid

# Try to load environment variables from multiple locations
env_paths = [
    Path(__file__).parent / "local.env",             # src/civicaide/local.env
    Path(__file__).parent.parent.parent / ".env",    # Root .env
    Path(__file__).parent / ".env",                  # src/civicaide/.env
]

for env_path in env_paths:
    if env_path.exists():
        print(f"Loading environment variables from: {env_path}")
        load_dotenv(env_path, override=True)
        break

class SimpleTraceProcessor:
    """Simple trace processor that captures and stores trace data to Supabase"""
    
    def __init__(self):
        self.traces = {}
        self.current_trace_id = None
        # Create a database connection
        self.connection = None
        self.connect_to_db()
        
    def connect_to_db(self):
        """Connect to the Supabase PostgreSQL database"""
        try:
            # Print connection parameters (hide password)
            if os.getenv("user") and os.getenv("host") and os.getenv("port") and os.getenv("dbname"):
                print(f"Connecting to database: user={os.getenv('user')}, host={os.getenv('host')}, port={os.getenv('port')}, dbname={os.getenv('dbname')}")
            else:
                print("WARNING: Missing one or more database connection parameters")
                print(f"Available environment vars: {[k for k in os.environ.keys() if k in ['user', 'host', 'port', 'dbname']]}")
            
            # Attempt connection
            self.connection = psycopg2.connect(
                user=os.getenv("user"),
                password=os.getenv("password"),
                host=os.getenv("host"),
                port=os.getenv("port"),
                dbname=os.getenv("dbname")
            )
            print("Connected to Supabase PostgreSQL database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connection = None
            
            # Print more diagnostic information
            print("Connection environment variables:")
            for env_var in ["user", "host", "port", "dbname"]:
                print(f"  {env_var}: {os.getenv(env_var, 'NOT SET')}")
            print(f"  password: {'SET' if os.getenv('password') else 'NOT SET'}")
    
    def add_span(self, trace_id, span_data):
        """Add a span to a trace with full input/output content"""
        if trace_id not in self.traces:
            self.traces[trace_id] = []
            self.current_trace_id = trace_id
            
        # Ensure the span has trace_id set
        if "trace_id" not in span_data:
            span_data["trace_id"] = trace_id
            
        self.traces[trace_id].append(span_data)
        return span_data["span_id"]
    
    def record_agent_interaction(self, trace_id, agent_name, input_text, output_text, 
                              span_type="agent_interaction", parent_span_id=None, 
                              model=None, tokens_used=None, metadata=None,
                              system_instructions=None):
        """
        Record a complete agent interaction with full input and output content
        
        Args:
            trace_id: The trace ID to associate this span with
            agent_name: Name of the agent
            input_text: The full input prompt/text
            output_text: The full output/response
            span_type: Type of span
            parent_span_id: ID of parent span if this is a child span
            model: The model used (if applicable)
            tokens_used: Token usage information (if available)
            metadata: Any additional metadata
            system_instructions: The system instructions/prompt for this agent
            
        Returns:
            span_id: The ID of the created span
        """
        # Create a timestamp
        now = datetime.now()
        
        # Generate a span ID
        span_id = f"span_{len(self.traces.get(trace_id, [])) + 1}"
        
        # Create content dictionary with all relevant fields
        content = {
            "input": input_text,
            "output": output_text,
            "model": model,
            "tokens_used": tokens_used,
            "system_instructions": system_instructions
        }
        
        # Ensure tokens_used is properly formatted
        if tokens_used:
            if isinstance(tokens_used, dict):
                # Already formatted as a dictionary
                content["tokens_used"] = tokens_used
            elif isinstance(tokens_used, str):
                # Try to parse as JSON
                try:
                    parsed_tokens = json.loads(tokens_used)
                    content["tokens_used"] = parsed_tokens
                except:
                    content["tokens_used"] = {"total_tokens": tokens_used}
            elif isinstance(tokens_used, (int, float)):
                # Use as a simple value
                content["tokens_used"] = {"total_tokens": tokens_used}
            else:
                # For any other type, convert to string
                content["tokens_used"] = {"total_tokens": str(tokens_used)}
        
        # Extract OpenAI trace information if available in metadata
        if metadata and "openai_response_id" in metadata:
            content["openai_response_id"] = metadata["openai_response_id"]
        
        # Add any metadata to content
        if metadata:
            content.update(metadata)
        
        # Create the span data with full input/output
        span_data = {
            "span_id": span_id,
            "trace_id": trace_id,
            "parent_id": parent_span_id,
            "span_type": span_type,
            "started_at": now.isoformat(),
            "ended_at": now.isoformat(),
            "details": {
                "agent_name": agent_name,
                "message": f"{agent_name} processed request",
                "tokens_used": tokens_used
            },
            "content": content
        }
        
        # Add the span to the trace
        return self.add_span(trace_id, span_data)
    
    def generate_unique_span_id(self, trace_id):
        """Generate a unique span ID that won't conflict with existing spans"""
        base = f"span_{uuid.uuid4().hex[:8]}"
        count = 1
        span_id = f"{base}_{count}"
        
        # Check if this span ID is already in the database
        if self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM policy_aide.spans WHERE span_id = %s", (span_id,))
                if cursor.fetchone()[0] > 0:
                    # ID exists, generate a new one
                    count += 1
                    span_id = f"{base}_{count}"
            except:
                pass
                
        return span_id
    
    def save_trace_to_file_and_db_and_db(self, query, policy_type):
        """Save trace data to a file and to the Supabase database"""
        if not self.current_trace_id or not self.traces.get(self.current_trace_id):
            print("No trace data found to save")
            return None
            
        # Create traces directory if it doesn't exist
        os.makedirs("src/civicaide/traces", exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_file = f"src/civicaide/traces/trace_{policy_type}_{timestamp}.json"
        
        # Calculate total duration and collect agent names
        total_duration_ms = 0
        agent_names = set()
        
        for span in self.traces[self.current_trace_id]:
            # Extract agent name if available
            if "details" in span and "agent_name" in span["details"]:
                agent_names.add(span["details"]["agent_name"])
            
            # Calculate duration if timestamps are available
            if "started_at" in span and "ended_at" in span:
                try:
                    start = datetime.fromisoformat(span["started_at"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(span["ended_at"].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds() * 1000
                    span["duration_ms"] = duration
                    total_duration_ms += duration
                except:
                    pass
        
        # Prepare trace data
        trace_data = {
            "query": query,
            "trace_id": self.current_trace_id,
            "policy_type": policy_type,
            "timestamp": timestamp,
            "spans": self.traces[self.current_trace_id],
            "openai_trace_id": os.environ.get("OPENAI_TRACE_ID"),
            "agent_count": len(agent_names),
            "total_duration_ms": total_duration_ms
        }
        
        # Save to file
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2)
        
        # Save to database
        insertion_success = False
        if self.connection:
            try:
                # Create a cursor with autocommit OFF (default)
                cursor = self.connection.cursor()
                
                # Print diagnostic info
                print(f"Saving trace to Supabase: ID={trace_data['trace_id']}, Type={policy_type}, Spans={len(trace_data['spans'])}")
                
                # Insert trace record
                cursor.execute("""
                    INSERT INTO policy_aide.traces 
                    (trace_id, policy_query, policy_type, created_at, openai_trace_id, agent_count, total_duration_ms, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    trace_data["trace_id"],
                    trace_data["query"],
                    trace_data["policy_type"],
                    datetime.fromisoformat(timestamp.replace('_', 'T')),
                    trace_data.get("openai_trace_id"),
                    trace_data["agent_count"],
                    trace_data["total_duration_ms"],
                    json.dumps({})
                ))
                
                # Commit the trace record immediately
                self.connection.commit()
                print("✅ Trace record inserted successfully")
                insertion_success = True
                
                # Collect all span IDs to ensure uniqueness
                used_span_ids = set()
                span_error_count = 0
                
                # Insert span records with individual commits
                for i, span_data in enumerate(trace_data["spans"]):
                    # Convert timestamps to datetime objects
                    started_at = None
                    ended_at = None
                    
                    if "started_at" in span_data:
                        try:
                            started_at = datetime.fromisoformat(span_data["started_at"].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if "ended_at" in span_data:
                        try:
                            ended_at = datetime.fromisoformat(span_data["ended_at"].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Extract content data (inputs/outputs)
                    content_data = span_data.get("content", {})
                    span_data_json = span_data.get("span_data", {})
                    
                    # Extract input and output text from various possible locations
                    input_text = content_data.get("input")
                    output_text = content_data.get("output")
                    model_name = content_data.get("model")
                    
                    # Extract OpenAI response ID if available in metadata
                    openai_response_id = None
                    if "openai_response_id" in content_data:
                        openai_response_id = content_data.get("openai_response_id")
                    elif metadata := span_data.get("metadata", {}):
                        if "openai_response_id" in metadata:
                            openai_response_id = metadata.get("openai_response_id")
                    
                    # Check for other OpenAI trace information
                    openai_trace_data = {}
                    if "trace" in content_data:
                        openai_trace_data = content_data.get("trace", {})
                    elif "trace" in span_data:
                        openai_trace_data = span_data.get("trace", {})
                    
                    # If the span has span_data as a proper field, extract from there
                    if "span_data" in span_data and isinstance(span_data["span_data"], dict):
                        span_data_content = span_data["span_data"]
                        if not input_text and "input" in span_data_content:
                            input_text = str(span_data_content["input"])
                        if not output_text and "output" in span_data_content:
                            output_text = str(span_data_content["output"])
                        if not model_name and "model" in span_data_content:
                            model_name = str(span_data_content["model"])
                    
                    # Try to get these values from span_data if they're not in content
                    if not input_text and isinstance(span_data_json, dict):
                        # Try to extract from various locations in the span data
                        if "input" in span_data_json:
                            input_text = str(span_data_json["input"])
                        elif "details" in span_data_json and "message" in span_data_json["details"]:
                            input_text = str(span_data_json["details"]["message"])
                    
                    if not output_text and isinstance(span_data_json, dict):
                        if "output" in span_data_json:
                            output_text = str(span_data_json["output"])
                        elif "details" in span_data_json and "result" in span_data_json["details"]:
                            output_text = str(span_data_json["details"]["result"])
                    
                    # Also check if span_data is a string that needs parsing
                    if isinstance(span_data_json, str):
                        try:
                            parsed_data = json.loads(span_data_json)
                            if isinstance(parsed_data, dict):
                                if not input_text and "input" in parsed_data:
                                    input_text = str(parsed_data["input"])
                                if not output_text and "output" in parsed_data:
                                    output_text = str(parsed_data["output"])
                                if not model_name and "model" in parsed_data:
                                    model_name = str(parsed_data["model"])
                        except:
                            pass
                    
                    # Last resort - if we still don't have input/output, try to extract from the agent name and message
                    if not input_text and "details" in span_data and "agent_name" in span_data["details"]:
                        input_text = f"Agent: {span_data['details']['agent_name']}"
                        
                    if not output_text and "details" in span_data and "message" in span_data["details"]:
                        output_text = str(span_data["details"]["message"])
                    
                    # Generate a unique span ID to avoid conflicts
                    original_span_id = span_data["span_id"]
                    
                    # Make sure we don't reuse a span ID within this batch
                    base_unique_id = f"{original_span_id}_{trace_data['trace_id'][-6:]}"
                    unique_span_id = base_unique_id
                    
                    counter = 1
                    while unique_span_id in used_span_ids:
                        # Add a counter to make it unique
                        unique_span_id = f"{base_unique_id}_{counter}"
                        counter += 1
                    
                    used_span_ids.add(unique_span_id)
                    
                    print(f"  Inserting span {i+1}/{len(trace_data['spans'])}: {unique_span_id}")
                    
                    try:
                        # Ensure span has trace_id (use parent trace_id if missing)
                        span_trace_id = span_data.get("trace_id", trace_data["trace_id"])
                        
                        # Extract parent span ID from various possible locations
                        parent_span_id = span_data.get("parent_id")
                        if not parent_span_id and "parent_span_id" in span_data:
                            parent_span_id = span_data.get("parent_span_id")
                        elif not parent_span_id and "details" in span_data and "parent_id" in span_data["details"]:
                            parent_span_id = span_data["details"]["parent_id"]
                        
                        # Transform parent_span_id to match the same format as our unique span IDs
                        unique_parent_span_id = None
                        if parent_span_id:
                            # Extract the base part (e.g., 'span_1' from 'span_1_123456')
                            parent_base = parent_span_id
                            if '_' in parent_span_id and parent_span_id.count('_') == 1:
                                # Simple span ID like 'span_1', add suffix
                                unique_parent_span_id = f"{parent_span_id}_{trace_data['trace_id'][-6:]}"
                            elif '_' in parent_span_id:
                                # Already has a suffix or is in a different format
                                unique_parent_span_id = parent_span_id
                            
                            # Check if this parent span ID is in our used_span_ids set
                            if unique_parent_span_id not in used_span_ids:
                                # Try to find a matching span ID that starts with the same base
                                potential_parents = [
                                    sid for sid in used_span_ids
                                    if sid.startswith(parent_base + '_')
                                ]
                                if potential_parents:
                                    unique_parent_span_id = potential_parents[0]
                        
                        # Extract tokens used from content or metadata
                        tokens_used = None
                        if content_data and "tokens_used" in content_data:
                            tokens_used = content_data.get("tokens_used")
                        elif "metadata" in span_data and span_data["metadata"] and "tokens_used" in span_data["metadata"]:
                            tokens_used = span_data["metadata"]["tokens_used"]
                        elif "details" in span_data and "tokens_used" in span_data["details"]:
                            tokens_used = span_data["details"]["tokens_used"]
                        
                        # Convert tokens_used to proper JSON format for the database
                        if tokens_used is not None:
                            if isinstance(tokens_used, dict):
                                # Already a dict, convert to JSON string
                                tokens_used_json = json.dumps(tokens_used)
                            elif isinstance(tokens_used, str):
                                # Try to parse as JSON first
                                try:
                                    # Check if it's already valid JSON
                                    json.loads(tokens_used)
                                    tokens_used_json = tokens_used
                                except json.JSONDecodeError:
                                    # Not valid JSON, convert to simple total
                                    tokens_used_json = json.dumps({"total_tokens": tokens_used})
                            elif isinstance(tokens_used, (int, float)):
                                # Convert numeric value to JSON with total_tokens
                                tokens_used_json = json.dumps({"total_tokens": tokens_used})
                            else:
                                # For any other type, use None
                                tokens_used_json = None
                        else:
                            tokens_used_json = None
                        
                        # Double-check for openai_response_id in all possible locations
                        if not openai_response_id:
                            if "details" in span_data and "openai_response_id" in span_data["details"]:
                                openai_response_id = span_data["details"]["openai_response_id"]
                            elif "metadata" in span_data and span_data["metadata"] and "openai_response_id" in span_data["metadata"]:
                                openai_response_id = span_data["metadata"]["openai_response_id"]
                        
                        cursor.execute("""
                            INSERT INTO policy_aide.spans
                            (span_id, trace_id, parent_span_id, span_type, agent_name, 
                            started_at, ended_at, duration_ms, input_text, output_text, 
                            model, span_data, openai_response_id, tokens_used, system_instructions)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            unique_span_id,
                            span_trace_id,
                            unique_parent_span_id,
                            span_data.get("span_type", "unknown"),
                            span_data.get("details", {}).get("agent_name", "System"),
                            started_at,
                            ended_at,
                            span_data.get("duration_ms", 0),
                            input_text,  # Store input text
                            output_text,  # Store output text
                            model_name,  # Store model info
                            json.dumps(span_data),  # Store full span data
                            openai_response_id,  # Store OpenAI response ID if available
                            tokens_used_json,  # Store tokens used as JSON
                            content_data.get("system_instructions")  # Store system instructions directly
                        ))
                        
                        # Commit each span individually
                        self.connection.commit()
                        print(f"    ✅ Span {unique_span_id} inserted successfully")
                    except Exception as span_error:
                        span_error_count += 1
                        print(f"    ❌ Error inserting span {unique_span_id}: {span_error}")
                        # Rollback just this span insertion, not the whole transaction
                        self.connection.rollback()
                
                # Print final status
                if span_error_count == 0:
                    print(f"✅ All spans inserted successfully. Trace data saved with ID: {self.current_trace_id}")
                else:
                    print(f"⚠️ Trace record and {len(trace_data['spans']) - span_error_count}/{len(trace_data['spans'])} spans inserted successfully.")
                    print(f"   {span_error_count} spans failed to insert. Trace ID: {self.current_trace_id}")
                
                # Verify the trace was actually saved
                print("\nVerifying trace was saved to database...")
                verification = self.verify_trace_exists(trace_data["trace_id"])
                if not verification:
                    print("⚠️ WARNING: Although the operations reported success, the trace could not be verified in the database.")
                    print("   This might indicate a database connection issue or permissions problem.")
                
            except Exception as e:
                print(f"❌ Error saving trace to database: {str(e)}")
                self.connection.rollback()
                
                # Try to reconnect
                print("Attempting to reconnect to database...")
                self.connect_to_db()
        else:
            print("❌ Database connection not available. Trace saved to file only.")
        
        return trace_file
    
    def save_trace_to_file_and_db(self, query, policy_type):
        """Alias for save_trace_to_file_and_db_and_db"""
        return self.save_trace_to_file_and_db_and_db(query, policy_type)
        
    def test_database_connection(self):
        """Test database connection and schema"""
        if not self.connection:
            print("❌ Database connection is not available")
            self.connect_to_db()
            if not self.connection:
                return False
                
        try:
            # Create a cursor
            cursor = self.connection.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'policy_aide' AND table_name = 'traces')")
            traces_exists = cursor.fetchone()[0]
            
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'policy_aide' AND table_name = 'spans')")
            spans_exists = cursor.fetchone()[0]
            
            # Check table structures
            if traces_exists:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'policy_aide' AND table_name = 'traces'")
                trace_columns = [row[0] for row in cursor.fetchall()]
                print(f"Trace table columns: {trace_columns}")
            else:
                print("❌ Traces table does not exist")
                
            if spans_exists:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'policy_aide' AND table_name = 'spans'")
                span_columns = [row[0] for row in cursor.fetchall()]
                print(f"Spans table columns: {span_columns}")
            else:
                print("❌ Spans table does not exist")
                
            return traces_exists and spans_exists
            
        except Exception as e:
            print(f"❌ Error testing database schema: {e}")
            return False
    
    def verify_trace_exists(self, trace_id):
        """Verify that a trace exists in the database after insertion"""
        if not self.connection:
            print("❌ Database connection not available for verification")
            return False
            
        try:
            # Create a cursor
            cursor = self.connection.cursor()
            
            # Check if the trace exists
            cursor.execute("SELECT EXISTS (SELECT 1 FROM policy_aide.traces WHERE trace_id = %s)", (trace_id,))
            trace_exists = cursor.fetchone()[0]
            
            if trace_exists:
                # Check span count
                cursor.execute("SELECT COUNT(*) FROM policy_aide.spans WHERE trace_id = %s", (trace_id,))
                span_count = cursor.fetchone()[0]
                
                print(f"✅ Verified trace {trace_id} exists in database with {span_count} spans")
                return True
            else:
                print(f"❌ Verification failed: Trace {trace_id} not found in database despite successful insertion")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying trace: {e}")
            return False

# Create a singleton instance of the trace processor
trace_processor = SimpleTraceProcessor()

def get_trace_processor():
    """Get the trace processor instance"""
    return trace_processor