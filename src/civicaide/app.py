import streamlit as st
import importlib
import os
import sys
import traceback
import json
import glob
from importlib import import_module

# Add the source directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variable to prevent imported modules from creating their own page config
os.environ["STREAMLIT_RUN_VIA_APP"] = "true"

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
    /* Ensure content stretches to full width */
    .css-1d391kg, .css-1r6slb0, .css-18e3th9, 
    .css-1fbsrjo, .stMarkdown, .css-1544g2n {
        width: 100% !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
    /* Hide loading messages */
    .stMarkdown p:contains("Loading") {
        display: none !important;
    }
    /* Style width selector buttons */
    .width-button-selected {
        background-color: #4e8df5 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# Function to handle page navigation
def navigate_to(page):
    st.session_state.current_page = page
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
    {'name': 'Policy Evolution', 'icon': '🔄'},
    {'name': 'Control Room', 'icon': '🎛️'}
]

# Display navigation buttons in sidebar using clickable buttons instead of markdown
for option in nav_options:
    button_label = f"{option['icon']} {option['name']}"
    if st.sidebar.button(button_label, key=f"nav_{option['name']}"):
        st.session_state.current_page = option['name']
        st.rerun()

# Page width settings
st.sidebar.markdown("---")
st.sidebar.subheader("Page Settings")

# Initialize page width in session state if not present
if 'page_width' not in st.session_state:
    st.session_state.page_width = "wide"  # Default to wide

# Create page width selector
st.sidebar.markdown("""
<style>
    .width-option {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 8px;
        text-align: center;
        cursor: pointer;
        margin: 2px;
    }
    .width-option:hover {
        border-color: #4e8df5;
    }
    .width-selected {
        border: 2px solid #4e8df5;
        background-color: #f0f4fc;
    }
    .width-icon {
        display: block;
        margin: 0 auto;
        background-color: #e0e0e0;
        margin-bottom: 5px;
        border-radius: 3px;
    }
    .width-text {
        font-size: 0.8rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

width_cols = st.sidebar.columns(3)

with width_cols[0]:
    narrow_selected = "width-selected" if st.session_state.page_width == "narrow" else ""
    narrow_html = f"""
    <div class="width-option {narrow_selected}" onclick="
        window.parent.postMessage({{
            'type': 'streamlit:setComponentValue',
            'value': 'narrow',
            'target': 'narrow_width'
        }}, '*')
    ">
        <div class="width-icon" style="width: 30%; height: 20px; margin: 0 auto;"></div>
        <div class="width-text">Narrow</div>
    </div>
    """
    st.markdown(narrow_html, unsafe_allow_html=True)
    st.markdown('<div style="display:none">', unsafe_allow_html=True)
    if st.text_input("narrow_width", "", key="narrow_width") == "narrow":
        st.session_state.page_width = "narrow"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with width_cols[1]:
    standard_selected = "width-selected" if st.session_state.page_width == "standard" else ""
    standard_html = f"""
    <div class="width-option {standard_selected}" onclick="
        window.parent.postMessage({{
            'type': 'streamlit:setComponentValue',
            'value': 'standard',
            'target': 'standard_width'
        }}, '*')
    ">
        <div class="width-icon" style="width: 60%; height: 20px; margin: 0 auto;"></div>
        <div class="width-text">Standard</div>
    </div>
    """
    st.markdown(standard_html, unsafe_allow_html=True)
    st.markdown('<div style="display:none">', unsafe_allow_html=True)
    if st.text_input("standard_width", "", key="standard_width") == "standard":
        st.session_state.page_width = "standard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with width_cols[2]:
    wide_selected = "width-selected" if st.session_state.page_width == "wide" else ""
    wide_html = f"""
    <div class="width-option {wide_selected}" onclick="
        window.parent.postMessage({{
            'type': 'streamlit:setComponentValue',
            'value': 'wide',
            'target': 'wide_width'
        }}, '*')
    ">
        <div class="width-icon" style="width: 90%; height: 20px; margin: 0 auto;"></div>
        <div class="width-text">Wide</div>
    </div>
    """
    st.markdown(wide_html, unsafe_allow_html=True)
    st.markdown('<div style="display:none">', unsafe_allow_html=True)
    if st.text_input("wide_width", "", key="wide_width") == "wide":
        st.session_state.page_width = "wide"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Apply the page width styles
width_styles = {
    "narrow": "max-width: 700px !important; margin-left: auto; margin-right: auto;",
    "standard": "max-width: 1000px !important; margin-left: auto; margin-right: auto;",
    "wide": "max-width: 95% !important; padding-left: 2rem; padding-right: 2rem;"
}

# Dynamic CSS based on selected width
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 2rem;
        {width_styles[st.session_state.page_width]}
    }}
</style>
""", unsafe_allow_html=True)

# Check URL parameters for direct navigation
try:
    query_params = st.query_params
    if query_params and 'page' in query_params:
        page_name = query_params['page']
        # Convert snake_case or camelCase to title case for matching
        page_title = ' '.join(word.capitalize() for word in page_name.replace('_', ' ').split())
        
        # Find matching page in nav_options
        matching_pages = [opt['name'] for opt in nav_options if opt['name'].lower().replace(' ', '') == page_title.lower().replace(' ', '')]
        if matching_pages:
            st.session_state.current_page = matching_pages[0]
except:
    # Fall back to legacy method
    try:
        query_params = st.experimental_get_query_params()
        if 'page' in query_params:
            page_name = query_params['page'][0]
            # Convert snake_case or camelCase to title case for matching
            page_title = ' '.join(word.capitalize() for word in page_name.replace('_', ' ').split())
            
            # Find matching page in nav_options
            matching_pages = [opt['name'] for opt in nav_options if opt['name'].lower().replace(' ', '') == page_title.lower().replace(' ', '')]
            if matching_pages:
                st.session_state.current_page = matching_pages[0]
    except:
        pass

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
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("### Create Profile")
            st.write("Set up your jurisdiction profile to get started")
            if st.button("Go to Profile", key="home_profile_btn"):
                st.session_state.current_page = "Profile"
                st.rerun()
            
        with col2:
            st.markdown("### Policy Dashboard")
            st.write("View and analyze policy reports")
            if st.button("Go to Dashboard", key="home_dashboard_btn"):
                st.session_state.current_page = "Policy Dashboard"
                st.rerun()
            
        with col3:
            st.markdown("### Analyze New Policy")
            st.write("Start a new policy analysis")
            if st.button("Create Analysis", key="home_analysis_btn"):
                st.session_state.current_page = "Policy Analysis"
                st.rerun()
                
        with col4:
            st.markdown("### Control Room")
            st.write("Monitor agent performance and settings")
            if st.button("Open Control Room", key="home_control_btn"):
                st.session_state.current_page = "Control Room"
                st.rerun()
            
    elif st.session_state.current_page == 'Profile':
        # Import and run the profile page module
        try:
            # Add a flag to the module to prevent setting page config
            sys.modules["streamlit"].in_streamlit_app = True
            from profile_page import main as profile_main
            profile_main()
        except Exception as e:
            st.error("Error loading Profile page")
            st.title("Profile Page - Error Loading")
            st.markdown("""
            We couldn't load the Profile page. Please try the following:
            
            1. Check if the profile_page.py file exists in the src/civicaide directory
            2. Make sure you have all the required dependencies installed
            3. Try refreshing the page
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Policy Dashboard':
        # Import and run the policy dashboard module directly
        try:
            # Create/modify a module to monkey patch set_page_config
            original_set_page_config = st.set_page_config
            def noop_set_page_config(*args, **kwargs):
                # Do nothing, because page config is already set in app.py
                pass
            
            # Replace with no-op function
            st.set_page_config = noop_set_page_config
            
            # Now import the module
            from policy_dashboard import main as policy_dashboard
            policy_dashboard()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except ImportError:
            st.error("Could not import the Policy Dashboard module")
            st.title("Policy Dashboard - Error Loading")
            st.markdown("""
            We couldn't load the Policy Dashboard. Please make sure the policy_dashboard.py file 
            exists in the src/civicaide directory and has a main() function.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
        except Exception as e:
            st.error(f"Error loading Policy Dashboard: {str(e)}")
            st.title("Policy Dashboard - Error Running")
            st.markdown("""
            There was an error running the Policy Dashboard. This might be due to missing data 
            or a configuration issue.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Traces Dashboard':
        # Import and run the trace dashboard module
        try:
            # Replace set_page_config temporarily
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            # Create traces directory if it doesn't exist
            os.makedirs("traces", exist_ok=True)
            
            # Ensure we have a basic trace file for demo purposes
            sample_file = "traces/sample_trace.json"
            if not os.path.exists(sample_file):
                try:
                    sample_data = {
                        "trace_id": "trace_sample_123456",
                        "query": "Ban on single use plastic bags",
                        "policy_type": "environmental",
                        "timestamp": "2025-05-24T10:30:00",
                        "spans": [
                            {
                                "span_id": "span_1",
                                "span_type": "agent",
                                "started_at": "2025-05-24T10:30:00",
                                "ended_at": "2025-05-24T10:31:00",
                                "details": {
                                    "agent_name": "Research Planner Agent",
                                    "message": "Planning research approach for plastic bag ban policy"
                                }
                            },
                            {
                                "span_id": "span_2",
                                "span_type": "policy_generation",
                                "started_at": "2025-05-24T10:33:00",
                                "ended_at": "2025-05-24T10:35:00",
                                "details": {
                                    "agent_name": "Policy Generation Agent",
                                    "message": "Generating initial policy proposals"
                                }
                            }
                        ]
                    }
                    with open(sample_file, 'w') as f:
                        json.dump(sample_data, f, indent=2)
                except Exception as e:
                    st.warning(f"Could not create sample trace file: {str(e)}")
            
            # Import the dashboard
            from trace_dashboard import main as trace_dashboard
            trace_dashboard()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except Exception as e:
            st.error("Error loading Traces Dashboard")
            st.title("Traces Dashboard - Error Loading")
            st.markdown(f"""
            We encountered an error loading the Traces Dashboard: {str(e)}
            
            ### Potential solutions:
            
            1. Make sure the trace_dashboard.py file exists in the src/civicaide directory
            2. Check if the traces directory exists
            3. Try refreshing the page
            
            If you're seeing errors related to OpenAI traces API, this is normal if you don't have API access set up.
            The application will use local JSON files for trace visualization instead.
            """)
            
            # Create trace directory if it doesn't exist
            os.makedirs("traces", exist_ok=True)
            
            # Check for trace files
            trace_files = glob.glob("traces/*.json")
            if not trace_files:
                st.info("No trace files found in traces directory")
            else:
                st.success(f"Found {len(trace_files)} trace files")
                for file in trace_files:
                    st.text(os.path.basename(file))
            
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Policy Analysis':
        # Import and run the policy analysis module
        try:
            # Replace set_page_config temporarily
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            from policy_analysis import main as analysis_main
            analysis_main()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except Exception as e:
            st.error("Error loading Policy Analysis")
            st.title("Policy Analysis - Error Loading")
            st.markdown("""
            We couldn't load the Policy Analysis page. This might be due to a missing file or module.
            Please check if the policy_analysis.py file exists and has a main() function.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Policy Research':
        # Import and run the policy research module
        try:
            # Replace set_page_config temporarily
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            from policy_research import main as research_main
            research_main()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except Exception as e:
            st.error("Error loading Policy Research")
            st.title("Policy Research - Error Loading")
            st.markdown("""
            We couldn't load the Policy Research page. Please check if the policy_research.py file 
            exists and has a main() function.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Policy Evolution':
        # Import and run the policy evolution module
        try:
            # Replace set_page_config temporarily
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            from policy_evolution import main as evolution_main
            evolution_main()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except Exception as e:
            st.error("Error loading Policy Evolution")
            st.title("Policy Evolution - Error Loading")
            st.markdown("""
            We couldn't load the Policy Evolution page. Please check if the policy_evolution.py file 
            exists and has a main() function.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    elif st.session_state.current_page == 'Control Room':
        # Import and run the control room module
        try:
            # Replace set_page_config temporarily
            original_set_page_config = st.set_page_config
            st.set_page_config = lambda *args, **kwargs: None
            
            from control_room import main as control_room_main
            control_room_main()
            
            # Restore original function
            st.set_page_config = original_set_page_config
        except Exception as e:
            st.error("Error loading Control Room")
            st.title("Control Room - Error Loading")
            st.markdown("""
            We couldn't load the Control Room page. Please check if the control_room.py file 
            exists and has a main() function.
            """)
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

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