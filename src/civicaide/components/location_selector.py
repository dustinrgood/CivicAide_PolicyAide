"""
Location selector component for CivicAide.

This module provides a Streamlit component for selecting a location (state, county, city)
using pre-populated dropdown lists from Census data.
"""

import streamlit as st
import logging
from typing import Dict, Any, Tuple, Optional, List, Callable

# Import our location data utilities
from src.civicaide.utils.location_data import (
    get_states_for_dropdown,
    get_counties_for_dropdown,
    get_places_for_dropdown,
    fetch_place_data,
    get_government_structures
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def location_selector(
    on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
    key_prefix: str = "location"
) -> Dict[str, Any]:
    """
    Streamlit component for selecting a location.
    
    Args:
        on_submit: Optional callback function to call when form is submitted
        key_prefix: Prefix for Streamlit session state keys
        
    Returns:
        Dictionary with selected location data
    """
    # Initialize session state for selected values
    if f"{key_prefix}_state_fips" not in st.session_state:
        st.session_state[f"{key_prefix}_state_fips"] = ""
    if f"{key_prefix}_county_fips" not in st.session_state:
        st.session_state[f"{key_prefix}_county_fips"] = ""
    if f"{key_prefix}_place_fips" not in st.session_state:
        st.session_state[f"{key_prefix}_place_fips"] = ""
    if f"{key_prefix}_place_search" not in st.session_state:
        st.session_state[f"{key_prefix}_place_search"] = ""
    if f"{key_prefix}_government_structure" not in st.session_state:
        st.session_state[f"{key_prefix}_government_structure"] = ""
    if f"{key_prefix}_selected_data" not in st.session_state:
        st.session_state[f"{key_prefix}_selected_data"] = {}
    
    # Create a form for selecting location
    with st.form(key=f"{key_prefix}_form"):
        st.subheader("Select your location")
        
        # Get states for dropdown
        states = get_states_for_dropdown()
        
        # State selection
        selected_state_fips = st.selectbox(
            "State",
            options=[s["value"] for s in states],
            format_func=lambda x: next((s["label"] for s in states if s["value"] == x), ""),
            key=f"{key_prefix}_state_select"
        )
        
        # Only show county selection if state is selected
        if selected_state_fips:
            # Find state name
            state_name = next((s["label"] for s in states if s["value"] == selected_state_fips), "Unknown")
            logger.info(f"Selected state: {state_name} with FIPS: {selected_state_fips}")
            
            # Map state names directly to known FIPS codes to avoid any potential mismatch
            state_fips_map = {
                "Alabama": "01",
                "Illinois": "17",
                "New York": "36",
                "California": "06",
                "Texas": "48"
            }
            
            # Override selected FIPS if we have a hardcoded value
            if state_name in state_fips_map:
                corrected_fips = state_fips_map[state_name]
                if selected_state_fips != corrected_fips:
                    logger.warning(f"Correcting {state_name} FIPS from {selected_state_fips} to {corrected_fips}")
                    selected_state_fips = corrected_fips
            
            # For Illinois, always use hardcoded counties to guarantee correct data
            if state_name == "Illinois":
                logger.info("ILLINOIS SELECTED - Using hardcoded Illinois counties")
                counties = [
                    {"value": "17001", "label": "Adams County"},
                    {"value": "17003", "label": "Alexander County"},
                    {"value": "17005", "label": "Bond County"},
                    {"value": "17007", "label": "Boone County"},
                    {"value": "17009", "label": "Brown County"},
                    {"value": "17011", "label": "Bureau County"},
                    {"value": "17013", "label": "Calhoun County"},
                    {"value": "17015", "label": "Carroll County"},
                    {"value": "17017", "label": "Cass County"},
                    {"value": "17019", "label": "Champaign County"},
                    {"value": "17021", "label": "Christian County"},
                    {"value": "17023", "label": "Clark County"},
                    {"value": "17025", "label": "Clay County"},
                    {"value": "17027", "label": "Clinton County"},
                    {"value": "17029", "label": "Coles County"},
                    {"value": "17031", "label": "Cook County"},
                    {"value": "17033", "label": "Crawford County"},
                    {"value": "17035", "label": "Cumberland County"},
                    {"value": "17037", "label": "DeKalb County"},
                    {"value": "17039", "label": "De Witt County"},
                    {"value": "17041", "label": "Douglas County"},
                    {"value": "17043", "label": "DuPage County"},
                    {"value": "17045", "label": "Edgar County"},
                    {"value": "17047", "label": "Edwards County"},
                    {"value": "17049", "label": "Effingham County"},
                    {"value": "17051", "label": "Fayette County"},
                    {"value": "17053", "label": "Ford County"},
                    {"value": "17055", "label": "Franklin County"},
                    {"value": "17057", "label": "Fulton County"},
                    {"value": "17059", "label": "Gallatin County"},
                    {"value": "17061", "label": "Greene County"},
                    {"value": "17063", "label": "Grundy County"},
                    {"value": "17065", "label": "Hamilton County"},
                    {"value": "17067", "label": "Hancock County"},
                    {"value": "17069", "label": "Hardin County"},
                    {"value": "17071", "label": "Henderson County"},
                    {"value": "17073", "label": "Henry County"},
                    {"value": "17075", "label": "Iroquois County"},
                    {"value": "17077", "label": "Jackson County"},
                    {"value": "17079", "label": "Jasper County"},
                    {"value": "17081", "label": "Jefferson County"},
                    {"value": "17083", "label": "Jersey County"},
                    {"value": "17085", "label": "Jo Daviess County"},
                    {"value": "17087", "label": "Johnson County"},
                    {"value": "17089", "label": "Kane County"},
                    {"value": "17091", "label": "Kankakee County"},
                    {"value": "17093", "label": "Kendall County"},
                    {"value": "17095", "label": "Knox County"},
                    {"value": "17097", "label": "Lake County"},
                    {"value": "17099", "label": "La Salle County"},
                    {"value": "17101", "label": "Lawrence County"},
                    {"value": "17103", "label": "Lee County"},
                    {"value": "17105", "label": "Livingston County"},
                    {"value": "17107", "label": "Logan County"},
                    {"value": "17109", "label": "McDonough County"},
                    {"value": "17111", "label": "McHenry County"},
                    {"value": "17113", "label": "McLean County"},
                    {"value": "17115", "label": "Macon County"}
                ]
                logger.info(f"Set {len(counties)} hardcoded counties for Illinois")
            else:
                # Get counties for selected state - ensure we're using the correct FIPS code
                try:
                    # Force string type for state_fips and ensure it's exactly 2 characters
                    state_fips_fixed = selected_state_fips.strip()
                    if len(state_fips_fixed) == 1:
                        state_fips_fixed = f"0{state_fips_fixed}"
                    
                    logger.info(f"Fetching counties using state FIPS: {state_fips_fixed} for {state_name}")
                    counties = get_counties_for_dropdown(state_fips_fixed)
                    logger.info(f"Got {len(counties)} counties for {state_name}")
                    
                    if counties:
                        logger.info(f"First few counties: {[c['label'] for c in counties[:5]] if len(counties) >= 5 else [c['label'] for c in counties]}")
                except Exception as e:
                    logger.error(f"Error fetching counties: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    counties = []
            
            # County selection
            selected_county_fips = st.selectbox(
                "County",
                options=[""] + [c["value"] for c in counties],
                format_func=lambda x: "" if not x else next((c["label"] for c in counties if c["value"] == x), ""),
                key=f"{key_prefix}_county_select"
            )
            
            # Place search box
            place_search = st.text_input(
                "Search for your city/town",
                key=f"{key_prefix}_place_search_input"
            )
            
            # Only show place selection if search term is provided
            if place_search and len(place_search) >= 2:
                # Get places for selected state filtered by search
                places = get_places_for_dropdown(selected_state_fips, place_search)
                
                # Place selection
                if places:
                    selected_place_fips = st.selectbox(
                        "City/Town",
                        options=[""] + [p["value"] for p in places],
                        format_func=lambda x: "" if not x else next((p["label"] for p in places if p["value"] == x), ""),
                        key=f"{key_prefix}_place_select"
                    )
                else:
                    st.warning("No places found matching your search. Please try a different search term.")
                    selected_place_fips = ""
            else:
                if place_search:
                    st.info("Please enter at least 2 characters to search for your city/town.")
                selected_place_fips = ""
            
            # Government structure selection
            gov_structures = get_government_structures()
            selected_gov_structure = st.selectbox(
                "Government Structure",
                options=[""] + [g["name"] for g in gov_structures],
                key=f"{key_prefix}_gov_structure_select",
                help="The type of government structure for your municipality."
            )
            
            # Show description if government structure is selected
            if selected_gov_structure:
                for structure in gov_structures:
                    if structure["name"] == selected_gov_structure:
                        st.info(structure["description"])
        else:
            selected_county_fips = ""
            selected_place_fips = ""
            selected_gov_structure = ""
        
        # Submit button
        submit_button = st.form_submit_button("Continue")
        
        if submit_button:
            # Validate form
            if not selected_state_fips:
                st.error("Please select a state.")
                return {}
            
            if not selected_county_fips:
                st.warning("County selection is recommended but not required.")
            
            if not selected_place_fips:
                st.error("Please select a city/town.")
                return {}
            
            if not selected_gov_structure:
                st.warning("Government structure selection is recommended but not required.")
            
            # Fetch detailed place data
            place_data = fetch_place_data(selected_state_fips, selected_place_fips)
            
            if not place_data:
                st.error("Could not fetch data for the selected place. Please try again.")
                return {}
            
            # Prepare result data
            result = {
                "city": place_data["name"],
                "state": place_data["state"],
                "state_abbr": place_data["state_abbr"],
                "county": next((c["label"] for c in get_counties_for_dropdown(selected_state_fips) if c["value"] == selected_county_fips), "Unknown"),
                "state_fips": selected_state_fips,
                "county_fips": selected_county_fips.replace(selected_state_fips, "") if selected_county_fips else "",
                "place_fips": selected_place_fips,
                "population": place_data.get("population", 0),
                "government_structure": selected_gov_structure
            }
            
            # Save to session state
            st.session_state[f"{key_prefix}_state_fips"] = selected_state_fips
            st.session_state[f"{key_prefix}_county_fips"] = selected_county_fips
            st.session_state[f"{key_prefix}_place_fips"] = selected_place_fips
            st.session_state[f"{key_prefix}_government_structure"] = selected_gov_structure
            st.session_state[f"{key_prefix}_selected_data"] = result
            
            # Call on_submit callback if provided
            if on_submit:
                on_submit(result)
            
            return result
    
    # Return empty dict if form not submitted
    return {}

def display_location_info(location_data: Dict[str, Any]):
    """
    Display location information.
    
    Args:
        location_data: Dictionary with location data
    """
    if not location_data:
        return
    
    st.subheader("Location Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**City/Town:** {location_data.get('city', 'N/A')}")
        st.markdown(f"**County:** {location_data.get('county', 'N/A')}")
        st.markdown(f"**State:** {location_data.get('state', 'N/A')} ({location_data.get('state_abbr', 'N/A')})")
    
    with col2:
        st.markdown(f"**Population:** {location_data.get('population', 'N/A'):,}")
        st.markdown(f"**Government Structure:** {location_data.get('government_structure', 'N/A')}")
        st.markdown(f"**FIPS Codes:** State: {location_data.get('state_fips', 'N/A')}, County: {location_data.get('county_fips', 'N/A')}, Place: {location_data.get('place_fips', 'N/A')}")

def main():
    """
    Main function for testing the location selector component.
    """
    st.set_page_config(
        page_title="CivicAide Location Selector",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("CivicAide Location Selector")
    st.markdown("Select your location to get started with CivicAide.")
    
    # Create a callback function for form submission
    def on_location_selected(data):
        st.success(f"Location selected: {data['city']}, {data['state_abbr']}")
    
    # Show the location selector
    location_data = location_selector(on_submit=on_location_selected)
    
    # If form was submitted, display location info
    if location_data:
        st.markdown("---")
        display_location_info(location_data)

if __name__ == "__main__":
    main() 