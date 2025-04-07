import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from trace_manager import get_trace_processor

def init_page():
    """Initialize the Streamlit page settings"""
    st.set_page_config(
        page_title="CivicAide Control Room",
        page_icon="🎛️",
        layout="wide"
    )

def load_agent_data():
    """Load agent data from the database"""
    trace_processor = get_trace_processor()
    cursor = trace_processor.connection.cursor()
    
    # Simple query to get just the basic data
    cursor.execute("""
        SELECT DISTINCT 
            agent_name,
            system_instructions,
            started_at
        FROM policy_aide.spans 
        WHERE system_instructions IS NOT NULL
        ORDER BY started_at DESC
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} rows with instructions")
    for row in results:
        print(f"Agent: {row[0]}, Instructions length: {len(row[1]) if row[1] else 0}")
    
    if not results:
        # If no results, let's check if we have any spans at all
        cursor.execute("SELECT COUNT(*) FROM policy_aide.spans")
        total_spans = cursor.fetchone()[0]
        print(f"Total spans in database: {total_spans}")
        
        # And check how many have system instructions
        cursor.execute("SELECT COUNT(*) FROM policy_aide.spans WHERE system_instructions IS NOT NULL")
        spans_with_instructions = cursor.fetchone()[0]
        print(f"Spans with instructions: {spans_with_instructions}")
    
    return pd.DataFrame(results, columns=[
        'agent_name', 'system_instructions', 'started_at'
    ])

def load_performance_metrics():
    """Load performance metrics from the database"""
    trace_processor = get_trace_processor()
    cursor = trace_processor.connection.cursor()
    
    # Get performance metrics per agent
    cursor.execute("""
        SELECT 
            agent_name,
            COUNT(*) as total_runs,
            AVG(CAST(tokens_used->>'total_tokens' AS INTEGER)) as avg_tokens,
            AVG(duration_ms) as avg_duration_ms,
            COUNT(DISTINCT trace_id) as unique_traces
        FROM policy_aide.spans
        GROUP BY agent_name
        ORDER BY total_runs DESC
    """)
    
    results = cursor.fetchall()
    return pd.DataFrame(results, columns=[
        'agent_name', 'total_runs', 'avg_tokens', 
        'avg_duration_ms', 'unique_traces'
    ])

def save_instructions(agent_name: str, instructions: str) -> bool:
    """Save new instructions for an agent to the database"""
    if not instructions.strip():
        return False
        
    trace_processor = get_trace_processor()
    cursor = trace_processor.connection.cursor()
    
    try:
        # Create a new default span with these instructions
        cursor.execute("""
            INSERT INTO policy_aide.spans
            (span_id, trace_id, agent_name, span_type, system_instructions, started_at, ended_at)
            VALUES
            (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            f"instruction_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            f"instruction_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_name,
            'instruction_update',
            instructions
        ))
        trace_processor.connection.commit()
        return True
    except Exception as e:
        print(f"Error saving instructions: {e}")
        return False

def display_agent_instructions(df):
    """Display and allow editing of agent instructions"""
    st.header("Agent Instructions")
    
    if df.empty:
        st.warning("No agent data found in the database.")
        return
        
    # Display raw data for debugging
    st.subheader("Raw Data")
    st.dataframe(df)
    
    # Group by agent name
    for agent in df['agent_name'].unique():
        st.subheader(f"📋 {agent}")
        agent_data = df[df['agent_name'] == agent]
        
        # Display current instructions
        if pd.isna(agent_data['system_instructions'].iloc[0]):
            st.info("No instructions set")
        else:
            st.code(agent_data['system_instructions'].iloc[0], language="markdown")
            st.caption(f"Last used: {agent_data['started_at'].iloc[0]}")
        
        # Add new instructions
        with st.expander("Update Instructions"):
            new_instructions = st.text_area(
                "New instructions", 
                value=agent_data['system_instructions'].iloc[0] if not pd.isna(agent_data['system_instructions'].iloc[0]) else "",
                key=f"new_{agent}",
                height=200
            )
            
            if st.button("Save New Instructions", key=f"save_{agent}", type="primary"):
                if save_instructions(agent, new_instructions):
                    st.success("Instructions saved! They will be used in the next run.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to save instructions. Please try again.")

def display_performance_metrics(df):
    """Display performance metrics and visualizations"""
    st.header("Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Token usage by agent
        fig = px.bar(
            df,
            x='agent_name',
            y='avg_tokens',
            title='Average Token Usage by Agent',
            labels={'agent_name': 'Agent', 'avg_tokens': 'Average Tokens'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Duration by agent
        fig = px.bar(
            df,
            x='agent_name',
            y='avg_duration_ms',
            title='Average Duration by Agent (ms)',
            labels={'agent_name': 'Agent', 'avg_duration_ms': 'Average Duration (ms)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed metrics table
    st.subheader("Detailed Metrics")
    st.dataframe(df)

def display_trace_viewer():
    """Display recent traces and their details"""
    st.header("Recent Traces")
    
    trace_processor = get_trace_processor()
    cursor = trace_processor.connection.cursor()
    
    # Get recent traces
    cursor.execute("""
        SELECT 
            t.trace_id,
            t.policy_query,
            t.policy_type,
            t.created_at,
            t.agent_count,
            t.total_duration_ms,
            COUNT(s.span_id) as span_count,
            SUM(CAST(s.tokens_used->>'total_tokens' AS INTEGER)) as total_tokens
        FROM policy_aide.traces t
        LEFT JOIN policy_aide.spans s ON t.trace_id = s.trace_id
        GROUP BY t.trace_id, t.policy_query, t.policy_type, t.created_at, t.agent_count, t.total_duration_ms
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    
    traces = cursor.fetchall()
    if not traces:
        st.info("No traces found")
        return
        
    # Create trace selector
    trace_options = [f"{t[1][:100]}... ({t[0]})" for t in traces]
    selected_trace = st.selectbox("Select a trace to view", trace_options)
    selected_idx = trace_options.index(selected_trace)
    trace = traces[selected_idx]
    
    # Show trace details
    st.subheader("Trace Details")
    cols = st.columns(4)
    cols[0].metric("Policy Type", trace[2])
    cols[1].metric("Agent Count", trace[4])
    cols[2].metric("Total Duration", f"{trace[5]/1000:.2f}s")
    cols[3].metric("Total Tokens", trace[7])
    
    # Get spans for this trace
    cursor.execute("""
        SELECT 
            span_id,
            agent_name,
            span_type,
            system_instructions,
            input_text,
            output_text,
            tokens_used
        FROM policy_aide.spans
        WHERE trace_id = %s
        ORDER BY started_at
    """, (trace[0],))
    
    spans = cursor.fetchall()
    if spans:
        st.subheader("Spans")
        
        # Group spans by agent
        spans_by_agent = {}
        for span in spans:
            if span[1] not in spans_by_agent:  # agent_name
                spans_by_agent[span[1]] = []
            spans_by_agent[span[1]].append(span)
        
        # Create tabs for each agent
        agent_tabs = st.tabs(list(spans_by_agent.keys()))
        for agent_tab, (agent_name, agent_spans) in zip(agent_tabs, spans_by_agent.items()):
            with agent_tab:
                for span in agent_spans:
                    st.markdown(f"**Span Type:** {span[2]}")
                    
                    if span[3]:  # system_instructions
                        st.markdown("**System Instructions:**")
                        st.code(span[3])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Input:**")
                        st.text(span[4] if span[4] else "No input")
                    with col2:
                        st.markdown("**Output:**")
                        st.text(span[5] if span[5] else "No output")
                    
                    if span[6]:  # tokens_used
                        st.metric("Tokens Used", json.loads(span[6]).get('total_tokens', 0))
                    
                    st.divider()

def main():
    """Main function for the control room interface"""
    init_page()
    
    # Navigation inside main content area instead of sidebar
    st.title("🎛️ CivicAide Control Room")
    
    # Create tabs for navigation instead of sidebar radio buttons
    tab1, tab2, tab3 = st.tabs(["Instructions", "Performance", "Trace Viewer"])
    
    # Load data
    agent_data = load_agent_data()
    performance_data = load_performance_metrics()
    
    # Display selected page in appropriate tab
    with tab1:  # Instructions
        display_agent_instructions(agent_data)
    
    with tab2:  # Performance
        display_performance_metrics(performance_data)
    
    with tab3:  # Trace Viewer
        display_trace_viewer()
    
    # Footer
    st.markdown("---")
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main() 