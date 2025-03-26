import streamlit as st
import importlib
import os
import sys

# Add the source directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config
st.set_page_config(
    page_title="CivicAide PolicyAide",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for navigation
st.markdown("""
<style>
    .nav-button {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .nav-button:hover {
        background-color: #e0e2e6;
    }
    .nav-button.active {
        background-color: #4e8df5;
        color: white;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .stApp header {
        background-color: rgba(0, 0, 0, 0);
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# Function to handle page navigation
def navigate_to(page):
    st.session_state.current_page = page
    # Force a rerun to update the UI
    st.rerun()

# Sidebar navigation
st.sidebar.title("CivicAide PolicyAide")
st.sidebar.image("https://img.icons8.com/color/96/000000/government.png", width=100)

# Navigation options
nav_options = [
    {'name': 'Home', 'icon': '🏠'},
    {'name': 'Profile', 'icon': '👤'},
    {'name': 'Policy Dashboard', 'icon': '📊'},
    {'name': 'Traces Dashboard', 'icon': '🔍'},
    {'name': 'Policy Analysis', 'icon': '📝'},
    {'name': 'Policy Research', 'icon': '🔬'},
    {'name': 'Policy Evolution', 'icon': '🔄'}
]

# Display navigation buttons in sidebar
for option in nav_options:
    button_class = "nav-button active" if st.session_state.current_page == option['name'] else "nav-button"
    if st.sidebar.markdown(f"""
        <div class="{button_class}" onclick="parent.window.location.href='?page={option['name'].replace(' ', '')}'">{option['icon']} {option['name']}</div>
        """, unsafe_allow_html=True):
        navigate_to(option['name'])

# Check URL parameters for direct navigation
query_params = st.experimental_get_query_params()
if 'page' in query_params:
    page_name = query_params['page'][0]
    # Convert snake_case or camelCase to title case for matching
    page_title = ' '.join(word.capitalize() for word in page_name.replace('_', ' ').split())
    
    # Find matching page in nav_options
    matching_pages = [opt['name'] for opt in nav_options if opt['name'].lower().replace(' ', '') == page_title.lower().replace(' ', '')]
    if matching_pages:
        st.session_state.current_page = matching_pages[0]

# Main content container
main_container = st.container()

with main_container:
    # Display the current page based on navigation state
    if st.session_state.current_page == 'Home':
        st.title("Welcome to CivicAide PolicyAide")
        st.markdown("""
        CivicAide PolicyAide is a comprehensive policy analysis and development tool designed for local governments.
        
        ### Key Features:
        - **Policy Analysis**: Analyze proposed policies and their potential impacts
        - **Community Profiles**: Maintain profiles of your jurisdiction for context-aware recommendations
        - **Interactive Dashboards**: Visualize policy impacts and stakeholder concerns
        - **AI-Powered Research**: Leverage AI to research policy options and best practices
        - **Trace Visualization**: Understand how AI agents contribute to policy analysis
        
        Get started by navigating to one of the sections using the sidebar.
        """)
        
        # Quick access cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px; height: 150px; text-align: center;">
                <h3>Create Profile</h3>
                <p>Set up your jurisdiction profile to get started</p>
                <div style="background-color: #4e8df5; color: white; padding: 8px; border-radius: 5px; cursor: pointer;" onclick="parent.window.location.href='?page=Profile'">Go to Profile</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px; height: 150px; text-align: center;">
                <h3>Policy Dashboard</h3>
                <p>View and analyze policy reports</p>
                <div style="background-color: #4e8df5; color: white; padding: 8px; border-radius: 5px; cursor: pointer;" onclick="parent.window.location.href='?page=PolicyDashboard'">Go to Dashboard</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 5px; height: 150px; text-align: center;">
                <h3>Analyze New Policy</h3>
                <p>Start a new policy analysis</p>
                <div style="background-color: #4e8df5; color: white; padding: 8px; border-radius: 5px; cursor: pointer;" onclick="parent.window.location.href='?page=PolicyAnalysis'">Create Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            
    elif st.session_state.current_page == 'Profile':
        # Import and run the profile page module
        try:
            from src.civicaide.profile_page import main as profile_main
            profile_main()
        except Exception as e:
            st.error(f"Error loading Profile page: {str(e)}")
    
    elif st.session_state.current_page == 'Policy Dashboard':
        # Import and run the policy dashboard module directly
        try:
            # We don't call main() here because the policy_dashboard.py script runs directly
            import src.civicaide.policy_dashboard
        except Exception as e:
            st.error(f"Error loading Policy Dashboard: {str(e)}")
    
    elif st.session_state.current_page == 'Traces Dashboard':
        # Import and run the trace dashboard module
        try:
            from src.civicaide.trace_dashboard import main as trace_main
            trace_main()
        except Exception as e:
            st.error(f"Error loading Traces Dashboard: {str(e)}")
    
    elif st.session_state.current_page == 'Policy Analysis':
        # Import and run the policy analysis module
        try:
            from src.civicaide.policy_analysis import main as analysis_main
            analysis_main()
        except Exception as e:
            st.error(f"Error loading Policy Analysis: {str(e)}")
    
    elif st.session_state.current_page == 'Policy Research':
        # Import and run the policy research module
        try:
            from src.civicaide.policy_research import main as research_main
            research_main()
        except Exception as e:
            st.error(f"Error loading Policy Research: {str(e)}")
    
    elif st.session_state.current_page == 'Policy Evolution':
        # Import and run the policy evolution module
        try:
            from src.civicaide.policy_evolution import main as evolution_main
            evolution_main()
        except Exception as e:
            st.error(f"Error loading Policy Evolution: {str(e)}")

# Footer
st.markdown("---")
st.caption("© 2025 CivicAide PolicyAide | AI-Powered Policy Analysis for Local Government")

# Add a simple way to report issues
with st.expander("Report an Issue"):
    st.write("If you encounter any issues with the application, please provide details below:")
    issue_description = st.text_area("Issue Description")
    if st.button("Submit Issue"):
        # In a real app, this would save to a database or send an email
        st.success("Thank you for reporting the issue. We'll look into it.") 