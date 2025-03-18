import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
import re
import time

# Set page config
st.set_page_config(
    page_title="CivicAide Policy Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
    .policy-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #4e8df5;
    }
    .metric-container {
        background-color: #f1f3f6;
        border-radius: 5px;
        padding: 1rem;
        text-align: center;
    }
    .impact-high {
        color: #28a745;
        font-weight: bold;
    }
    .impact-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .impact-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Add a new function to gather local community context via web search
def gather_community_context(jurisdiction_name):
    """
    Gather general community context information during user onboarding
    Returns a dictionary of community context information
    """
    # This is a simplified simulation - in a real implementation, 
    # this would use a real web search API to gather information
    st.info(f"Gathering community information about {jurisdiction_name}...")
    
    # Simulate search delay
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.02)
        progress_bar.progress(i + 1)
    
    # For demo purposes, we'll return pre-set data for some cities
    # In a real implementation, this would parse web search results
    jurisdiction_data = {
        "elgin": {
            "Jurisdiction": "City of Elgin, Illinois (Population: 115,000)",
            "Economic Context": "Education, Health Care, Government, Industrial",
            "Geographic Area": "38.9 square miles",
            "Demographic Profile": "65% White, 24% Hispanic, 6% Black, 5% Asian",
            "Political Landscape": "Upcoming election, disorganized sustainability commission",
            "Budget Constraints": "$25,000 allocated for sustainability initiatives",
            "Local Challenges": "Many lower income residents, infrastructure needs",
            "Key Stakeholders": "City, schools, residents, businesses, environment groups",
            "Existing Government Structure": "Council-manager form of government with 8 council members"
        },
        "chicago": {
            "Jurisdiction": "City of Chicago, Illinois (Population: 2.7 million)",
            "Economic Context": "Finance, Manufacturing, Transportation, Technology",
            "Geographic Area": "234 square miles",
            "Demographic Profile": "33% White, 30% Black, 29% Hispanic, 7% Asian",
            "Political Landscape": "Strong mayoral system, active city council with 50 aldermen",
            "Budget Constraints": "Significant resources but competing priorities",
            "Local Challenges": "Economic inequality, environmental justice concerns, crime",
            "Key Stakeholders": "Large retailers, neighborhood businesses, environmental groups, residents",
            "Existing Government Structure": "Mayor-council government with 50 wards"
        },
        "portland": {
            "Jurisdiction": "City of Portland, Oregon (Population: 650,000)",
            "Economic Context": "Technology, Manufacturing, Outdoor Recreation, Services",
            "Geographic Area": "145 square miles",
            "Demographic Profile": "70% White, 9% Hispanic, 6% Black, 8% Asian",
            "Political Landscape": "Progressive city council, strong environmental focus",
            "Budget Constraints": "Dedicated sustainability funding ($1.2M annually)",
            "Local Challenges": "Homelessness, rapid growth, housing affordability",
            "Key Stakeholders": "Environmental advocates, business alliances, community groups",
            "Existing Government Structure": "Commission form of government with 4 commissioners and a mayor"
        }
    }
    
    # Default data for jurisdictions not in our pre-set list
    default_data = {
        "Jurisdiction": f"{jurisdiction_name} (Population: Unknown)",
        "Economic Context": "Information not available",
        "Geographic Area": "Information not available",
        "Demographic Profile": "Information not available",
        "Political Landscape": "Information not available",
        "Budget Constraints": "Information not available",
        "Local Challenges": "Information not available",
        "Key Stakeholders": "Residents, businesses, local government",
        "Existing Government Structure": "Information not available"
    }
    
    # Return data for the requested jurisdiction or default data
    return jurisdiction_data.get(jurisdiction_name.lower().strip(), default_data)

# Add a function to gather policy-specific context via web search
def gather_policy_context(policy_topic, jurisdiction_name):
    """
    Gather policy-specific context for a given topic and jurisdiction
    Returns policy research plan, existing policies, and related information
    """
    # This is a simplified simulation - in a real implementation, 
    # this would use a real web search API to gather information
    st.info(f"Researching {policy_topic} policies relevant to {jurisdiction_name}...")
    
    # Simulate search delay
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.03)
        progress_bar.progress(i + 1)
    
    # Map of pre-defined policy data for demonstration
    policy_data = {
        "plastic bags": {
            "similar_jurisdictions": [
                "Evanston, IL (Complete ban on single-use bags)",
                "Oak Park, IL (10-cent fee per bag)",
                "Chicago, IL (7-cent tax per checkout bag)"
            ],
            "existing_policies": {
                "elgin": "No existing policies on plastic bags",
                "chicago": "7-cent tax on all checkout bags since 2017",
                "portland": "Ban on single-use plastic bags since 2011, 5-cent fee on paper bags"
            },
            "implementation_challenges": [
                "Business adaptation costs and potential resistance",
                "Consumer behavior change requiring education and awareness",
                "Enforcement mechanisms and compliance monitoring",
                "Budget for educational campaigns and alternatives"
            ],
            "success_metrics": [
                "80-90% reduction in single-use plastic bag consumption",
                "High levels of reusable bag adoption (60-70% of shoppers)",
                "Reduced plastic waste in local waterways and cleanup sites",
                "Minimal economic impact on low-income residents" 
            ],
            "search_queries": [
                f"Single use plastic bag ban ordinances in U.S. cities similar to {jurisdiction_name}",
                "Effectiveness of plastic bag bans in cities with similar demographics",
                "Implementation challenges of plastic bag bans within limited budgets",
                f"Cost analysis of enforcing plastic bag bans for cities like {jurisdiction_name}",
                "Community and business responses to proposed plastic bag bans"
            ]
        },
        "short term rentals": {
            "similar_jurisdictions": [
                "Nashville, TN (Permit system with primary residence requirement)",
                "Austin, TX (License requirement with occupancy limits)",
                "Charleston, SC (Strict zoning restrictions)"
            ],
            "existing_policies": {
                "elgin": "Limited regulation through general zoning ordinances",
                "chicago": "Shared Housing Ordinance requiring registration and fees",
                "portland": "Accessory Short-Term Rental program with permit requirements"
            },
            "implementation_challenges": [
                "Enforcement difficulties with online platforms",
                "Balancing housing availability with tourism benefits",
                "Tracking unregistered properties",
                "Addressing neighborhood concerns about character and noise"
            ],
            "success_metrics": [
                "Registration compliance rates above 70%",
                "Maintenance of long-term housing affordability",
                "Balanced distribution of STRs across neighborhoods",
                "Reduction in nuisance complaints from neighbors"
            ],
            "search_queries": [
                f"Short term rental regulations in cities similar to {jurisdiction_name}",
                "Enforcement mechanisms for short term rental ordinances",
                "Impact of STR regulations on housing affordability",
                "Balancing tourism benefits with neighborhood preservation in STR policy",
                "Short term rental compliance monitoring systems"
            ]
        }
    }
    
    # Default data for policy topics not in our pre-set list
    default_policy_data = {
        "similar_jurisdictions": [
            "Information not available - custom research needed"
        ],
        "existing_policies": {
            jurisdiction_name.lower(): "No information available on existing policies"
        },
        "implementation_challenges": [
            "Specific challenges would require targeted research for this policy area"
        ],
        "success_metrics": [
            "Success metrics would be developed based on policy objectives"
        ],
        "search_queries": [
            f"{policy_topic} regulations in cities similar to {jurisdiction_name}",
            f"Best practices for {policy_topic} policy implementation",
            f"Community impact of {policy_topic} regulations",
            f"Cost analysis of {policy_topic} policy enforcement",
            f"Stakeholder responses to {policy_topic} policies"
        ]
    }
    
    # Get the policy data or use default if not found
    topic_key = next((k for k in policy_data.keys() if k in policy_topic.lower()), None)
    result = policy_data.get(topic_key, default_policy_data)
    
    # Add the jurisdiction-specific existing policy if available
    existing_policy = "No information available"
    if topic_key:
        existing_policy = result["existing_policies"].get(jurisdiction_name.lower(), 
                                                        f"No specific {policy_topic} policies found for {jurisdiction_name}")
    
    return {
        "similar_jurisdictions": result["similar_jurisdictions"],
        "existing_policy": existing_policy,
        "implementation_challenges": result["implementation_challenges"],
        "success_metrics": result["success_metrics"],
        "search_queries": result["search_queries"]
    }

# Function to load policy data from markdown files
def load_policy_data(file_path=None):
    """Load policy data from a markdown file or use demo data if not available"""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the markdown content to extract data
        data = {}
        
        # Extract title/query
        title_match = re.search(r'# .*: (.*)', content)
        if title_match:
            data['query'] = title_match.group(1)
        else:
            data['query'] = "Unknown Policy Query"
        
        # Extract summary
        summary_match = re.search(r'## Executive Summary\s+\n(.*?)(?=\n## )', content, re.DOTALL)
        if summary_match:
            data['summary'] = summary_match.group(1).strip()
        else:
            data['summary'] = "No summary available"
        
        # Extract top proposals
        proposals_section = re.search(r'## Top Policy Proposals\s+\n(.*?)(?=\n## )', content, re.DOTALL)
        if proposals_section:
            proposals_text = proposals_section.group(1)
            proposals = []
            
            # Find all proposal blocks
            proposal_blocks = re.findall(r'### \d+\. (.*?)\s+\n(.*?)(?=\*\*Rationale\*\*: )(.*?)(?=\n\n|$)', proposals_text, re.DOTALL)
            
            for title, description, rationale in proposal_blocks:
                proposals.append({
                    'id': f"proposal_{len(proposals)+1}",
                    'title': title.strip(),
                    'description': description.strip(),
                    'rationale': rationale.strip()
                })
            
            data['top_proposals'] = proposals
        else:
            data['top_proposals'] = []
        
        # Extract impact matrix if available
        matrix_section = re.search(r'## Policy Impact Matrix\s+\n\|(.*?)\|(.*?)\n\|(.*?)\|(.*?)(?=\n\n|$)', content, re.DOTALL)
        if matrix_section:
            # Parse the markdown table
            headers = [h.strip() for h in matrix_section.group(1).split('|') if h.strip()]
            rows = []
            
            # Get all rows after the header and separator
            table_rows = re.findall(r'\|(.*?)\|', content[matrix_section.end():])
            
            # Process each policy row
            impact_matrix = []
            for i in range(0, len(table_rows), len(headers)):
                if i >= len(table_rows):
                    break
                    
                row_values = [v.strip() for v in table_rows[i].split('|') if v]
                
                if len(row_values) == len(headers):
                    row_dict = {}
                    for j, header in enumerate(headers):
                        row_dict[header.lower().replace(' ', '_')] = row_values[j]
                    impact_matrix.append(row_dict)
            
            data['impact_matrix'] = impact_matrix
        else:
            data['impact_matrix'] = []
        
        # Extract stakeholder analysis
        stakeholder_section = re.search(r'## Stakeholder Impact Analysis\s+\n(.*?)(?=\n## )', content, re.DOTALL)
        if stakeholder_section:
            stakeholder_text = stakeholder_section.group(1)
            stakeholders = {}
            
            # Find all stakeholder blocks
            stakeholder_blocks = re.findall(r'### (.*?)\s+\n(.*?)(?=\n###|\n## |$)', stakeholder_text, re.DOTALL)
            
            for stakeholder, impacts in stakeholder_blocks:
                impact_list = [impact.strip().lstrip('- ') for impact in impacts.strip().split('\n') if impact.strip()]
                stakeholders[stakeholder.strip()] = impact_list
            
            data['stakeholder_analysis'] = stakeholders
        else:
            data['stakeholder_analysis'] = {}
        
        # Extract implementation steps
        steps_section = re.search(r'## Implementation Steps\s+\n(.*?)(?=\n## |$)', content, re.DOTALL)
        if steps_section:
            steps_text = steps_section.group(1)
            steps = [step.strip().lstrip('0123456789. ') for step in steps_text.strip().split('\n') if step.strip()]
            data['implementation_steps'] = steps
        else:
            data['implementation_steps'] = []
        
        # Extract implementation considerations
        considerations_section = re.search(r'## Implementation Considerations\s+\n(.*?)(?=\n## |$)', content, re.DOTALL)
        if considerations_section:
            considerations_text = considerations_section.group(1)
            considerations = [consideration.strip().lstrip('- ') for consideration in considerations_text.strip().split('\n') if consideration.strip()]
            data['key_considerations'] = considerations
        else:
            data['key_considerations'] = []
        
        return data
    else:
        # Return demo data if no file provided or file doesn't exist
        return {
            'query': 'ban on single use plastic bags',
            'summary': 'This report explores strategies to effectively ban single-use plastic bags with a focus on sustainability and equity.',
            'top_proposals': [
                {
                    'id': 'proposal_1',
                    'title': 'Enhanced Biodegradable Bag Mandate',
                    'description': 'Mandate all stores to provide biodegradable bags made from certified renewable resources.',
                    'rationale': 'Strengthening the mandate ensures significant reduction in plastic pollution.'
                },
                {
                    'id': 'proposal_2',
                    'title': 'Community-Led Education and Plastic Reduction Initiative',
                    'description': 'Launch a community-focused campaign to educate residents on environmental impacts.',
                    'rationale': 'Empowering communities ensures local buy-in and taps into grassroots innovation.'
                },
                {
                    'id': 'proposal_3',
                    'title': 'Enhanced Incentivized Reusable Bag Program',
                    'description': 'Expand the program by integrating digital technologies and tiered incentives.',
                    'rationale': 'Leveraging digital tools amplifies behavior changes, ensuring greater participation.'
                }
            ],
            'impact_matrix': [
                {
                    'policy': 'Enhanced Biodegradable Bag Mandate',
                    'environmental_impact': 'High',
                    'economic_feasibility': 'High',
                    'equity': 'High',
                    'implementation_complexity': 'Medium'
                },
                {
                    'policy': 'Community-Led Education and Plastic Reduction Initiative',
                    'environmental_impact': 'High',
                    'economic_feasibility': 'High',
                    'equity': 'High',
                    'implementation_complexity': 'Medium'
                },
                {
                    'policy': 'Enhanced Incentivized Reusable Bag Program',
                    'environmental_impact': 'High',
                    'economic_feasibility': 'High',
                    'equity': 'High',
                    'implementation_complexity': 'Medium'
                }
            ],
            'stakeholder_analysis': {
                'Small Businesses': ['May face initial adaptation challenges but benefit from level playing field.'],
                'Large Retailers': ['Have resources to adapt but need to adjust supply chains.'],
                'Low Income Residents': ['Require protection from potential price increases.'],
                'Environmental Groups': ['Supportive but may push for stronger measures.'],
                'Local Government': ['Responsible for implementation and enforcement.'],
                'Manufacturers': ['Need to adapt product lines.']
            },
            'implementation_steps': [
                'Conduct stakeholder consultations to refine policy details.',
                'Develop and deploy educational materials and tools.',
                'Launch pilot programs to test acceptance and effectiveness.',
                'Expand policies based on pilot feedback and adjust as needed.',
                'Establish monitoring and reporting frameworks for ongoing evaluation.'
            ],
            'key_considerations': [
                'Ensuring sufficient supply of biodegradable materials.',
                'Engaging diverse communities for widespread participation.',
                'Balancing initial costs with long-term environmental benefits.',
                'Monitoring compliance and adapting policies based on data feedback.'
            ]
        }

# Find all policy report files
def find_policy_files():
    """Find all policy report markdown files in the current directory and src/civicaide"""
    files = []
    
    # Look in current directory
    for file in glob.glob("*.md"):
        if "policy" in file.lower() or "ban" in file.lower():
            files.append(file)
    
    # Look in src/civicaide
    civicaide_dir = os.path.join("src", "civicaide")
    if os.path.exists(civicaide_dir):
        for file in glob.glob(os.path.join(civicaide_dir, "*")):
            if os.path.isfile(file) and ("policy" in os.path.basename(file).lower() or "ban" in os.path.basename(file).lower()):
                files.append(file)
    
    return files

# Sidebar for file selection and controls
st.sidebar.title("CivicAide Policy Dashboard")
st.sidebar.image("https://img.icons8.com/color/96/000000/government.png", width=100)

# Find policy files
policy_files = find_policy_files()

if policy_files:
    selected_file = st.sidebar.selectbox(
        "Select Policy Report",
        options=policy_files,
        format_func=lambda x: os.path.basename(x)
    )
    policy_data = load_policy_data(selected_file)
else:
    st.sidebar.warning("No policy report files found. Using demo data.")
    policy_data = load_policy_data()

# Add filter options in sidebar
st.sidebar.subheader("Filter Options")
if policy_data['stakeholder_analysis']:
    selected_stakeholders = st.sidebar.multiselect(
        "Stakeholder Groups",
        options=list(policy_data['stakeholder_analysis'].keys()),
        default=list(policy_data['stakeholder_analysis'].keys())[:2] if policy_data['stakeholder_analysis'] else []
    )

# Main dashboard content
st.title(f"Policy Analysis Dashboard: {policy_data['query'].title()}")

# Summary section
st.header("Executive Summary")
st.write(policy_data['summary'])

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Policy Proposals", "Impact Analysis", "Stakeholder Analysis", "Implementation", "Research & Context"])

# Tab 1: Policy Proposals
with tab1:
    st.subheader("Top Policy Proposals")
    
    # Display policy proposals in card-like format
    for i, proposal in enumerate(policy_data['top_proposals']):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="policy-card">
                <h3>{i+1}. {proposal['title']}</h3>
                <p>{proposal['description']}</p>
                <p><strong>Rationale:</strong> {proposal['rationale']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Find this proposal in the impact matrix
            proposal_impacts = {}
            for impact in policy_data['impact_matrix']:
                if impact.get('policy') == proposal['title']:
                    proposal_impacts = impact
                    break
            
            if proposal_impacts:
                # Create a radar chart for this proposal
                categories = ['Environmental', 'Economic', 'Equity', 'Implementation']
                values = []
                
                for cat in ['environmental_impact', 'economic_feasibility', 'equity', 'implementation_complexity']:
                    # Convert textual ratings to numeric
                    if cat in proposal_impacts:
                        if proposal_impacts[cat].lower() == 'high':
                            values.append(3)
                        elif proposal_impacts[cat].lower() == 'medium':
                            values.append(2)
                        elif proposal_impacts[cat].lower() == 'low':
                            values.append(1)
                        else:
                            values.append(0)
                    else:
                        values.append(0)
                
                # If implementation complexity is high, that's actually bad, so invert the scale
                if len(values) >= 4:
                    values[3] = 4 - values[3]
                
                # Create radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=proposal['title']
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 3]
                        )
                    ),
                    showlegend=False,
                    margin=dict(l=5, r=5, t=20, b=20),
                    height=180
                )
                
                st.plotly_chart(fig, use_container_width=True)

# Tab 2: Impact Analysis
with tab2:
    st.subheader("Policy Impact Matrix")
    
    if policy_data['impact_matrix']:
        try:
            # Create a DataFrame from the impact matrix
            impact_df = pd.DataFrame(policy_data['impact_matrix'])
            
            # Convert textual ratings to numeric for visualization
            numeric_df = impact_df.copy()
            for col in ['environmental_impact', 'economic_feasibility', 'equity', 'implementation_complexity']:
                if col in numeric_df.columns:
                    numeric_df[col] = numeric_df[col].apply(lambda x: 3 if x.lower() == 'high' else (2 if x.lower() == 'medium' else 1))
            
            # For implementation complexity, lower is better
            if 'implementation_complexity' in numeric_df.columns:
                numeric_df['implementation_complexity'] = 4 - numeric_df['implementation_complexity']
                numeric_df.rename(columns={'implementation_complexity': 'implementation_ease'}, inplace=True)
            
            # Reshape for radar chart
            categories = [col.replace('_', ' ').title() for col in numeric_df.columns if col != 'policy']
            
            # Create radar chart for all policies
            if len(categories) > 0 and len(numeric_df) > 0:
                fig = go.Figure()
                
                for i, policy in enumerate(numeric_df['policy']):
                    values = numeric_df.iloc[i, 1:].values
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=policy
                    ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 3]
                        )
                    ),
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a clustered bar chart for comparison
                fig_bar = go.Figure()
                
                for i, col in enumerate([col for col in impact_df.columns if col != 'policy']):
                    visible = 'legendonly' if i > 1 else True  # Only show first two metrics by default
                    
                    fig_bar.add_trace(go.Bar(
                        x=impact_df['policy'],
                        y=[3 if val.lower() == 'high' else (2 if val.lower() == 'medium' else 1) for val in impact_df[col]],
                        name=col.replace('_', ' ').title(),
                        visible=visible
                    ))
                
                fig_bar.update_layout(
                    barmode='group',
                    xaxis_title="Policy",
                    yaxis_title="Rating (3=High, 2=Medium, 1=Low)",
                    legend_title="Impact Metrics",
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=400
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Not enough data to create visualizations.")
            
            # Display raw data table
            if not impact_df.empty:
                st.subheader("Raw Impact Data")
                st.dataframe(impact_df.set_index('policy'))
            
        except Exception as e:
            st.error(f"Error creating impact visualizations: {str(e)}")
    else:
        st.write("No impact matrix data available.")

# Tab 3: Stakeholder Analysis
with tab3:
    st.subheader("Stakeholder Impact Analysis")
    
    if policy_data['stakeholder_analysis']:
        try:
            # Filter stakeholders based on selection
            if 'selected_stakeholders' in locals() and selected_stakeholders:
                filtered_stakeholders = {k: v for k, v in policy_data['stakeholder_analysis'].items() if k in selected_stakeholders}
            else:
                filtered_stakeholders = policy_data['stakeholder_analysis']
            
            # Create a heatmap of policy impacts on stakeholders
            impact_scores = {}
            
            # Function to estimate sentiment score from impact text
            def estimate_impact_score(text):
                positive_terms = ['benefit', 'supportive', 'positive', 'advantage', 'opportunity']
                negative_terms = ['challenge', 'concern', 'negative', 'burden', 'cost']
                
                score = 0
                for term in positive_terms:
                    if term in text.lower():
                        score += 1
                for term in negative_terms:
                    if term in text.lower():
                        score -= 1
                
                # Normalize to range 0-5
                return min(5, max(0, score + 3))
            
            # Calculate impact scores
            for stakeholder, impacts in filtered_stakeholders.items():
                impact_scores[stakeholder] = {}
                
                # Check if impacts are already separated by policy
                policy_specific = any(':' in impact for impact in impacts)
                
                if policy_specific:
                    for impact in impacts:
                        if ':' in impact:
                            parts = impact.split(':', 1)
                            policy = parts[0].strip()
                            impact_text = parts[1].strip()
                            impact_scores[stakeholder][policy] = estimate_impact_score(impact_text)
                else:
                    # If not policy-specific, assume the impact applies to all policies
                    avg_score = sum(estimate_impact_score(impact) for impact in impacts) / len(impacts) if impacts else 2.5
                    for proposal in policy_data['top_proposals']:
                        impact_scores[stakeholder][proposal['title']] = avg_score
            
            # Convert to format suitable for heatmap
            heatmap_data = []
            
            for stakeholder in filtered_stakeholders.keys():
                for proposal in policy_data['top_proposals']:
                    score = impact_scores.get(stakeholder, {}).get(proposal['title'], 2.5)  # Default neutral
                    heatmap_data.append({
                        'Stakeholder': stakeholder,
                        'Policy': proposal['title'],
                        'Impact Score': score
                    })
            
            if heatmap_data and len(heatmap_data) > 0:
                heatmap_df = pd.DataFrame(heatmap_data)
                
                # Create heatmap
                fig = px.imshow(
                    pd.pivot_table(
                        heatmap_df, 
                        values='Impact Score',
                        index='Stakeholder',
                        columns='Policy'
                    ),
                    color_continuous_scale=px.colors.diverging.RdBu_r,
                    zmin=0, zmax=5,
                    labels=dict(x="Policy", y="Stakeholder", color="Impact Score")
                )
                
                fig.update_layout(
                    xaxis_title="Policy Proposal",
                    yaxis_title="Stakeholder Group",
                    coloraxis_colorbar=dict(
                        title="Impact Score",
                        tickvals=[0, 1, 2, 3, 4, 5],
                        ticktext=['Very Negative', 'Negative', 'Slightly Negative', 
                                'Slightly Positive', 'Positive', 'Very Positive']
                    ),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Not enough data to create heatmap visualization.")
            
            # Display stakeholder impacts in expandable sections
            for stakeholder, impacts in filtered_stakeholders.items():
                with st.expander(f"{stakeholder}"):
                    for impact in impacts:
                        st.write(f"• {impact}")
                        
        except Exception as e:
            st.error(f"Error creating stakeholder visualizations: {str(e)}")
    else:
        st.write("No stakeholder analysis data available.")

# Tab 4: Implementation
with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Implementation Steps")
        if policy_data['implementation_steps']:
            for i, step in enumerate(policy_data['implementation_steps']):
                st.markdown(f"**{i+1}.** {step}")
        else:
            st.write("No implementation steps available.")
    
    with col2:
        st.subheader("Key Considerations")
        if policy_data['key_considerations']:
            for consideration in policy_data['key_considerations']:
                st.markdown(f"• {consideration}")
        else:
            st.write("No key considerations available.")
    
    # Create a Gantt chart for implementation timeline
    st.subheader("Implementation Timeline (Estimated)")
    
    if policy_data['implementation_steps']:
        try:
            # Create estimated timeline data
            timeline_data = []
            current_month = 0
            
            for i, step in enumerate(policy_data['implementation_steps']):
                # Estimate duration based on step text
                if any(term in step.lower() for term in ['launch', 'establish', 'conduct']):
                    duration = 2
                elif any(term in step.lower() for term in ['develop', 'expand', 'adjust']):
                    duration = 3
                else:
                    duration = 1
                    
                timeline_data.append({
                    'Task': f"Step {i+1}",
                    'Description': step,
                    'Start': current_month,
                    'Duration': duration,
                    'End': current_month + duration,
                    'Resource': 'Primary' if i % 2 == 0 else 'Secondary'
                })
                
                current_month += duration
            
            df = pd.DataFrame(timeline_data)
            
            # Create Gantt chart
            fig = px.timeline(
                df, 
                x_start="Start", 
                x_end="End", 
                y="Task",
                color="Resource",
                hover_data=["Description"]
            )
            
            fig.update_layout(
                xaxis_title="Months from Start",
                yaxis_title="",
                height=300,
                xaxis=dict(
                    tickvals=list(range(int(df['End'].max() + 1))),
                    ticktext=[f"Month {i}" for i in range(int(df['End'].max() + 1))]
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating timeline visualization: {str(e)}")
        
        # Success metrics
        st.subheader("Suggested Success Metrics")
        
        metrics = [
            "Reduction in single-use bag consumption",
            "Public awareness and satisfaction levels",
            "Business compliance rates",
            "Reduction in plastic waste at cleanup sites",
            "Proportion of residents using reusable bags"
        ]
        
        metric_cols = st.columns(len(metrics))
        for i, col in enumerate(metric_cols):
            with col:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>{metrics[i]}</h4>
                    <div class="goal-indicator" style="height: 5px; background: linear-gradient(to right, #ff4e50, #f9d423);"></div>
                </div>
                """, unsafe_allow_html=True)

# Tab 5: Research & Context
with tab5:
    st.subheader("Research Methodology & Local Context")
    
    # Add tabs for the two different context gathering workflows
    context_tab1, context_tab2 = st.tabs(["Community Onboarding", "Policy Research"])
    
    # Tab 1: Community Context Onboarding
    with context_tab1:
        st.markdown("### Community Context Gathering")
        st.write("""
        This process is typically completed during onboarding when a new community joins PolicyAide.
        The gathered information serves as the foundation for all future policy analyses.
        """)
        
        # Create two columns for the context gathering interface
        col_search, col_result = st.columns([1, 2])
        
        with col_search:
            st.markdown("#### Community Search")
            st.write("Enter your jurisdiction to gather community information:")
            
            community_input = st.text_input("Jurisdiction Name", "")
            
            if st.button("Gather Community Context"):
                if community_input:
                    # Get context data via web search
                    context_data = gather_community_context(community_input)
                    
                    # Store in session state so it persists
                    st.session_state.community_data = context_data
                    st.session_state.show_community_editor = True
                else:
                    st.error("Please enter a jurisdiction name")
        
        with col_result:
            # Display and allow editing of gathered community context
            if 'community_data' in st.session_state and 'show_community_editor' in st.session_state and st.session_state.show_community_editor:
                st.markdown("#### Community Information")
                st.write("Review and edit the gathered information:")
                
                # Create editable fields for each context item
                edited_context = {}
                for key, value in st.session_state.community_data.items():
                    edited_value = st.text_input(f"{key}", value, key=f"community_{key}")
                    edited_context[key] = edited_value
                
                # Allow the user to save their changes
                if st.button("Save Community Profile"):
                    st.session_state.community_data = edited_context
                    st.session_state.community_confirmed = True
                    st.success("Community profile saved! This information will be used for all policy analyses.")
    
    # Tab 2: Policy-Specific Research
    with context_tab2:
        st.markdown("### Policy-Specific Research")
        st.write("""
        This process is conducted for each new policy topic you want to analyze.
        It builds on your community profile to find relevant policy information.
        """)
        
        # Create two columns for the policy research interface
        col_policy, col_findings = st.columns([1, 2])
        
        with col_policy:
            st.markdown("#### Policy Topic")
            
            # Get the jurisdiction from community data if available
            jurisdiction = ""
            if 'community_data' in st.session_state and 'community_confirmed' in st.session_state:
                jurisdiction_full = st.session_state.community_data.get("Jurisdiction", "")
                jurisdiction = jurisdiction_full.split("(")[0].strip() if "(" in jurisdiction_full else jurisdiction_full
            
            # Allow users to override the jurisdiction
            policy_jurisdiction = st.text_input("Jurisdiction", jurisdiction, key="policy_jurisdiction")
            policy_topic = st.text_input("Policy Topic", "Ban on single use plastic bags")
            
            if st.button("Research Policy Context"):
                if policy_jurisdiction and policy_topic:
                    # Get policy-specific data
                    policy_research = gather_policy_context(policy_topic, policy_jurisdiction)
                    
                    # Store in session state
                    st.session_state.policy_research = policy_research
                    st.session_state.show_policy_research = True
                else:
                    st.error("Please enter both jurisdiction and policy topic")
        
        with col_findings:
            # Display policy research findings
            if 'policy_research' in st.session_state and 'show_policy_research' in st.session_state and st.session_state.show_policy_research:
                st.markdown("#### Policy Research Findings")
                
                # Show existing policy
                st.markdown("**Existing Policy:**")
                st.info(st.session_state.policy_research["existing_policy"])
                
                # Show similar jurisdictions
                st.markdown("**Similar Jurisdictions with Relevant Policies:**")
                for jurisdiction in st.session_state.policy_research["similar_jurisdictions"]:
                    st.markdown(f"• {jurisdiction}")
                
                # Show implementation challenges
                with st.expander("Implementation Challenges"):
                    for challenge in st.session_state.policy_research["implementation_challenges"]:
                        st.markdown(f"• {challenge}")
                
                # Show success metrics
                with st.expander("Recommended Success Metrics"):
                    for metric in st.session_state.policy_research["success_metrics"]:
                        st.markdown(f"• {metric}")
                
                # Show search queries used
                with st.expander("Research Queries"):
                    st.markdown("*The following search queries were used to gather information:*")
                    for query in st.session_state.policy_research["search_queries"]:
                        st.markdown(f"• {query}")
                
                # Button to use this research for policy analysis
                if st.button("Use This Research for Policy Analysis"):
                    st.success("Research context confirmed! This will be used for your policy analysis.")
                    st.session_state.policy_research_confirmed = True
    
    # Display the rest of the Research & Context tab
    st.markdown("---")
    
    # Create two columns for the existing layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Local Context")
        
        # Use confirmed community data if available, otherwise use the default
        if 'community_data' in st.session_state and 'community_confirmed' in st.session_state and st.session_state.community_confirmed:
            local_context = {k: v for k, v in st.session_state.community_data.items() if k in [
                "Jurisdiction", "Economic Context", "Political Landscape", 
                "Budget Constraints", "Local Challenges", "Key Stakeholders"
            ]}
        else:
            # This is the existing default data
            local_context = {
                "Jurisdiction": "City of Elgin Illinois (Population: 115,000)",
                "Economic Context": "Education, Health Care, Government, Industrial",
                "Political Landscape": "Upcoming election, disorganized sustainability commission",
                "Budget Constraints": "$25,000",
                "Local Challenges": "many lower income residents",
                "Key Stakeholders": "city, schools, residents, businesses, environment"
            }
        
        # Add existing policy if available
        if 'policy_research' in st.session_state and 'policy_research_confirmed' in st.session_state:
            local_context["Existing Policies"] = st.session_state.policy_research["existing_policy"]
        else:
            local_context["Existing Policies"] = "none"
        
        # Display local context as a table
        context_df = pd.DataFrame({"Parameter": local_context.keys(), 
                                  "Value": local_context.values()})
        st.table(context_df)
    
    with col2:
        st.markdown("### Research Strategy")
        
        # Use research queries from policy research if available
        if 'policy_research' in st.session_state and 'policy_research_confirmed' in st.session_state:
            search_queries = st.session_state.policy_research["search_queries"]
        else:
            # Default queries
            search_queries = [
                "Single use plastic bag ban ordinances in U.S. cities similar to Elgin",
                "Effectiveness of plastic bag bans in cities with low-income populations",
                "Implementation challenges of plastic bag bans within budget constraints",
                "Cost analysis of enforcing plastic bag bans for small to mid-sized cities",
                "Community and business responses to proposed plastic bag bans"
            ]
        
        for i, query in enumerate(search_queries):
            st.markdown(f"**{i+1}. {query}**")
            
    # Policy Tournament Visualization
    st.subheader("Policy Tournament Process")
    st.markdown("""
    The final policy recommendations were developed through an evolutionary tournament process
    where policy options competed against each other based on effectiveness, feasibility, and fit with local context.
    """)
    
    # Create sample tournament data
    tournament_data = [
        {"round": 1, "policy1": "Biodegradable Bag Mandate", "policy2": "Complete Plastic Bag Ban", 
         "winner": "Biodegradable Bag Mandate", "reasoning": "Better feasibility and less economic disruption"},
        {"round": 1, "policy1": "Educational Campaign", "policy2": "Incentivized Reusable Program", 
         "winner": "Incentivized Reusable Program", "reasoning": "More direct impact on behavior"},
        {"round": 2, "policy1": "Biodegradable Bag Mandate", "policy2": "Incentivized Reusable Program", 
         "winner": "Comprehensive Plastic Bag Management", "reasoning": "Combined approach leverages strengths of both"},
        {"round": 2, "policy1": "Phased Implementation", "policy2": "Immediate Ban", 
         "winner": "Phased Implementation", "reasoning": "Better stakeholder acceptance and adaptation time"},
        {"round": 3, "policy1": "Comprehensive Plastic Bag Management", "policy2": "Phased Implementation", 
         "winner": "Enhanced Strategy for Phasing Out Single-Use Plastic Bags", "reasoning": "Integrated approach with robust implementation plan"}
    ]
    
    # Display tournament bracket visualization
    fig = go.Figure()
    
    # Create a tree-like structure for tournament visualization
    y_positions = {
        1: [5, 3, 1],
        2: [4, 2],
        3: [3]
    }
    
    # Add nodes for policies
    for round_num in range(1, 4):
        round_matches = [match for match in tournament_data if match["round"] <= round_num]
        
        for i, match in enumerate([m for m in round_matches if m["round"] == round_num]):
            # Policy 1 node
            fig.add_trace(go.Scatter(
                x=[round_num],
                y=[y_positions[round_num][i*2] if i*2 < len(y_positions[round_num]) else y_positions[round_num][-1]],
                mode="markers+text",
                marker=dict(size=15, color="royalblue"),
                text=[match["policy1"]],
                textposition="bottom center",
                hoverinfo="text",
                hovertext=f"Round {round_num}: {match['policy1']}"
            ))
            
            # Policy 2 node (for first two rounds)
            if round_num < 3:
                fig.add_trace(go.Scatter(
                    x=[round_num],
                    y=[y_positions[round_num][i*2+1] if i*2+1 < len(y_positions[round_num]) else y_positions[round_num][-1]],
                    mode="markers+text",
                    marker=dict(size=15, color="royalblue"),
                    text=[match["policy2"]],
                    textposition="bottom center",
                    hoverinfo="text",
                    hovertext=f"Round {round_num}: {match['policy2']}"
                ))
            
            # Winner node in the next round
            if round_num < 3:
                fig.add_trace(go.Scatter(
                    x=[round_num + 1],
                    y=[y_positions[round_num+1][i] if i < len(y_positions[round_num+1]) else y_positions[round_num+1][-1]],
                    mode="markers+text",
                    marker=dict(size=15, color="green"),
                    text=[match["winner"]],
                    textposition="bottom center",
                    hoverinfo="text",
                    hovertext=f"Winner: {match['winner']}<br>Reasoning: {match['reasoning']}"
                ))
                
                # Connect with lines
                fig.add_trace(go.Scatter(
                    x=[round_num, round_num + 1],
                    y=[y_positions[round_num][i*2] if i*2 < len(y_positions[round_num]) else y_positions[round_num][-1], 
                       y_positions[round_num+1][i] if i < len(y_positions[round_num+1]) else y_positions[round_num+1][-1]],
                    mode="lines",
                    line=dict(color="gray", width=1),
                    hoverinfo="none"
                ))
                
                fig.add_trace(go.Scatter(
                    x=[round_num, round_num + 1],
                    y=[y_positions[round_num][i*2+1] if i*2+1 < len(y_positions[round_num]) else y_positions[round_num][-1], 
                       y_positions[round_num+1][i] if i < len(y_positions[round_num+1]) else y_positions[round_num+1][-1]],
                    mode="lines",
                    line=dict(color="gray", width=1),
                    hoverinfo="none"
                ))
    
    fig.update_layout(
        title="Policy Tournament Visualization",
        xaxis=dict(
            title="Tournament Rounds",
            tickvals=[1, 2, 3],
            ticktext=["Initial Proposals", "Refinement", "Final Selection"]
        ),
        yaxis=dict(
            showticklabels=False,
            zeroline=False
        ),
        showlegend=False,
        height=400,
        hovermode="closest"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparison reasoning details
    st.subheader("Key Comparison Insights")
    
    for match in tournament_data:
        with st.expander(f"Round {match['round']}: {match['policy1']} vs {match['policy2']}"):
            st.markdown(f"**Winner:** {match['winner']}")
            st.markdown(f"**Reasoning:** {match['reasoning']}")
            st.markdown("**Detailed Analysis:**")
            
            # This would come from your actual agent trace data
            st.markdown("""
            * **Environmental Impact:** The winning policy provides stronger long-term environmental benefits
            * **Economic Feasibility:** Implementation costs are manageable within the $25,000 budget constraint
            * **Stakeholder Acceptance:** The approach addresses concerns of both businesses and residents
            * **Implementation Timeline:** Can be executed within the current political landscape
            * **Equity Considerations:** Special provisions for low-income residents ensure fair implementation
            """)
    
    # Agent Information
    st.subheader("AI Agent Information")
    
    # Create columns for different agent metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Agents Used", "5", "Policy Evolution System")
    
    with col2:
        st.metric("Total Tokens", "5,291", "771 avg per agent")
    
    with col3:
        st.metric("Analysis Depth", "High", "Multiple rounds of refinement")
    
    # Model information
    st.markdown("### Model Information")
    st.markdown("All policy analysis was performed using **GPT-4o (2024-08-06)** with multi-agent orchestration")
    
    # Add link to OpenAI trace for advanced users
    if st.button("View Complete AI Trace"):
        st.info("This would link to the OpenAI trace data for this analysis session")

# Add help text at the bottom
st.markdown("---")
st.caption("This interactive dashboard visualizes policy analysis results from the CivicAide Policy Analysis System.")
st.caption("To see other policy reports, select them from the dropdown in the sidebar.")

# Add the ability to create this dashboard from any policy report
st.markdown("---")
st.subheader("Create Your Own Dashboard")

with st.expander("Generate dashboard for any policy report"):
    st.write("To visualize your own policy report, enter its path below:")
    
    custom_path = st.text_input("Path to policy report file (Markdown format)")
    
    if st.button("Generate Dashboard"):
        if custom_path and os.path.exists(custom_path):
            policy_data = load_policy_data(custom_path)
            st.success(f"Dashboard generated for {os.path.basename(custom_path)}. Please refresh to see changes.")
        else:
            st.error("File not found. Please check the path and try again.") 