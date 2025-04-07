import streamlit as st
import os
import glob
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from policy_dashboard import fetch_openai_trace
import time

# Only set page config if not running from app.py
if os.environ.get("STREAMLIT_RUN_VIA_APP") != "true":
    # Set page config
    st.set_page_config(
        page_title="CivicAide Agent Traces Dashboard",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 95% !important;
    }
    .trace-header {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 5px solid #4e8df5;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e9ecef;
    }
    /* Ensure content stretches to full width */
    .css-1d391kg, .css-1r6slb0, .element-container, .stMarkdown {
        width: 100% !important;
    }
    /* Make plotly charts use full width properly */
    .js-plotly-plot, .plotly, .plot-container {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

def display_trace_timeline(spans):
    """Display a timeline visualization of trace spans"""
    # Convert spans to DataFrame
    spans_data = []
    
    for span in spans:
        # Parse dates
        try:
            start_time = datetime.fromisoformat(span["started_at"])
            end_time = datetime.fromisoformat(span["ended_at"])
            duration = (end_time - start_time).total_seconds()
        except:
            # Fallback for invalid dates
            duration = 0
        
        # Extract agent name if available
        agent_name = span.get("details", {}).get("agent_name", "System")
        
        # Get span type (action)
        span_type = span.get("span_type", "unknown")
        
        spans_data.append({
            "span_id": span["span_id"],
            "agent": agent_name,
            "action": span_type,
            "start_time": start_time if 'start_time' in locals() else None,
            "end_time": end_time if 'end_time' in locals() else None,
            "duration": duration
        })
    
    if spans_data:
        df = pd.DataFrame(spans_data)
        
        # Create a Gantt chart
        fig = px.timeline(
            df, 
            x_start="start_time", 
            x_end="end_time", 
            y="agent",
            color="action",
            hover_name="action",
            title="Agent Trace Timeline"
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Agent",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show the span details in a table
        st.subheader("Trace Details")
        st.dataframe(df[["agent", "action", "duration"]])
    else:
        st.warning("No valid timeline data available in this trace.")

def find_local_traces():
    """Find all local trace files in the traces directory"""
    try:
        # First try looking in src/civicaide/traces
        trace_files = glob.glob("traces/*.json")
        if not trace_files:
            # Also try current directory
            trace_files = glob.glob("*.json")
            if not trace_files:
                # Try application root directory
                trace_files = glob.glob("src/civicaide/traces/*.json")
        
        traces = []
        
        for file_path in trace_files:
            try:
                with open(file_path, 'r') as f:
                    trace_data = json.load(f)
                    
                filename = os.path.basename(file_path)
                created_at = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Extract trace_id from filename or data
                trace_id = trace_data.get('trace_id', trace_data.get('id', os.path.splitext(filename)[0]))
                
                # Get policy id if available
                policy_id = trace_data.get('policy_id', None)
                if not policy_id and "_policy_" in filename:
                    policy_id = filename.split("_policy_")[1].split("_")[0]
                
                traces.append({
                    'trace_id': trace_id,
                    'policy_id': policy_id,
                    'created_at': created_at,
                    'file_path': file_path,
                    'source': 'local'
                })
            except Exception as e:
                print(f"Error loading trace file {file_path}: {e}")
                
        # Sort by creation time (newest first)
        traces.sort(key=lambda x: x['created_at'], reverse=True)
        return traces
    except Exception as e:
        print(f"Error finding trace files: {e}")
        return []

def main():
    # Only set page config if not running from app.py
    if os.environ.get("STREAMLIT_RUN_VIA_APP") != "true":
        st.set_page_config(page_title="Policy Analysis Trace Viewer", layout="wide")
    
    st.markdown("# Policy Analysis Trace Viewer")
    
    # Check if we have a trace ID from URL parameter
    try:
        query_params = st.query_params
        trace_id = query_params.get("trace_id", None)
    except:
        # Fall back to legacy method
        query_params = st.experimental_get_query_params()
        trace_id = query_params.get("trace_id", [None])[0]
    
    with st.sidebar:
        st.markdown("## Trace Controls")
        
        # Option to view a specific trace by ID
        new_trace_id = st.text_input("Enter Trace ID:", value=trace_id if trace_id else "")
        if st.button("View Trace"):
            if new_trace_id:
                st.experimental_set_query_params(trace_id=new_trace_id)
                trace_id = new_trace_id
                st.rerun()
        
        st.divider()
        
        # List of available local traces
        st.markdown("## Available Traces")
        traces = find_local_traces()
        
        if not traces:
            st.info("No traces found.")
        else:
            for idx, trace in enumerate(traces):
                col1, col2 = st.columns([3, 1])
                
                # Truncate ID for display if needed
                display_id = trace['trace_id']
                if len(display_id) > 20:
                    display_id = display_id[:17] + "..."
                
                with col1:
                    trace_label = f"{display_id}"
                    if trace['policy_id']:
                        trace_label += f" ({trace['policy_id']})"
                    
                    if st.button(trace_label, key=f"trace_{idx}"):
                        st.experimental_set_query_params(trace_id=trace['trace_id'])
                        trace_id = trace['trace_id']
                        st.rerun()
                
                with col2:
                    st.caption(trace['created_at'].strftime("%m/%d %H:%M"))
    
    # Main content area
    if not trace_id:
        st.info("Select a trace from the sidebar or enter a trace ID to view details.")
        return
    
    # Fetch trace data
    with st.spinner(f"Loading trace data for {trace_id}..."):
        trace_data = fetch_openai_trace(trace_id)
        
    if not trace_data:
        st.error(f"Could not load trace data for ID: {trace_id}")
        return
    
    # Display trace overview
    st.markdown(f"## Trace Overview: {trace_data.get('id', 'Unknown')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Workflow", trace_data.get("workflow_name", "Unknown"))
    with col2:
        created_at = trace_data.get("created_at", "")
        if created_at:
            try:
                # Try to parse and format the timestamp
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        st.metric("Created", created_at)
    with col3:
        span_count = len(trace_data.get("spans", []))
        st.metric("Spans", span_count)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Timeline View", "Raw Data"])
    
    with tab1:
        spans = trace_data.get("spans", [])
        if not spans:
            st.info("No spans found in this trace.")
        else:
            # Process spans for visualization
            span_data = []
            for span in spans:
                # Check if we have the required fields
                if not all(k in span for k in ["id", "started_at", "ended_at"]):
                    continue
                    
                # Parse timestamps
                try:
                    started = datetime.fromisoformat(span["started_at"].replace('Z', '+00:00')) if isinstance(span["started_at"], str) else span["started_at"]
                    ended = datetime.fromisoformat(span["ended_at"].replace('Z', '+00:00')) if isinstance(span["ended_at"], str) else span["ended_at"]
                    
                    span_data.append({
                        "id": span["id"],
                        "name": span.get("name", "Unknown"),
                        "type": span.get("type", "Unknown"),
                        "started_at": started,
                        "ended_at": ended,
                        "duration_ms": span.get("duration_ms", (ended - started).total_seconds() * 1000),
                        "parent_id": span.get("parent_id", None)
                    })
                except Exception as e:
                    print(f"Error processing span {span['id']}: {e}")
            
            if span_data:
                # Convert to dataframe for easier manipulation
                df = pd.DataFrame(span_data)
                
                # Sort by start time
                df = df.sort_values("started_at")
                
                # Calculate the timeline position
                min_time = df["started_at"].min()
                max_time = df["ended_at"].max()
                total_duration = (max_time - min_time).total_seconds() * 1000
                
                # Display the timeline
                st.markdown("### Execution Timeline")
                
                for i, row in df.iterrows():
                    span_start = ((row["started_at"] - min_time).total_seconds() * 1000) / total_duration
                    span_width = max(row["duration_ms"] / total_duration, 0.005)  # Min width for visibility
                    
                    # Create the timeline bar
                    col1, col2 = st.columns([0.3, 0.7])
                    with col1:
                        st.write(f"**{row['name']}** ({row['type']})")
                        st.caption(f"{row['duration_ms']:.0f}ms")
                    
                    with col2:
                        # Create a progress bar to represent the timeline position
                        st.progress(span_start + span_width)
                        
                    # Add collapsible details
                    with st.expander("Details"):
                        st.json(spans[i])
            else:
                st.warning("Could not process span data for visualization.")
    
    with tab2:
        st.json(trace_data)

if __name__ == "__main__":
    main()