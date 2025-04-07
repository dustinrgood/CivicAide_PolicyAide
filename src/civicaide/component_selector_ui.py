"""
CivicAide Component Selector UI

A Streamlit interface for helping users choose the right policy component.
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our component selector
from src.civicaide.component_selector import (
    ComponentSelector, UserProfile, PolicyNeed,
    UserExpertise, TimeAvailable, ComponentType
)

def main():
    """Create the Streamlit UI for component selection."""
    st.set_page_config(
        page_title="CivicAide - Component Selector",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("CivicAide Component Selector")
    st.write("""
    Not sure which policy component to use? This tool will help you select the most appropriate 
    component based on your needs and constraints.
    """)
    
    # Initialize the component selector
    selector = ComponentSelector()
    
    # Create two columns for the UI
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.header("Your requirements")
        
        # 1. Policy development needs
        st.subheader("Policy Development Needs")
        st.write("What are you trying to accomplish? (Select all that apply)")
        
        needs_options = {
            PolicyNeed.BACKGROUND_RESEARCH: "Gather information and research about a policy topic",
            PolicyNeed.GENERATE_OPTIONS: "Generate different policy options or approaches",
            PolicyNeed.EVALUATE_OPTIONS: "Evaluate and compare different policy options",
            PolicyNeed.LOCAL_CONTEXT: "Understand my local context and how it affects policy",
            PolicyNeed.STAKEHOLDER_ANALYSIS: "Analyze impacts on different stakeholders",
            PolicyNeed.IMPLEMENTATION_PLAN: "Develop an implementation plan",
            PolicyNeed.COMPREHENSIVE_SOLUTION: "Create a complete, well-considered policy",
            PolicyNeed.REFINEMENT: "Refine and improve an existing policy idea",
            PolicyNeed.EVOLUTION: "Evolve policies through multiple iterations"
        }
        
        selected_needs = []
        for need, description in needs_options.items():
            if st.checkbox(description, key=f"need_{need.name}"):
                selected_needs.append(need)
        
        if not selected_needs:
            st.warning("Please select at least one policy development need.")
        
        # 2. User expertise
        st.subheader("Your Expertise Level")
        expertise_level = st.radio(
            "What is your level of expertise with policy development?",
            [
                ("Novice - I'm new to policy development", UserExpertise.NOVICE),
                ("Intermediate - I have some experience", UserExpertise.INTERMEDIATE),
                ("Expert - I have extensive experience", UserExpertise.EXPERT)
            ],
            format_func=lambda x: x[0]
        )[1]
        
        # 3. Time available
        st.subheader("Time Available")
        time_available = st.radio(
            "How much time do you have available for this policy work?",
            [
                ("Quick - Under 10 minutes", TimeAvailable.QUICK),
                ("Medium - 10-30 minutes", TimeAvailable.MEDIUM),
                ("Extensive - 30+ minutes", TimeAvailable.EXTENSIVE)
            ],
            format_func=lambda x: x[0]
        )[1]
        
        # 4. Additional context
        st.subheader("Additional Information")
        has_local_context = st.checkbox("I already have detailed information about my local context")
        has_research = st.checkbox("I have already gathered research on this policy topic")
        
        # Create profile and get recommendations when the user clicks the button
        if st.button("Get Recommendation", disabled=len(selected_needs) == 0):
            # Create user profile
            profile = UserProfile(
                primary_needs=selected_needs,
                expertise_level=expertise_level,
                time_available=time_available,
                has_local_context=has_local_context,
                has_research=has_research
            )
            
            # Store in session state so it persists across reruns
            st.session_state.profile = profile
            st.session_state.recommendation = selector.recommend_component(profile)
    
    # Display recommendation if available
    with col2:
        if 'recommendation' in st.session_state:
            recommendation = st.session_state.recommendation
            component_type = recommendation.component_type
            component_details = selector.get_component_description(component_type)
            
            st.header("Recommended Component")
            
            # Component name and description with confidence score
            st.markdown(f"""
            ### {component_details['name']}
            *Confidence score: {recommendation.confidence:.0%}*
            
            {component_details['description']}
            """)
            
            # Display reasons for recommendation
            st.subheader("Why this component is recommended")
            for reason in recommendation.reasons:
                st.markdown(f"✅ {reason}")
            
            # Display limitations if any
            if recommendation.limitations:
                st.subheader("Limitations to consider")
                for limitation in recommendation.limitations:
                    st.markdown(f"⚠️ {limitation}")
            
            # Display next steps
            st.subheader("Next steps")
            for i, step in enumerate(recommendation.next_steps, 1):
                st.markdown(f"{i}. {step}")
            
            # Component-specific action button
            st.markdown("---")
            if component_type == ComponentType.RESEARCH:
                if st.button("Start Policy Research"):
                    st.session_state.redirect = "research"
                    
            elif component_type == ComponentType.ANALYSIS:
                if st.button("Start Policy Analysis"):
                    st.session_state.redirect = "analysis"
                    
            elif component_type == ComponentType.EVOLUTION:
                if st.button("Start Policy Evolution"):
                    st.session_state.redirect = "evolution"
                    
            elif component_type == ComponentType.INTEGRATED:
                if st.button("Start Integrated Policy Process"):
                    st.session_state.redirect = "integrated"
                    
            elif component_type == ComponentType.CONTEXT:
                if st.button("Start Context Gathering"):
                    st.session_state.redirect = "context"
            
            # Handle redirections
            if 'redirect' in st.session_state:
                if st.session_state.redirect == "research":
                    st.info("Redirecting to Policy Research...")
                    # In a real app, this would redirect to the research page
                
                elif st.session_state.redirect == "analysis":
                    st.info("Redirecting to Policy Analysis...")
                    # In a real app, this would redirect to the analysis page
                
                elif st.session_state.redirect == "evolution":
                    st.info("Redirecting to Policy Evolution...")
                    # In a real app, this would redirect to the evolution page
                
                elif st.session_state.redirect == "integrated":
                    st.info("Redirecting to Integrated Policy Process...")
                    # In a real app, this would redirect to the integrated system page
                
                elif st.session_state.redirect == "context":
                    st.info("Redirecting to Context Gathering...")
                    # In a real app, this would redirect to the context gathering page
                
                # Clear the redirect flag to prevent infinite loops
                st.session_state.redirect = None
        else:
            # Display initial information about components
            st.header("Available Components")
            st.write("Select your requirements to get a personalized recommendation.")
            
            # Component summaries
            with st.expander("Policy Research"):
                st.write("""
                **Best for:** Learning about existing approaches, precedents, and evidence around a policy issue.
                
                **How it works:** Plans searches, performs web searches on relevant topics, and synthesizes 
                findings into structured research data.
                
                **When to use:** When you need to gather background information or understand what others have done.
                """)
            
            with st.expander("Policy Analysis"):
                st.write("""
                **Best for:** Quick policy analysis when you already understand the background/context.
                
                **How it works:** Generates initial policy proposals, evaluates and ranks them,
                uses a "judge" agent to select the best proposal, refines the winning proposal,
                and creates a final report.
                
                **When to use:** When you need to generate and evaluate multiple policy options quickly.
                """)
            
            with st.expander("Policy Evolution"):
                st.write("""
                **Best for:** Creating highly customized, well-considered policies for specific local contexts.
                
                **How it works:** Gathers local context information, conducts web research,
                generates initial proposals, uses tournament-style competition to evaluate proposals,
                evolves top proposals across multiple generations, and creates a comprehensive final report.
                
                **When to use:** When you need sophisticated, highly refined policy recommendations.
                """)
            
            with st.expander("Integrated Policy System"):
                st.write("""
                **Best for:** End-to-end policy development when starting from scratch.
                
                **How it works:** Combines research and analysis into a single workflow,
                conducts research first, then feeds findings into the analysis component.
                
                **When to use:** When you want a complete process from research to concrete recommendations.
                """)
                
            with st.expander("Context Gathering"):
                st.write("""
                **Best for:** Understanding local demographic, economic, and governmental factors.
                
                **How it works:** Automatically gathers information about your jurisdiction using web searches
                and structured data sources, creating a profile that can inform policy development.
                
                **When to use:** When you need to understand how local factors affect policy implementation.
                """)

if __name__ == "__main__":
    main() 