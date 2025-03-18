import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="PolicyAide - Official Profile",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .profile-header {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 5px solid #4e8df5;
    }
    .status-card {
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .status-complete {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .status-pending {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e9ecef;
    }
    .info-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .info-section {
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to simulate AI-powered jurisdiction information gathering
def gather_jurisdiction_data(jurisdiction_name, official_role=None):
    """
    Gather comprehensive jurisdiction information using AI-powered research
    Returns a dictionary of jurisdiction data
    """
    # Simulate search and data gathering process
    st.info(f"🔍 Researching information about {jurisdiction_name}...")
    
    # Simulate progress with meaningful steps
    steps = [
        "Identifying jurisdiction boundaries and type...",
        "Gathering demographic and economic data...",
        "Researching government structure and leadership...",
        "Analyzing local budget information...",
        "Identifying key stakeholders and community groups...",
        "Reviewing recent legislative activity...",
        "Analyzing current policy priorities...",
        "Gathering information on upcoming elections and political landscape..."
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i+1)/len(steps))
        time.sleep(0.8)  # Simulate processing time
    
    status_text.text("✅ Jurisdiction research complete!")
    time.sleep(0.5)
    
    # Sample data for demonstration
    jurisdiction_data = {
        "elgin": {
            "basic_info": {
                "jurisdiction_type": "City",
                "name": "City of Elgin",
                "state": "Illinois",
                "county": "Kane and Cook Counties",
                "incorporation_date": "1854",
                "population": 115000,
                "area_sq_miles": 38.9,
                "population_density": 2956
            },
            "demographics": {
                "racial_makeup": {
                    "White": 65.2,
                    "Hispanic/Latino": 24.7,
                    "Black": 6.8,
                    "Asian": 5.4,
                    "Other": 2.9
                },
                "median_age": 34.3,
                "median_household_income": 76513,
                "poverty_rate": 10.8,
                "education_bachelors_or_higher": 28.7
            },
            "government": {
                "gov_type": "Council-Manager",
                "mayor": "David J. Kaptain",
                "council_size": 8,
                "election_schedule": "Next election: April 2025",
                "meeting_schedule": "City Council meets on the 2nd and 4th Wednesday of each month at 6:00 PM",
                "departments": ["Police", "Fire", "Public Works", "Community Development", "Finance", "Parks and Recreation"]
            },
            "budget": {
                "fiscal_year": "2023-2024",
                "total_budget": "$308.7 million",
                "general_fund": "$119.2 million",
                "capital_improvements": "$42.6 million",
                "sustainability_allocation": "$25,000",
                "major_revenue_sources": ["Property Tax (30%)", "Sales Tax (22%)", "Utility Fees (15%)", "State Income Tax (8%)"]
            },
            "current_priorities": [
                "Downtown revitalization",
                "Infrastructure improvements",
                "Economic development",
                "Public safety initiatives",
                "Environmental sustainability"
            ],
            "key_stakeholders": {
                "business_groups": ["Elgin Area Chamber of Commerce", "Downtown Neighborhood Association"],
                "community_orgs": ["Centro de Información", "Community Crisis Center", "Food for Greater Elgin"],
                "educational_institutions": ["School District U-46", "Elgin Community College"],
                "media_outlets": ["Daily Herald", "The Courier-News"]
            },
            "political_landscape": {
                "voter_turnout_last_election": "28% (local election)",
                "partisan_makeup": "Nonpartisan local elections",
                "active_community_issues": [
                    "Housing affordability",
                    "Economic development",
                    "Infrastructure and transportation",
                    "Public safety",
                    "Environmental sustainability"
                ]
            },
            "recent_legislation": [
                "Resolution supporting environmental sustainability initiatives (2023)",
                "Ordinance updating building codes for energy efficiency (2022)",
                "Resolution establishing diversity and inclusion task force (2022)"
            ]
        },
        "chicago": {
            "basic_info": {
                "jurisdiction_type": "City",
                "name": "City of Chicago",
                "state": "Illinois",
                "county": "Cook County",
                "incorporation_date": "1837",
                "population": 2696555,
                "area_sq_miles": 234,
                "population_density": 11783
            },
            "demographics": {
                "racial_makeup": {
                    "White": 33.5,
                    "Hispanic/Latino": 29.9,
                    "Black": 28.7,
                    "Asian": 7.1,
                    "Other": 0.8
                },
                "median_age": 34.9,
                "median_household_income": 62097,
                "poverty_rate": 18.4,
                "education_bachelors_or_higher": 39.5
            },
            "government": {
                "gov_type": "Mayor-Council",
                "mayor": "Brandon Johnson",
                "council_size": 50,
                "election_schedule": "Next municipal election: February 2027",
                "meeting_schedule": "City Council meets monthly, usually on the third Wednesday",
                "departments": ["Police", "Fire", "Streets and Sanitation", "Housing", "Planning and Development", "Public Health"]
            },
            "budget": {
                "fiscal_year": "2024",
                "total_budget": "$16.77 billion",
                "general_fund": "$5.68 billion",
                "capital_improvements": "$3.9 billion",
                "sustainability_allocation": "$188 million (Climate and Environmental Equity Fund)",
                "major_revenue_sources": ["Property Tax (21%)", "Local Taxes (19%)", "Utility Taxes (11%)", "Federal Grants (11%)"]
            },
            "current_priorities": [
                "Public safety and violence reduction",
                "Affordable housing",
                "Homelessness reduction",
                "Economic development",
                "Transit improvements",
                "Climate resilience"
            ],
            "key_stakeholders": {
                "business_groups": ["Chicago Chamber of Commerce", "Chicagoland Chamber of Commerce", "World Business Chicago"],
                "community_orgs": ["Chicago Community Trust", "United Way of Metro Chicago", "Neighborhood Housing Services"],
                "educational_institutions": ["Chicago Public Schools", "City Colleges of Chicago", "University of Chicago"],
                "media_outlets": ["Chicago Tribune", "Chicago Sun-Times", "WBEZ", "Block Club Chicago"]
            },
            "political_landscape": {
                "voter_turnout_last_election": "32% (municipal election)",
                "partisan_makeup": "Heavily Democratic (46 of 50 aldermen identify as Democrats)",
                "active_community_issues": [
                    "Crime and policing",
                    "Affordable housing crisis",
                    "Public education funding",
                    "Taxation and budget constraints",
                    "Environmental justice"
                ]
            },
            "recent_legislation": [
                "Increase in Real Estate Transfer Tax for homeless services (2023)",
                "Fair Transit Pilot Program extended (2023)",
                "Expanded metal detector screening at CTA stations (2023)",
                "Building energy efficiency standards updated (2022)"
            ]
        }
    }
    
    # Return data for the requested jurisdiction or a default message
    default_data = {
        "basic_info": {
            "jurisdiction_type": "Unknown",
            "name": jurisdiction_name,
            "state": "Information not available",
            "county": "Information not available",
            "incorporation_date": "Information not available",
            "population": 0,
            "area_sq_miles": 0,
            "population_density": 0
        },
        "demographics": {
            "racial_makeup": {
                "Information": "not available"
            },
            "median_age": 0,
            "median_household_income": 0,
            "poverty_rate": 0,
            "education_bachelors_or_higher": 0
        },
        "government": {
            "gov_type": "Information not available",
            "mayor": "Information not available",
            "council_size": 0,
            "election_schedule": "Information not available",
            "meeting_schedule": "Information not available",
            "departments": ["Information not available"]
        },
        "budget": {
            "fiscal_year": "Information not available",
            "total_budget": "Information not available",
            "general_fund": "Information not available",
            "capital_improvements": "Information not available",
            "sustainability_allocation": "Information not available",
            "major_revenue_sources": ["Information not available"]
        },
        "current_priorities": [
            "Information not available"
        ],
        "key_stakeholders": {
            "business_groups": ["Information not available"],
            "community_orgs": ["Information not available"],
            "educational_institutions": ["Information not available"],
            "media_outlets": ["Information not available"]
        },
        "political_landscape": {
            "voter_turnout_last_election": "Information not available",
            "partisan_makeup": "Information not available",
            "active_community_issues": [
                "Information not available"
            ]
        },
        "recent_legislation": [
            "Information not available"
        ]
    }
    
    return jurisdiction_data.get(jurisdiction_name.lower().strip(), default_data)

# Function to save profile data
def save_profile_data(profile_data):
    """Save profile data to a local JSON file"""
    os.makedirs("profiles", exist_ok=True)
    filename = f"profiles/{profile_data['basic_info']['name'].replace(' ', '_').lower()}.json"
    
    with open(filename, 'w') as f:
        json.dump(profile_data, f, indent=2)
    
    return filename

# Main profile page
def main():
    # Check if profile is already created and load it
    if 'profile_data' in st.session_state and 'profile_created' in st.session_state and st.session_state.profile_created:
        display_completed_profile(st.session_state.profile_data)
        return
        
    # Header
    st.markdown("<div class='profile-header'><h1>🏛️ PolicyAide Official Profile</h1><p>Welcome to PolicyAide! Let's gather information about your jurisdiction to provide tailored policy recommendations.</p></div>", unsafe_allow_html=True)
    
    # Setup form
    with st.form("profile_setup_form"):
        st.subheader("Official Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            official_name = st.text_input("Your Name", placeholder="e.g. Jane Smith")
            official_email = st.text_input("Official Email", placeholder="e.g. jsmith@cityofexample.gov")
            official_role = st.selectbox(
                "Your Role", 
                ["Mayor", "City Council Member", "County Commissioner", "City Manager", 
                 "Department Head", "Staff Member", "Other"]
            )
            
            if official_role == "Other":
                official_role_other = st.text_input("Please specify your role")
        
        with col2:
            jurisdiction_name = st.text_input("Jurisdiction Name", placeholder="e.g. City of Elgin")
            jurisdiction_type = st.selectbox(
                "Jurisdiction Type",
                ["City", "County", "Township", "Village", "Special District", "Other"]
            )
            
            if jurisdiction_type == "Other":
                jurisdiction_type_other = st.text_input("Please specify jurisdiction type")
            
            jurisdiction_state = st.selectbox(
                "State",
                ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", 
                 "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", 
                 "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", 
                 "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", 
                 "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", 
                 "New Hampshire", "New Jersey", "New Mexico", "New York", 
                 "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", 
                 "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
                 "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", 
                 "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"]
            )
        
        st.subheader("Areas of Interest")
        
        interests = st.multiselect(
            "Select policy areas you're most interested in",
            [
                "Environmental Sustainability", "Economic Development", "Housing",
                "Transportation", "Public Safety", "Parks and Recreation",
                "Public Health", "Education", "Budget and Taxation",
                "Equity and Inclusion", "Infrastructure", "Technology and Innovation"
            ]
        )
        
        submit_button = st.form_submit_button("Create Profile")
        
        if submit_button:
            if not official_name or not jurisdiction_name:
                st.error("Please provide both your name and jurisdiction name.")
            else:
                # Gather jurisdiction data
                with st.spinner("Gathering jurisdiction information..."):
                    jurisdiction_data = gather_jurisdiction_data(
                        jurisdiction_name.split(" ")[-1] if " " in jurisdiction_name else jurisdiction_name,
                        official_role
                    )
                
                # Create profile data
                profile_data = {
                    "official_info": {
                        "name": official_name,
                        "email": official_email,
                        "role": official_role_other if official_role == "Other" else official_role,
                        "interests": interests
                    },
                    "basic_info": jurisdiction_data["basic_info"],
                    "demographics": jurisdiction_data["demographics"],
                    "government": jurisdiction_data["government"],
                    "budget": jurisdiction_data["budget"],
                    "current_priorities": jurisdiction_data["current_priorities"],
                    "key_stakeholders": jurisdiction_data["key_stakeholders"],
                    "political_landscape": jurisdiction_data["political_landscape"],
                    "recent_legislation": jurisdiction_data["recent_legislation"],
                    "profile_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Override with user-provided information
                profile_data["basic_info"]["name"] = jurisdiction_name
                profile_data["basic_info"]["jurisdiction_type"] = jurisdiction_type_other if jurisdiction_type == "Other" else jurisdiction_type
                profile_data["basic_info"]["state"] = jurisdiction_state
                
                # Save profile
                filename = save_profile_data(profile_data)
                
                # Store in session state
                st.session_state.profile_data = profile_data
                st.session_state.profile_created = True
                
                # Success message
                st.success(f"✅ Profile created successfully and saved to {filename}!")
                st.balloons()
                
                # Display the completed profile
                st.rerun()

def display_completed_profile(profile_data):
    """Display the completed profile"""
    
    # Header with jurisdiction and official info
    st.markdown(f"""
    <div class='profile-header'>
        <h1>🏛️ {profile_data['basic_info']['name']}</h1>
        <p>Profile for {profile_data['official_info']['name']}, {profile_data['official_info']['role']}</p>
        <p><small>Created: {profile_data['profile_created']}</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Start Policy Analysis"):
            st.session_state.start_policy_analysis = True
            st.info("Redirecting to policy analysis...")
            # In a real app, you would redirect to the policy analysis page
    
    with col2:
        if st.button("Edit Profile"):
            st.session_state.profile_created = False
            st.rerun()
    
    with col3:
        st.write("")  # Empty space for alignment
    
    # Main content in tabs
    tab1, tab2, tab3 = st.tabs(["Jurisdiction Overview", "Government & Budget", "Political Landscape"])
    
    # Tab 1: Jurisdiction Overview
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<div class='section-header'>Basic Information</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='info-card'>
                <p><strong>Type:</strong> {profile_data['basic_info']['jurisdiction_type']}</p>
                <p><strong>State:</strong> {profile_data['basic_info']['state']}</p>
                <p><strong>County:</strong> {profile_data['basic_info']['county']}</p>
                <p><strong>Incorporated:</strong> {profile_data['basic_info']['incorporation_date']}</p>
                <p><strong>Population:</strong> {profile_data['basic_info']['population']:,}</p>
                <p><strong>Area:</strong> {profile_data['basic_info']['area_sq_miles']} sq miles</p>
                <p><strong>Density:</strong> {profile_data['basic_info']['population_density']} people/sq mile</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='section-header'>Current Priorities</div>", unsafe_allow_html=True)
            
            for priority in profile_data["current_priorities"]:
                st.markdown(f"• {priority}")
            
        with col2:
            st.markdown("<div class='section-header'>Demographics</div>", unsafe_allow_html=True)
            
            # Create demographic pie chart
            if "racial_makeup" in profile_data["demographics"] and isinstance(profile_data["demographics"]["racial_makeup"], dict):
                if "Information" not in profile_data["demographics"]["racial_makeup"]:
                    fig = px.pie(
                        values=list(profile_data["demographics"]["racial_makeup"].values()),
                        names=list(profile_data["demographics"]["racial_makeup"].keys()),
                        title="Racial/Ethnic Composition"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Demographics table
            demo_data = {
                "Metric": ["Median Age", "Median Household Income", "Poverty Rate", "Bachelor's Degree or Higher"],
                "Value": [
                    f"{profile_data['demographics']['median_age']} years",
                    f"${profile_data['demographics']['median_household_income']:,}",
                    f"{profile_data['demographics']['poverty_rate']}%",
                    f"{profile_data['demographics']['education_bachelors_or_higher']}%"
                ]
            }
            
            demo_df = pd.DataFrame(demo_data)
            st.table(demo_df)
    
    # Tab 2: Government & Budget
    with tab2:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<div class='section-header'>Government Structure</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='info-card'>
                <p><strong>Government Type:</strong> {profile_data['government']['gov_type']}</p>
                <p><strong>Mayor/Executive:</strong> {profile_data['government']['mayor']}</p>
                <p><strong>Council Size:</strong> {profile_data['government']['council_size']} members</p>
                <p><strong>Elections:</strong> {profile_data['government']['election_schedule']}</p>
                <p><strong>Meetings:</strong> {profile_data['government']['meeting_schedule']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='section-header'>Key Departments</div>", unsafe_allow_html=True)
            
            for dept in profile_data["government"]["departments"]:
                st.markdown(f"• {dept}")
        
        with col2:
            st.markdown("<div class='section-header'>Budget Overview</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='info-card'>
                <p><strong>Fiscal Year:</strong> {profile_data['budget']['fiscal_year']}</p>
                <p><strong>Total Budget:</strong> {profile_data['budget']['total_budget']}</p>
                <p><strong>General Fund:</strong> {profile_data['budget']['general_fund']}</p>
                <p><strong>Capital Improvements:</strong> {profile_data['budget']['capital_improvements']}</p>
                <p><strong>Sustainability Allocation:</strong> {profile_data['budget']['sustainability_allocation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='section-header'>Major Revenue Sources</div>", unsafe_allow_html=True)
            
            for source in profile_data["budget"]["major_revenue_sources"]:
                st.markdown(f"• {source}")
    
    # Tab 3: Political Landscape
    with tab3:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<div class='section-header'>Political Information</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='info-card'>
                <p><strong>Voter Turnout:</strong> {profile_data['political_landscape']['voter_turnout_last_election']}</p>
                <p><strong>Partisan Makeup:</strong> {profile_data['political_landscape']['partisan_makeup']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='section-header'>Active Community Issues</div>", unsafe_allow_html=True)
            
            for issue in profile_data["political_landscape"]["active_community_issues"]:
                st.markdown(f"• {issue}")
        
        with col2:
            st.markdown("<div class='section-header'>Key Stakeholders</div>", unsafe_allow_html=True)
            
            with st.expander("Business Groups"):
                for group in profile_data["key_stakeholders"]["business_groups"]:
                    st.markdown(f"• {group}")
            
            with st.expander("Community Organizations"):
                for org in profile_data["key_stakeholders"]["community_orgs"]:
                    st.markdown(f"• {org}")
            
            with st.expander("Educational Institutions"):
                for inst in profile_data["key_stakeholders"]["educational_institutions"]:
                    st.markdown(f"• {inst}")
            
            with st.expander("Media Outlets"):
                for media in profile_data["key_stakeholders"]["media_outlets"]:
                    st.markdown(f"• {media}")
            
            st.markdown("<div class='section-header'>Recent Legislation</div>", unsafe_allow_html=True)
            
            for legislation in profile_data["recent_legislation"]:
                st.markdown(f"• {legislation}")
    
    # Next steps section
    st.markdown("---")
    st.markdown("<div class='section-header'>Next Steps</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Now that your profile is complete, you can:
    1. **Start a Policy Analysis** - Analyze specific policy topics with AI assistance
    2. **Explore Sample Policies** - View policies from similar jurisdictions
    3. **Review Research Resources** - Access research and data relevant to your jurisdiction
    """)
    
    # Your interests section
    st.markdown("---")
    st.markdown("<div class='section-header'>Your Policy Interests</div>", unsafe_allow_html=True)
    
    interest_cols = st.columns(3)
    for i, interest in enumerate(profile_data["official_info"]["interests"]):
        interest_cols[i % 3].markdown(f"🔍 **{interest}**")

# Run the app
if __name__ == "__main__":
    main() 