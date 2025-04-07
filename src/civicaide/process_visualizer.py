"""
Process Visualizer for CivicAide

This module provides visualizations of the policy process stages for each component,
helping users understand the workflow and track progress.
"""

import os
import sys
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import numpy as np

# Process stage definitions

@dataclass
class ProcessStage:
    """A stage in a policy process."""
    id: str
    name: str
    description: str
    estimated_time: str  # e.g., "5-10 minutes"
    status: str = "pending"  # pending, in_progress, completed, error
    output: Optional[Any] = None
    
    @property
    def status_color(self) -> str:
        """Get the color for this status."""
        colors = {
            "pending": "#CCCCCC",  # gray
            "in_progress": "#FFD700",  # gold
            "completed": "#4CAF50",  # green
            "error": "#F44336"  # red
        }
        return colors.get(self.status, "#CCCCCC")

@dataclass
class PolicyProcess:
    """A policy process workflow with multiple stages."""
    name: str
    description: str
    stages: List[ProcessStage]
    current_stage_id: Optional[str] = None
    
    def get_stage_by_id(self, stage_id: str) -> Optional[ProcessStage]:
        """Get a stage by its ID."""
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None
    
    def update_stage_status(self, stage_id: str, status: str, output: Any = None) -> None:
        """Update the status of a stage."""
        stage = self.get_stage_by_id(stage_id)
        if stage:
            stage.status = status
            if output is not None:
                stage.output = output
    
    def set_current_stage(self, stage_id: str) -> None:
        """Set the current active stage."""
        self.current_stage_id = stage_id
        # Update the status of the current stage to in_progress
        self.update_stage_status(stage_id, "in_progress")
    
    def get_next_stage(self) -> Optional[ProcessStage]:
        """Get the next stage after the current one."""
        if not self.current_stage_id:
            return self.stages[0] if self.stages else None
        
        for i, stage in enumerate(self.stages):
            if stage.id == self.current_stage_id and i < len(self.stages) - 1:
                return self.stages[i + 1]
        
        return None
    
    def advance_to_next_stage(self) -> Optional[ProcessStage]:
        """Mark the current stage as completed and advance to the next stage."""
        if not self.current_stage_id:
            if self.stages:
                self.set_current_stage(self.stages[0].id)
                return self.stages[0]
            return None
        
        # Mark current stage as completed
        current_stage = self.get_stage_by_id(self.current_stage_id)
        if current_stage:
            self.update_stage_status(current_stage.id, "completed")
        
        # Move to next stage
        next_stage = self.get_next_stage()
        if next_stage:
            self.set_current_stage(next_stage.id)
            return next_stage
        
        return None
    
    def get_progress_percentage(self) -> float:
        """Get the percentage of completed stages."""
        if not self.stages:
            return 0.0
        
        completed_count = sum(1 for stage in self.stages if stage.status == "completed")
        return (completed_count / len(self.stages)) * 100.0

# Process definitions for each component type

def get_research_process() -> PolicyProcess:
    """Get the policy research process definition."""
    return PolicyProcess(
        name="Policy Research",
        description="Gather evidence and information about a policy topic",
        stages=[
            ProcessStage(
                id="plan",
                name="Research Planning",
                description="Identify key questions and information needs",
                estimated_time="1-2 minutes"
            ),
            ProcessStage(
                id="search",
                name="Web Research",
                description="Search for relevant information from multiple sources",
                estimated_time="3-5 minutes"
            ),
            ProcessStage(
                id="synthesize",
                name="Synthesis",
                description="Organize findings into structured research data",
                estimated_time="2-3 minutes"
            ),
            ProcessStage(
                id="output",
                name="Final Summary",
                description="Produce a cohesive summary of research findings",
                estimated_time="1-2 minutes"
            )
        ]
    )

def get_analysis_process() -> PolicyProcess:
    """Get the policy analysis process definition."""
    return PolicyProcess(
        name="Policy Analysis",
        description="Generate, evaluate, and refine policy proposals",
        stages=[
            ProcessStage(
                id="generate",
                name="Proposal Generation",
                description="Generate multiple policy approaches",
                estimated_time="2-4 minutes"
            ),
            ProcessStage(
                id="evaluate",
                name="Proposal Evaluation",
                description="Evaluate and score each proposal",
                estimated_time="2-3 minutes"
            ),
            ProcessStage(
                id="judge",
                name="Proposal Selection",
                description="Select the best proposal based on evaluation",
                estimated_time="1-2 minutes"
            ),
            ProcessStage(
                id="refine",
                name="Proposal Refinement",
                description="Refine and improve the selected proposal",
                estimated_time="2-3 minutes"
            ),
            ProcessStage(
                id="report",
                name="Final Report",
                description="Create a comprehensive policy report",
                estimated_time="2-3 minutes"
            )
        ]
    )

def get_evolution_process() -> PolicyProcess:
    """Get the policy evolution process definition."""
    return PolicyProcess(
        name="Policy Evolution",
        description="Create better policy proposals through competition and iteration",
        stages=[
            ProcessStage(
                id="context",
                name="Context Analysis",
                description="Gather information about local context",
                estimated_time="3-5 minutes"
            ),
            ProcessStage(
                id="research",
                name="Background Research",
                description="Gather relevant policy research",
                estimated_time="4-6 minutes"
            ),
            ProcessStage(
                id="initial",
                name="Initial Proposals",
                description="Generate diverse initial policy proposals",
                estimated_time="3-5 minutes"
            ),
            ProcessStage(
                id="tournament",
                name="Proposal Tournament",
                description="Evaluate proposals through head-to-head comparison",
                estimated_time="5-7 minutes"
            ),
            ProcessStage(
                id="evolution",
                name="Policy Evolution",
                description="Evolve top proposals to create improved versions",
                estimated_time="4-6 minutes"
            ),
            ProcessStage(
                id="final_tournament",
                name="Final Evaluation",
                description="Evaluate evolved proposals to select the best",
                estimated_time="3-5 minutes"
            ),
            ProcessStage(
                id="report",
                name="Comprehensive Report",
                description="Create detailed final policy report",
                estimated_time="3-5 minutes"
            )
        ]
    )

def get_integrated_process() -> PolicyProcess:
    """Get the integrated policy process definition."""
    return PolicyProcess(
        name="Integrated Policy System",
        description="Combines research and analysis into a single workflow",
        stages=[
            ProcessStage(
                id="research_plan",
                name="Research Planning",
                description="Plan the policy research approach",
                estimated_time="1-2 minutes"
            ),
            ProcessStage(
                id="research",
                name="Policy Research",
                description="Conduct research on the policy topic",
                estimated_time="5-8 minutes"
            ),
            ProcessStage(
                id="generate",
                name="Proposal Generation",
                description="Generate policy proposals based on research",
                estimated_time="3-5 minutes"
            ),
            ProcessStage(
                id="evaluate",
                name="Proposal Evaluation",
                description="Evaluate proposals using research insights",
                estimated_time="3-4 minutes"
            ),
            ProcessStage(
                id="refine",
                name="Proposal Refinement",
                description="Refine the best policy proposal",
                estimated_time="3-4 minutes"
            ),
            ProcessStage(
                id="report",
                name="Integrated Report",
                description="Create comprehensive report with research and recommendations",
                estimated_time="3-4 minutes"
            )
        ]
    )

def get_context_gathering_process() -> PolicyProcess:
    """Get the context gathering process definition."""
    return PolicyProcess(
        name="Context Gathering",
        description="Gather local context data to inform policy development",
        stages=[
            ProcessStage(
                id="location",
                name="Location Setup",
                description="Define the jurisdiction information",
                estimated_time="1 minute"
            ),
            ProcessStage(
                id="demographics",
                name="Demographic Research",
                description="Gather demographic data about the location",
                estimated_time="2-4 minutes"
            ),
            ProcessStage(
                id="economic",
                name="Economic Research",
                description="Gather economic information about the location",
                estimated_time="2-4 minutes"
            ),
            ProcessStage(
                id="government",
                name="Government Research",
                description="Research the local government structure",
                estimated_time="2-4 minutes"
            ),
            ProcessStage(
                id="profile",
                name="Profile Creation",
                description="Create a comprehensive jurisdiction profile",
                estimated_time="1-2 minutes"
            )
        ]
    )

# Process factory function

def get_process_by_type(process_type: str) -> Optional[PolicyProcess]:
    """Get a process definition by type."""
    process_map = {
        "research": get_research_process(),
        "analysis": get_analysis_process(),
        "evolution": get_evolution_process(),
        "integrated": get_integrated_process(),
        "context": get_context_gathering_process()
    }
    return process_map.get(process_type.lower())

# Visualization functions

def render_process_streamlit(process: PolicyProcess, show_descriptions: bool = True) -> None:
    """
    Render a policy process visualization in Streamlit.
    
    Args:
        process: The policy process to visualize
        show_descriptions: Whether to show stage descriptions
    """
    st.subheader(f"Process: {process.name}")
    
    # Progress bar for overall progress
    progress = process.get_progress_percentage() / 100.0
    st.progress(progress)
    st.write(f"Overall Progress: {progress:.0%}")
    
    # Display process stages
    for i, stage in enumerate(process.stages):
        stage_active = process.current_stage_id == stage.id
        
        # Create a visual indicator of status
        if stage.status == "completed":
            stage_icon = "✅"
        elif stage.status == "in_progress":
            stage_icon = "🔄"
        elif stage.status == "error":
            stage_icon = "❌"
        else:
            stage_icon = "⬜"
        
        # Create a container for each stage
        with st.container():
            cols = st.columns([1, 5, 2])
            
            # Column 1: Stage number and status icon
            with cols[0]:
                st.markdown(f"### {i+1}. {stage_icon}")
            
            # Column 2: Stage details
            with cols[1]:
                if stage_active:
                    st.markdown(f"**{stage.name}** *(Current Stage)*")
                else:
                    st.markdown(f"**{stage.name}**")
                    
                if show_descriptions:
                    st.markdown(stage.description)
            
            # Column 3: Time estimate and status
            with cols[2]:
                st.markdown(f"*Est. time: {stage.estimated_time}*")
                st.markdown(f"Status: **{stage.status.replace('_', ' ').title()}**")
            
            # Show output if available
            if stage.output and stage.status == "completed":
                with st.expander("View Output"):
                    st.write(stage.output)
            
            # Add a separator between stages
            if i < len(process.stages) - 1:
                st.markdown("---")

def render_process_as_graph(process: PolicyProcess) -> plt.Figure:
    """
    Render a policy process as a directed graph using NetworkX.
    
    Args:
        process: The policy process to visualize
        
    Returns:
        A matplotlib figure with the visualization
    """
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes for each stage
    for i, stage in enumerate(process.stages):
        G.add_node(stage.id, 
                  name=stage.name, 
                  status=stage.status,
                  pos=(i, 0))  # Position nodes horizontally
    
    # Add edges between consecutive stages
    for i in range(len(process.stages) - 1):
        G.add_edge(process.stages[i].id, process.stages[i+1].id)
    
    # Create a figure
    fig, ax = plt.subplots(figsize=(12, 3))
    
    # Get node positions
    pos = nx.get_node_attributes(G, 'pos')
    
    # Get node colors based on status
    node_colors = [get_stage_by_id(G, node).status_color for node in G.nodes()]
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, ax=ax)
    nx.draw_networkx_edges(G, pos, arrowsize=20, width=2, edge_color='gray', ax=ax)
    
    # Add labels
    labels = nx.get_node_attributes(G, 'name')
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, ax=ax)
    
    # Highlight current stage
    if process.current_stage_id:
        current_stage_pos = pos[process.current_stage_id]
        circle = plt.Circle(current_stage_pos, 0.15, color='gold', fill=False, linewidth=3)
        ax.add_patch(circle)
    
    # Remove axis
    plt.axis('off')
    
    return fig

def get_stage_by_id(graph: nx.DiGraph, node_id: str) -> ProcessStage:
    """
    Helper function to get a process stage for a node in the graph.
    
    Args:
        graph: The NetworkX graph
        node_id: The ID of the node
        
    Returns:
        A ProcessStage with the corresponding status color
    """
    # Get the node status
    status = graph.nodes[node_id].get('status', 'pending')
    
    # Create a minimal ProcessStage just to get the color
    stage = ProcessStage(
        id=node_id,
        name="",
        description="",
        estimated_time="",
        status=status
    )
    
    return stage

# UI Components for Streamlit

def display_process_info(process_type: str) -> None:
    """
    Display information about a process in Streamlit.
    
    Args:
        process_type: The type of process to display
    """
    process = get_process_by_type(process_type)
    if not process:
        st.error(f"Unknown process type: {process_type}")
        return
    
    # Display process information
    st.title(process.name)
    st.write(process.description)
    
    # Display process visualization
    render_process_streamlit(process)
    
    # Show total estimated time
    min_time = sum(int(stage.estimated_time.split('-')[0].split()[0]) for stage in process.stages)
    max_time = sum(int(stage.estimated_time.split('-')[-1].split()[0]) if '-' in stage.estimated_time 
                   else int(stage.estimated_time.split()[0]) for stage in process.stages)
    
    st.write(f"Total estimated time: {min_time}-{max_time} minutes")

def interactive_process_demo(process_type: str) -> None:
    """
    Create an interactive demo of a process in Streamlit.
    
    Args:
        process_type: The type of process to demonstrate
    """
    # Initialize the process in session state if it doesn't exist
    if 'demo_process' not in st.session_state:
        st.session_state.demo_process = get_process_by_type(process_type)
        
        # Set the first stage as current
        process = st.session_state.demo_process
        if process and process.stages:
            process.set_current_stage(process.stages[0].id)
    
    process = st.session_state.demo_process
    
    # Display process visualization
    render_process_streamlit(process)
    
    # Get the current stage
    current_stage = None
    if process.current_stage_id:
        current_stage = process.get_stage_by_id(process.current_stage_id)
    
    # Display current stage details if available
    if current_stage:
        st.subheader(f"Current Stage: {current_stage.name}")
        st.write(current_stage.description)
        
        # Simulate working on this stage
        if st.button("Complete This Stage"):
            # Mark stage as completed and advance
            next_stage = process.advance_to_next_stage()
            
            if next_stage:
                st.success(f"Advanced to next stage: {next_stage.name}")
            else:
                st.success("Process completed!")
                # Reset the process if desired
                if st.button("Restart Process"):
                    st.session_state.demo_process = get_process_by_type(process_type)
                    process = st.session_state.demo_process
                    if process and process.stages:
                        process.set_current_stage(process.stages[0].id)
            
            # Force a rerun to update the UI
            st.experimental_rerun()
    else:
        st.write("No active stage. Process may be complete or not started.")

def main():
    """Streamlit application entry point."""
    st.set_page_config(
        page_title="CivicAide - Process Visualizer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("CivicAide Process Visualizer")
    st.write("""
    This tool shows the stages involved in each policy component, 
    helping you understand the workflow and track progress.
    """)
    
    # Process selection
    process_options = {
        "research": "Policy Research",
        "analysis": "Policy Analysis", 
        "evolution": "Policy Evolution",
        "integrated": "Integrated Policy System",
        "context": "Context Gathering"
    }
    
    process_type = st.selectbox(
        "Select a process to visualize:",
        options=list(process_options.keys()),
        format_func=lambda x: process_options[x]
    )
    
    # Show either info or interactive demo
    mode = st.radio(
        "Display mode:",
        ["Process Information", "Interactive Demo"]
    )
    
    if mode == "Process Information":
        display_process_info(process_type)
    else:
        interactive_process_demo(process_type)

if __name__ == "__main__":
    main() 