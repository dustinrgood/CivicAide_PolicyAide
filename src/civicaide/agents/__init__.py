"""
CivicAide Agents Package

This package contains the various agent implementations used in the CivicAide system.
"""

# Import common utilities
from .utils import (
    execute_web_searches,
    extract_json_from_text,
    safe_json_loads,
    with_retry,
    RetrySettings,
    ensure_directory_exists,
    read_json_file,
    write_json_file
)

# Import base agent definitions
from .base_agents import (
    web_search_agent,
    synthesis_agent,
    extract_json_from_markdown,
    parse_agent_output_as_json,
    run_with_error_handling,
    StakeholderImpact,
    ImplementationStep
)

# Import research agents
from .research_agents import (
    policy_research_planner,
    policy_research_synthesizer,
    perform_policy_searches,
    PolicySearchItem,
    PolicySearchPlan,
    PolicyResearchData
)

# Import analysis agents
from .analysis_agents import (
    policy_generation_agent,
    policy_evaluation_agent,
    policy_judge_agent,
    policy_refinement_agent,
    policy_meta_review_agent,
    generate_and_evaluate_proposals,
    select_and_refine_proposal,
    create_final_report,
    PolicyProposal,
    PolicyProposalSet,
    RefinedPolicyProposal
)

# Import evolution agents
from .evolution_agents import (
    policy_context_agent,
    policy_creator_agent,
    policy_comparison_agent,
    policy_evolution_agent,
    final_report_agent,
    create_initial_proposals,
    run_proposal_tournament,
    evolve_proposals,
    create_final_policy_report,
    EloRating,
    PolicyProposalModel,
    PolicyProposalBatch,
    ComparisonResult,
    EvolutionResult,
    FinalReportModel
)

# Import context gathering agents
from .context_agents import (
    census_data_agent,
    economic_data_agent,
    government_structure_agent,
    policy_context_agent as policy_context_researcher_agent,  # Renamed to avoid conflict
    profile_creation_agent,
    gather_base_local_context,
    gather_policy_specific_context,
    create_full_policy_context,
    CensusAPI,
    LocationInfo,
    DemographicData,
    EconomicData,
    GovernmentStructure,
    PolicyContext,
    BaseLocalContext,
    FullPolicyContext
)

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple

@dataclass
class LocationInfo:
    """Information about a location/jurisdiction."""
    city: str
    state: str
    county: Optional[str] = None
    country: str = "USA"
    zip_codes: Optional[List[str]] = None
    
# Placeholder functions for context gathering
def gather_base_local_context(location: LocationInfo) -> Dict[str, Any]:
    """Gather base local context for a location.
    
    Note: This is a synchronous wrapper for the async function in context_agents.py.
    For asynchronous use, import gather_base_local_context directly from context_agents.
    
    Args:
        location: Location information
        
    Returns:
        Dictionary with local context data
    """
    # For demo purposes, it returns a placeholder
    return {
        "location": {
            "city": location.city,
            "state": location.state,
            "country": location.country,
        },
        "demographics": {
            "population": 964254,
            "median_age": 33.4,
            "racial_composition": {
                "White": 48.3,
                "Hispanic": 33.9,
                "Black": 7.8,
                "Asian": 7.3,
                "Other": 2.7
            }
        },
        "economics": {
            "major_industries": ["Technology", "Education", "Government", "Healthcare", "Entertainment"],
            "unemployment_rate": 3.2,
            "major_employers": ["University of Texas", "Dell Technologies", "Apple", "IBM", "Texas State Government"],
            "poverty_rate": 12.5
        },
        "government": {
            "government_type": "Council-Manager",
            "elected_officials": [
                {"title": "Mayor", "name": "Kirk Watson"},
                {"title": "City Manager", "name": "Spencer Cronk"},
                {"title": "City Council Member", "name": "Natasha Harper-Madison"}
            ],
            "departments": ["Public Works", "Parks and Recreation", "Police Department", "Fire Department"],
            "budget_info": {"total": 4500000000, "fiscal_year": "2023-2024"}
        }
    }

def gather_policy_specific_context(policy_area: str, location_info: Any) -> Dict[str, Any]:
    """Gather policy-specific context for a given policy area.
    
    Note: This is a synchronous wrapper for the async function in context_agents.py.
    For asynchronous use, import gather_policy_specific_context directly from context_agents.
    
    Args:
        policy_area: The policy area to research
        location_info: Basic location information
        
    Returns:
        Dictionary with policy-specific context
    """
    # For demo purposes, it returns a placeholder
    return {
        "policy_area": policy_area,
        "existing_regulations": [
            "City ordinance 20110804-022 (Single-Use Carryout Bag Ordinance)",
            "Texas Health and Safety Code §361.0961 (state preemption)",
            "Texas Supreme Court ruling on bag bans (June 2018)"
        ],
        "stakeholders": [
            {"name": "Austin Environmental Commission", "position": "Supportive"},
            {"name": "Texas Retail Association", "position": "Opposed"},
            {"name": "Local Environmental Groups", "position": "Strongly Supportive"}
        ],
        "similar_policies": [
            {"jurisdiction": "San Francisco, CA", "description": "Complete ban on plastic bags with 10¢ fee for alternatives"},
            {"jurisdiction": "Chicago, IL", "description": "7¢ tax on all bags (plastic and paper)"},
            {"jurisdiction": "Boston, MA", "description": "Ban on thin plastic bags, 5¢ fee for thicker bags and paper"}
        ],
        "recent_developments": [
            "Texas Legislature considered preemption bill HB 2416 in 2023",
            "Austin's Sustainability Office released impact report of original ban (2018)",
            "Local advocacy groups launched new campaign to reinstate bag ban (2022)"
        ]
    }

def create_full_policy_context(location: LocationInfo, policy_topic: str) -> Dict[str, Any]:
    """Create full policy context combining location data and policy-specific information.
    
    Note: This is a synchronous wrapper for the async function in context_agents.py.
    For asynchronous use, import create_full_policy_context directly from context_agents.
    
    Args:
        location: Location information
        policy_topic: Policy topic to research
        
    Returns:
        Dictionary with full policy context
    """
    # Combine the results from the two functions above
    base_context = gather_base_local_context(location)
    policy_context = gather_policy_specific_context(policy_topic, base_context["location"])
    
    return {
        "base_context": base_context,
        "policy_context": policy_context
    }

__all__ = [
    'LocationInfo',
    'gather_base_local_context',
    'gather_policy_specific_context',
    'create_full_policy_context'
] 