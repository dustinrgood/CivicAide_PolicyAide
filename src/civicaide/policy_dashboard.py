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
import requests
from datetime import datetime, timedelta
import random

# Try to get the OpenAI API key from environment variables or secrets
api_key = os.environ.get("OPENAI_API_KEY")
# If not in environment variables, try to get from streamlit secrets
if not api_key:
    try:
        if 'openai_api_key' in st.secrets:
            api_key = st.secrets['openai_api_key']
            # Check if it's still a placeholder
            if api_key == "YOUR_OPENAI_API_KEY_HERE":
                api_key = None
                st.warning("OpenAI API key is set to a placeholder value. Please update it in .streamlit/secrets.toml or set the OPENAI_API_KEY environment variable.")
    except:
        # Secrets not available or not configured
        pass

if not api_key:
    st.warning("OpenAI API key not found. Some features requiring API access will be disabled. Please set your API key in .streamlit/secrets.toml or as an environment variable.")

# Only set page config if not running from app.py
if os.environ.get("STREAMLIT_RUN_VIA_APP") != "true":
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
        max-width: 95% !important;
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

# Function to fetch OpenAI trace data
def fetch_openai_trace(trace_id, api_key=None):
    """
    Fetch trace data from OpenAI's API
    
    Args:
        trace_id (str): The ID of the trace to fetch
        api_key (str, optional): OpenAI API key. Defaults to environment variable.
        
    Returns:
        dict: The trace data if successful, None otherwise
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
        # Try to get from streamlit secrets if available
        try:
            if not api_key and 'openai_api_key' in st.secrets:
                api_key = st.secrets['openai_api_key']
        except:
            # Secrets not available or not configured
            pass
        
    if not api_key:
        # Log the issue but don't show errors to users
        print("No OpenAI API key provided. Set the OPENAI_API_KEY environment variable.")
        return None
        
    if not trace_id:
        print("No trace ID provided.")
        return None
    
    # Check if this is a locally generated trace ID (starts with 'trace_')
    if trace_id.startswith("trace_") and not trace_id.startswith("trace-"):
        # This is a local trace, not an OpenAI trace ID
        print(f"Using local trace data for {trace_id} (not an OpenAI trace ID)")
        
        # Look for local trace file
        local_trace_files = glob.glob(f"src/civicaide/traces/*{trace_id}*.json")
        if local_trace_files:
            # Sort by modification time (newest first)
            local_trace_files.sort(key=os.path.getmtime, reverse=True)
            try:
                with open(local_trace_files[0], 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading local trace file: {e}")
                return None
        
        # If we don't find a local file, create mock data
        print(f"Creating mock trace data for local trace ID: {trace_id}")
        return {
            "id": trace_id,
            "workflow_name": "Local Policy Workflow",
            "created_at": datetime.now().isoformat(),
            "spans": [
                {
                    "id": "span_1",
                    "name": "Policy Analysis Agent",
                    "type": "agent.planning",
                    "status": "success",
                    "parent_id": None,
                    "started_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
                    "ended_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
                    "duration_ms": 60000,
                    "input": {"query": "Policy planning"},
                    "output": {"plan": "Generated policy plan"}
                }
            ]
        }
    
    # This is an OpenAI trace ID, so fetch from the API
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "traces=v1"
        }
        
        # The endpoint for fetching a specific trace
        endpoint = f"https://api.openai.com/v1/traces/{trace_id}"
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            print(f"Successfully fetched OpenAI trace: {trace_id}")
            return response.json()
        elif response.status_code == 404:
            # For 404 errors, create a fake trace with a clear message
            print(f"Trace not found (404): {trace_id}")
            return {
                "id": trace_id,
                "workflow_name": "Sample Workflow (Trace Not Found)",
                "created_at": datetime.now().isoformat(),
                "status": "not_found",
                "spans": [
                    {
                        "id": "span_1",
                        "name": "Sample Span",
                        "type": "sample",
                        "status": "success",
                        "parent_id": None,
                        "started_at": datetime.now().isoformat(),
                        "ended_at": datetime.now().isoformat(),
                        "duration_ms": 1000,
                        "input": {
                            "message": "This is a sample trace because the requested trace was not found"
                        },
                        "output": {
                            "message": "This is a sample output for demonstration purposes"
                        }
                    }
                ]
            }
        else:
            print(f"Error fetching trace: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error fetching trace: {str(e)}")
        return None

# Function to parse trace data for visualization
def parse_trace_data(trace_data):
    """
    Parse trace data into a format suitable for visualization
    
    Args:
        trace_data (dict): The raw trace data from OpenAI
        
    Returns:
        tuple: (spans_df, events_df, metadata) DataFrames for spans and events, and metadata dict
    """
    if not trace_data or "spans" not in trace_data:
        return pd.DataFrame(), pd.DataFrame(), {}
    
    # Extract basic metadata
    metadata = {
        "trace_id": trace_data.get("id", "Unknown"),
        "workflow_name": trace_data.get("workflow_name", "Unknown"),
        "created_at": trace_data.get("created_at", "Unknown"),
    }
    
    # Process spans
    spans = []
    for span in trace_data.get("spans", []):
        span_data = {
            "span_id": span.get("id", ""),
            "name": span.get("name", ""),
            "type": span.get("type", ""),
            "status": span.get("status", ""),
            "parent_id": span.get("parent_id", ""),
            "started_at": span.get("started_at", ""),
            "ended_at": span.get("ended_at", ""),
            "duration_ms": span.get("duration_ms", 0),
        }
        spans.append(span_data)
    
    # Create spans DataFrame
    spans_df = pd.DataFrame(spans)
    
    # Process events (inputs/outputs)
    events = []
    for span in trace_data.get("spans", []):
        span_id = span.get("id", "")
        
        # Process input events
        if "input" in span:
            event_data = {
                "span_id": span_id,
                "type": "input",
                "timestamp": span.get("started_at", ""),
                "content": json.dumps(span["input"])[:500] + "..." if len(json.dumps(span["input"])) > 500 else json.dumps(span["input"]),
                "raw_content": span["input"]
            }
            events.append(event_data)
        
        # Process output events
        if "output" in span:
            event_data = {
                "span_id": span_id,
                "type": "output",
                "timestamp": span.get("ended_at", ""),
                "content": json.dumps(span["output"])[:500] + "..." if len(json.dumps(span["output"])) > 500 else json.dumps(span["output"]),
                "raw_content": span["output"]
            }
            events.append(event_data)
    
    # Create events DataFrame
    events_df = pd.DataFrame(events)
    
    return spans_df, events_df, metadata

# Add a class to manage trace capturing
class TraceCapture:
    """Class to capture and store trace data during policy generation process"""
    
    def __init__(self):
        self.traces = {}  # Dictionary to store trace data, keyed by policy_id
        
    def capture_trace(self, policy_id, agent_name, trace_id=None):
        """
        Capture trace data for a specific policy generation process
        
        Args:
            policy_id: Unique identifier for the policy
            agent_name: Name of the agent (e.g., "Research Planner", "Policy Generation")
            trace_id: If known, the specific trace ID to fetch
        """
        # In a real implementation, this would be called after each agent completes
        # For now, we'll simulate by storing the agent name and other metadata
        if policy_id not in self.traces:
            self.traces[policy_id] = []
            
        # If we have a trace_id, try to fetch actual trace data
        trace_data = None
        if trace_id:
            # Check if API key is available
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                try:
                    trace_data = fetch_openai_trace(trace_id, api_key)
                except Exception as e:
                    print(f"Error fetching trace: {str(e)}")
            
            if not trace_data:
                # Don't show an error, just log that we couldn't fetch trace data
                try:
                    if 'openai_api_key' in st.secrets:
                        # Try using secrets if available
                        try:
                            trace_data = fetch_openai_trace(trace_id, st.secrets["openai_api_key"])
                        except Exception as e:
                            print(f"Error fetching trace with secrets: {str(e)}")
                except:
                    # Secrets not available
                    pass
                
                if not trace_data:
                    print(f"No API key available or error occurred fetching trace {trace_id}")
                    # Create fake/mock trace data for demo purposes
                    trace_data = {
                        "id": trace_id,
                        "workflow_name": f"{agent_name} Workflow",
                        "created_at": datetime.now().isoformat(),
                        "spans": [
                            {
                                "id": "span_1",
                                "name": f"{agent_name} Planning",
                                "type": "agent.planning",
                                "status": "success",
                                "parent_id": None,
                                "started_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
                                "ended_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
                                "duration_ms": 60000,
                                "input": {"query": "Policy planning"},
                                "output": {"plan": "Generated policy plan"}
                            },
                            {
                                "id": "span_2",
                                "name": f"{agent_name} Execution",
                                "type": "agent.execution",
                                "status": "success",
                                "parent_id": "span_1",
                                "started_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
                                "ended_at": (datetime.now() - timedelta(minutes=2)).isoformat(),
                                "duration_ms": 120000,
                                "input": {"plan": "Generated policy plan"},
                                "output": {"result": "Policy execution completed"}
                            }
                        ]
                    }
                    print(f"Created mock trace data for {agent_name}")
        
        # Store the trace information
        self.traces[policy_id].append({
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "trace_id": trace_id,
            "trace_data": trace_data
        })
        
    def get_traces(self, policy_id):
        """Get all traces for a specific policy"""
        return self.traces.get(policy_id, [])

# Create a global instance
TRACE_MANAGER = TraceCapture()

# Function to load policy data from markdown files
def load_policy_data(file_path=None):
    """
    Load policy data from a file or return demo data
    """
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Parse the markdown content
        data = parse_policy_markdown(content)
        
        # Generate a policy_id from the file name
        policy_id = os.path.basename(file_path).replace('.md', '')
        
        # Look for corresponding trace files
        trace_files = glob.glob(f"src/civicaide/traces/*_{policy_id}_*.json")
        if trace_files:
            # Sort by date (newest first)
            trace_files.sort(key=os.path.getmtime, reverse=True)
            latest_trace = trace_files[0]
            
            # Extract trace data
            try:
                with open(latest_trace, 'r') as f:
                    trace_data = json.load(f)
                    
                # Store trace ID if available
                if 'trace_id' in trace_data:
                    data['trace_id'] = trace_data['trace_id']
                    
                # Store path to trace file
                data['trace_file'] = latest_trace
            except:
                # If we can't load the trace, just continue
                pass
        
        # If we don't have traces for this policy yet, simulate capturing them
        if policy_id not in TRACE_MANAGER.traces:
            # In a real implementation, these would be captured during generation
            # For demo purposes, we'll simulate pre-captured traces
            TRACE_MANAGER.capture_trace(policy_id, "Research Planner Agent", 
                                       trace_id="trace_6ea168d55a84a5bbe1c58b5a1f30427")
            TRACE_MANAGER.capture_trace(policy_id, "Initial Policy Generation")
            TRACE_MANAGER.capture_trace(policy_id, "Policy Generation Agent")
            TRACE_MANAGER.capture_trace(policy_id, "Policy Tournament")
            TRACE_MANAGER.capture_trace(policy_id, "Policy Comparison Agent")
            TRACE_MANAGER.capture_trace(policy_id, "Policy Evolution Agent")
        
        data['policy_id'] = policy_id
        return data
    else:
        # Return demo data if no file provided or file doesn't exist
        demo_data = {
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
            ],
            'policy_id': 'demo_plastic_bag_policy'
        }
        
        # Add simulated traces for the demo policy
        if 'demo_plastic_bag_policy' not in TRACE_MANAGER.traces:
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Research Planner Agent",
                                       trace_id="trace_6ea168d55a84a5bbe1c58b5a1f30427")
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Initial Policy Generation")
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Policy Generation Agent")
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Policy Tournament")
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Policy Comparison Agent")
            TRACE_MANAGER.capture_trace('demo_plastic_bag_policy', "Policy Evolution Agent")
            
        return demo_data

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

# Function to parse policy markdown content
def parse_policy_markdown(content):
    """Parse policy data from markdown content"""
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
    
    # Check for trace data reference
    trace_section = re.search(r'Trace data: \[View execution trace\]\((.*?)\)', content)
    if trace_section:
        trace_path = trace_section.group(1).replace('file://', '')
        if os.path.exists(trace_path):
            data['trace_file'] = trace_path
            
            # Get trace ID if available
            try:
                with open(trace_path, 'r') as f:
                    trace_data = json.load(f)
                    if 'trace_id' in trace_data:
                        data['trace_id'] = trace_data['trace_id']
            except:
                pass
    
    return data

# Add a main function that will be called from app.py
def main():
    """Main function for the policy dashboard when run as a module"""
    # Debug info
    st.sidebar.success("Policy Dashboard loaded successfully!")
    
    st.title("CivicAide Policy Dashboard")
    
    # Find policy files
    policy_files = find_policy_files()

    if policy_files:
        selected_file = st.selectbox(
            "Select Policy Report",
            options=policy_files,
            format_func=lambda x: os.path.basename(x)
        )
        policy_data = load_policy_data(selected_file)
    else:
        st.warning("No policy report files found. Using demo data.")
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
    st.header(f"Policy Analysis: {policy_data['query']}")

    # Show trace data if available
    if 'trace_id' in policy_data and 'trace_file' in policy_data:
        trace_id = policy_data['trace_id']
        trace_path = policy_data['trace_file']
        trace_link = f"[View Trace](?tab=Trace%20Viewer&trace_id={trace_id})"
        
        st.markdown(f"<div style='text-align: right;'>{trace_link}</div>", unsafe_allow_html=True)
        
        # Add badge to show trace is available
        st.markdown(f"<div style='text-align: right;'><span style='background-color: #f0f2f6; padding: 5px 10px; border-radius: 10px;'>📊 Agent Trace Available</span></div>", unsafe_allow_html=True)

    # Or find all associated traces by policy ID
    policy_id = os.path.basename(selected_file).replace('.md', '')
    trace_files = glob.glob(f"src/civicaide/traces/*_{policy_id}_*.json")

    if trace_files and not ('trace_id' in policy_data and 'trace_file' in policy_data):
        # Sort by date (newest first)
        trace_files.sort(key=os.path.getmtime, reverse=True)
        
        try:
            with open(trace_files[0], 'r') as f:
                trace_data = json.load(f)
                if 'trace_id' in trace_data:
                    trace_id = trace_data['trace_id']
                    trace_link = f"[View Trace](?tab=Trace%20Viewer&trace_id={trace_id})"
                    st.markdown(f"<div style='text-align: right;'>{trace_link}</div>", unsafe_allow_html=True)
                    
                    # Add badge to show trace is available
                    st.markdown(f"<div style='text-align: right;'><span style='background-color: #f0f2f6; padding: 5px 10px; border-radius: 10px;'>📊 Agent Trace Available</span></div>", unsafe_allow_html=True)
        except:
            pass

    # Show policy summary
    st.markdown("### Executive Summary")
    st.markdown(policy_data['summary'])

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Policy Proposals", "Impact Analysis", "Stakeholder Analysis", "Implementation", "Research & Context", "Agent Traces"])

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
            try:
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
            except Exception as e:
                st.error(f"Error creating tournament visualization: {str(e)}")
                
                # Fallback - display text-based tournament results
                st.write("**Tournament Results:**")
                for i, match in enumerate(tournament_data):
                    st.write(f"**Round {match['round']}:** {match['policy1']} vs {match['policy2']} → Winner: {match['winner']}")

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
                # Extract the trace ID from the URL if provided via URL param
                query_params = st.experimental_get_query_params()
                trace_id = query_params.get("trace_id", [""])[0]
                
                if trace_id:
                    # Set the trace ID in session state and switch to the trace viewer tab
                    st.session_state.trace_id_to_load = trace_id
                    st.experimental_set_query_params(tab="trace_viewer", trace_id=trace_id)
                    st.success(f"Loading trace: {trace_id}. Please navigate to the Trace Viewer tab.")
                else:
                    # Prompt for trace ID
                    st.info("To view the complete AI trace, navigate to the Trace Viewer tab and enter the trace ID.")
                    # Switch to trace viewer tab
                    st.experimental_set_query_params(tab="trace_viewer")

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

    # Trace Viewer Tab
    with tab6:
        st.subheader("AI Agent Workflow")
        
        # Find all trace files related to this policy
        trace_files = []
        policy_keyword = policy_data['query'].lower().replace(" ", "_")
        
        for file in glob.glob("src/civicaide/traces/*.json"):
            try:
                with open(file, 'r') as f:
                    trace_data = json.load(f)
                    if policy_keyword in trace_data.get("query", "").lower():
                        trace_files.append(file)
            except:
                pass
        
        if trace_files:
            trace_files.sort(key=os.path.getmtime, reverse=True)
            
            # Show the most recent trace by default
            selected_trace = trace_files[0]
            
            with open(selected_trace, 'r') as f:
                trace_data = json.load(f)
            
            # Show key trace information
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Analysis Type:** {trace_data.get('policy_type', 'Policy Analysis').title()}")
                st.markdown(f"**Trace ID:** {trace_data.get('trace_id', 'Unknown')}")
            
            with col2:
                if "timestamp" in trace_data:
                    st.markdown(f"**Date:** {trace_data['timestamp']}")
                st.markdown(f"**Number of Steps:** {len(trace_data.get('spans', []))}")
            
            # Show a sample of agent interaction
            st.subheader("Sample Agent Interaction")
            
            # Extract agent names
            agents = set()
            for span in trace_data.get("spans", []):
                agent_name = span.get("details", {}).get("agent_name", "System")
                if agent_name:
                    agents.add(agent_name)
            
            # Show agent list
            st.markdown("**Agents Involved:**")
            st.write(", ".join(sorted(agents)))
            
            # Create a simplified timeline
            timeline_data = []
            for span in trace_data.get("spans", [])[:10]:  # Show only first 10 for simplicity
                agent_name = span.get("details", {}).get("agent_name", "System")
                span_type = span.get("span_type", "unknown")
                
                if agent_name and span_type:
                    timeline_data.append({
                        "Agent": agent_name,
                        "Action": span_type
                    })
            
            if timeline_data:
                st.dataframe(pd.DataFrame(timeline_data))
            
            # Link to full trace dashboard
            st.info("This is a simplified view of the agent workflow. For a detailed visualization, check the dedicated Trace Dashboard.")
            
            if st.button("Open Full Trace Dashboard"):
                # In a real application, you'd link to the trace dashboard
                st.markdown("In a production application, this would open the full trace dashboard.")
        else:
            st.info("No trace data found for this policy query. Run a policy analysis to generate trace data.")

# This part will only execute when the file is run directly, not when imported
if __name__ == "__main__":
    # Sidebar for file selection and controls
    st.sidebar.title("CivicAide Policy Dashboard")
    st.sidebar.image("https://img.icons8.com/color/96/000000/government.png", width=100)
    
    # Run the main function
    main() 