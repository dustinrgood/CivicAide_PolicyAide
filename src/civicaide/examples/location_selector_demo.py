#!/usr/bin/env python
"""
Streamlit app to select a U.S. state and its corresponding counties.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from local.env
env_path = os.path.join(os.path.dirname(__file__), '..', 'local.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Environment file not found at {env_path}")

# Retrieve the Census API key from environment variables
CENSUS_API_KEY = os.getenv('CENSUS_API_KEY')
if not CENSUS_API_KEY:
    st.error("Census API key is not set. Please set the CENSUS_API_KEY environment variable.")
    st.stop()

# Function to fetch all states from the Census API
@st.cache_data
def fetch_states():
    url = f'https://api.census.gov/data/2020/dec/responserate?get=NAME&for=state:*&key={CENSUS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()[1:]  # Skip the header row
        state_dict = {state[0]: state[1] for state in data}
        return state_dict
    else:
        st.error(f"Failed to fetch states: {response.text}")
        return {}

# Function to fetch counties for a given state FIPS code
@st.cache_data
def fetch_counties(state_fips):
    url = f'https://api.census.gov/data/2020/dec/responserate?get=NAME&for=county:*&in=state:{state_fips}&key={CENSUS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()[1:]  # Skip the header row
        counties = [county[0] for county in data]
        return counties
    else:
        st.error(f"Failed to fetch counties: {response.text}")
        return []

def main():
    st.set_page_config(
        page_title="Location Selector",
        page_icon="🌍",
        layout="wide"
    )

    st.title("🌍 Location Selector")
    st.markdown("""
    Select a U.S. state to view its corresponding counties.
    """)

    # Fetch the list of states
    state_dict = fetch_states()
    if not state_dict:
        st.stop()

    # State selection dropdown
    state_name = st.selectbox("Select a state:", options=list(state_dict.keys()))
    state_fips = state_dict[state_name]

    # Fetch and display counties for the selected state
    counties = fetch_counties(state_fips)
    if counties:
        county_name = st.selectbox("Select a county:", options=counties)
        st.success(f"You have selected {county_name} County in {state_name}.")
    else:
        st.warning(f"No counties found for {state_name}.")

if __name__ == "__main__":
    main()
