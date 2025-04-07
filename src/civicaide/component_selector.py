"""
Component Selector for CivicAide

This module helps users determine which policy component to use based on their needs,
providing clear guidance on the capabilities and appropriate use cases for each component.
"""

import os
import sys
from pathlib import Path
from enum import Enum, auto
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass

# Data models for component selection

class PolicyNeed(Enum):
    """Enumeration of common policy development needs."""
    BACKGROUND_RESEARCH = auto()
    GENERATE_OPTIONS = auto()
    EVALUATE_OPTIONS = auto()
    LOCAL_CONTEXT = auto()
    STAKEHOLDER_ANALYSIS = auto()
    IMPLEMENTATION_PLAN = auto()
    COMPREHENSIVE_SOLUTION = auto()
    REFINEMENT = auto()
    EVOLUTION = auto()

class UserExpertise(Enum):
    """User's level of expertise with policy development."""
    NOVICE = auto()
    INTERMEDIATE = auto()
    EXPERT = auto()

class TimeAvailable(Enum):
    """Amount of time available for policy development."""
    QUICK = auto()  # Under 10 minutes
    MEDIUM = auto()  # 10-30 minutes
    EXTENSIVE = auto()  # 30+ minutes

class ComponentType(Enum):
    """Types of policy components available in the system."""
    RESEARCH = auto()
    ANALYSIS = auto()
    EVOLUTION = auto()
    INTEGRATED = auto()
    CONTEXT = auto()

@dataclass
class ComponentRecommendation:
    """Recommendation for which component to use."""
    component_type: ComponentType
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    limitations: List[str]
    next_steps: List[str]

@dataclass
class UserProfile:
    """Profile of the user's needs and constraints."""
    primary_needs: List[PolicyNeed]
    expertise_level: UserExpertise
    time_available: TimeAvailable
    has_local_context: bool
    has_research: bool
    has_requirements: Optional[List[str]] = None
    
    def __post_init__(self):
        # Ensure primary_needs is a list
        if not isinstance(self.primary_needs, list):
            self.primary_needs = [self.primary_needs]
        
        # Ensure requirements is a list or None
        if self.has_requirements is not None and not isinstance(self.has_requirements, list):
            self.has_requirements = [self.has_requirements]

class ComponentSelector:
    """
    Helps users select the most appropriate component based on their needs.
    
    This class provides methods to guide users through the component selection process
    and recommend the most suitable component for their policy development needs.
    """
    
    def __init__(self):
        """Initialize the ComponentSelector."""
        # Component capabilities matrix
        self.component_capabilities = {
            ComponentType.RESEARCH: {
                "name": "Policy Research",
                "description": "Gathers evidence and information about a policy topic",
                "primary_strengths": [
                    PolicyNeed.BACKGROUND_RESEARCH
                ],
                "secondary_strengths": [
                    PolicyNeed.STAKEHOLDER_ANALYSIS
                ],
                "time_required": TimeAvailable.MEDIUM,
                "expertise_required": UserExpertise.NOVICE,
                "needs_local_context": False
            },
            ComponentType.ANALYSIS: {
                "name": "Policy Analysis",
                "description": "Generates, evaluates, and refines policy proposals",
                "primary_strengths": [
                    PolicyNeed.GENERATE_OPTIONS,
                    PolicyNeed.EVALUATE_OPTIONS
                ],
                "secondary_strengths": [
                    PolicyNeed.IMPLEMENTATION_PLAN
                ],
                "time_required": TimeAvailable.MEDIUM,
                "expertise_required": UserExpertise.NOVICE,
                "needs_local_context": False
            },
            ComponentType.EVOLUTION: {
                "name": "Policy Evolution",
                "description": "Creates better policy proposals through competition and iteration",
                "primary_strengths": [
                    PolicyNeed.COMPREHENSIVE_SOLUTION,
                    PolicyNeed.REFINEMENT,
                    PolicyNeed.EVOLUTION,
                    PolicyNeed.LOCAL_CONTEXT
                ],
                "secondary_strengths": [
                    PolicyNeed.STAKEHOLDER_ANALYSIS,
                    PolicyNeed.IMPLEMENTATION_PLAN
                ],
                "time_required": TimeAvailable.EXTENSIVE,
                "expertise_required": UserExpertise.INTERMEDIATE,
                "needs_local_context": True
            },
            ComponentType.INTEGRATED: {
                "name": "Integrated Policy System",
                "description": "Combines research and analysis into a single workflow",
                "primary_strengths": [
                    PolicyNeed.BACKGROUND_RESEARCH,
                    PolicyNeed.GENERATE_OPTIONS,
                    PolicyNeed.EVALUATE_OPTIONS
                ],
                "secondary_strengths": [
                    PolicyNeed.IMPLEMENTATION_PLAN,
                    PolicyNeed.COMPREHENSIVE_SOLUTION
                ],
                "time_required": TimeAvailable.EXTENSIVE,
                "expertise_required": UserExpertise.NOVICE,
                "needs_local_context": False
            },
            ComponentType.CONTEXT: {
                "name": "Context Gathering",
                "description": "Gathers local context data to inform policy development",
                "primary_strengths": [
                    PolicyNeed.LOCAL_CONTEXT
                ],
                "secondary_strengths": [
                    PolicyNeed.STAKEHOLDER_ANALYSIS
                ],
                "time_required": TimeAvailable.MEDIUM,
                "expertise_required": UserExpertise.NOVICE,
                "needs_local_context": False
            }
        }
    
    def get_component_description(self, component_type: ComponentType) -> Dict[str, Any]:
        """Get the description of a component type."""
        return self.component_capabilities[component_type]
    
    def list_all_components(self) -> List[Dict[str, Any]]:
        """List all available components with descriptions."""
        return [
            {
                "type": component_type,
                "name": details["name"],
                "description": details["description"],
                "primary_strengths": [need.name for need in details["primary_strengths"]],
                "time_required": details["time_required"].name,
                "expertise_required": details["expertise_required"].name
            }
            for component_type, details in self.component_capabilities.items()
        ]
    
    def _score_component_match(self, profile: UserProfile, component_type: ComponentType) -> float:
        """
        Calculate a match score between a user profile and a component.
        
        Args:
            profile: User profile with needs and constraints
            component_type: Component type to evaluate
            
        Returns:
            Score from 0.0 to 1.0 where higher is better match
        """
        component = self.component_capabilities[component_type]
        score = 0.0
        max_score = 0.0
        
        # Primary needs match (most important)
        max_score += 6.0
        for need in profile.primary_needs:
            if need in component["primary_strengths"]:
                score += 6.0 / len(profile.primary_needs)
            elif need in component["secondary_strengths"]:
                score += 3.0 / len(profile.primary_needs)
        
        # Time constraint match
        max_score += 2.0
        if profile.time_available.value >= component["time_required"].value:
            score += 2.0
        else:
            # Partial credit for time close to required
            time_diff = component["time_required"].value - profile.time_available.value
            if time_diff == 1:
                score += 1.0
        
        # Expertise match
        max_score += 1.0
        if profile.expertise_level.value >= component["expertise_required"].value:
            score += 1.0
        else:
            # Partial credit for expertise close to required
            expertise_diff = component["expertise_required"].value - profile.expertise_level.value
            if expertise_diff == 1:
                score += 0.5
        
        # Local context match
        max_score += 1.0
        if not component["needs_local_context"] or profile.has_local_context:
            score += 1.0
        
        # Normalize to 0.0-1.0 range
        return score / max_score if max_score > 0 else 0.0
    
    def recommend_component(self, profile: UserProfile) -> ComponentRecommendation:
        """
        Recommend the most appropriate component based on user profile.
        
        Args:
            profile: User profile with needs and constraints
            
        Returns:
            ComponentRecommendation with the best match and justifications
        """
        # Score each component
        scores = {}
        for component_type in ComponentType:
            scores[component_type] = self._score_component_match(profile, component_type)
        
        # Find the best match
        best_component = max(scores, key=scores.get)
        best_score = scores[best_component]
        component_details = self.component_capabilities[best_component]
        
        # Generate reasons for recommendation
        reasons = []
        
        # Check primary needs match
        matching_primary_needs = [
            need.name for need in profile.primary_needs 
            if need in component_details["primary_strengths"]
        ]
        if matching_primary_needs:
            needs_str = ", ".join(matching_primary_needs)
            reasons.append(f"Addresses your primary needs: {needs_str}")
        
        # Check time and expertise match
        if profile.time_available.value >= component_details["time_required"].value:
            reasons.append(f"Works within your available time ({profile.time_available.name})")
        
        if profile.expertise_level.value >= component_details["expertise_required"].value:
            reasons.append(f"Suitable for your expertise level ({profile.expertise_level.name})")
        
        # Generate limitations
        limitations = []
        
        # Check for unaddressed primary needs
        unaddressed_needs = [
            need.name for need in profile.primary_needs 
            if need not in component_details["primary_strengths"] 
            and need not in component_details["secondary_strengths"]
        ]
        if unaddressed_needs:
            needs_str = ", ".join(unaddressed_needs)
            limitations.append(f"Does not directly address: {needs_str}")
        
        # Check time and expertise limitations
        if profile.time_available.value < component_details["time_required"].value:
            limitations.append(
                f"May require more time than you have available "
                f"({profile.time_available.name} vs. {component_details['time_required'].name} needed)"
            )
        
        if profile.expertise_level.value < component_details["expertise_required"].value:
            limitations.append(
                f"May be challenging for your expertise level "
                f"({profile.expertise_level.name} vs. {component_details['expertise_required'].name} recommended)"
            )
        
        # Local context requirement
        if component_details["needs_local_context"] and not profile.has_local_context:
            limitations.append("Works best with local context information, which you don't have yet")
        
        # Generate next steps
        next_steps = []
        
        # Start with component-specific next steps
        if best_component == ComponentType.RESEARCH:
            next_steps.append("Specify your policy research question")
            next_steps.append("Review and save research findings for use in later analysis")
        
        elif best_component == ComponentType.ANALYSIS:
            if not profile.has_research:
                next_steps.append("Consider running Policy Research first to gather background information")
            next_steps.append("Prepare your policy question for analysis")
        
        elif best_component == ComponentType.EVOLUTION:
            if not profile.has_local_context:
                next_steps.append("Run Context Gathering first to collect local information")
            next_steps.append("Prepare your policy challenge description")
        
        elif best_component == ComponentType.INTEGRATED:
            next_steps.append("Prepare your policy question for the integrated process")
            next_steps.append("Allocate sufficient time for the complete process")
        
        elif best_component == ComponentType.CONTEXT:
            next_steps.append("Collect basic information about your jurisdiction")
            next_steps.append("Save the context profile for use with other components")
        
        # Create and return the recommendation
        return ComponentRecommendation(
            component_type=best_component,
            confidence=best_score,
            reasons=reasons,
            limitations=limitations,
            next_steps=next_steps
        )
        
    def guided_selection(self) -> ComponentRecommendation:
        """
        Guide the user through component selection with interactive questions.
        
        Returns:
            ComponentRecommendation based on user responses
        """
        print("\n=== CIVICAIDE COMPONENT SELECTOR ===\n")
        print("I'll help you choose the right policy component for your needs.")
        
        # Collect primary needs
        print("\nWhat are your primary policy development needs? (Select all that apply)")
        needs_options = {
            "1": (PolicyNeed.BACKGROUND_RESEARCH, "Gather information and research about a policy topic"),
            "2": (PolicyNeed.GENERATE_OPTIONS, "Generate different policy options or approaches"),
            "3": (PolicyNeed.EVALUATE_OPTIONS, "Evaluate and compare different policy options"),
            "4": (PolicyNeed.LOCAL_CONTEXT, "Understand my local context and how it affects policy"),
            "5": (PolicyNeed.STAKEHOLDER_ANALYSIS, "Analyze impacts on different stakeholders"),
            "6": (PolicyNeed.IMPLEMENTATION_PLAN, "Develop an implementation plan"),
            "7": (PolicyNeed.COMPREHENSIVE_SOLUTION, "Create a complete, well-considered policy"),
            "8": (PolicyNeed.REFINEMENT, "Refine and improve an existing policy idea"),
            "9": (PolicyNeed.EVOLUTION, "Evolve policies through multiple iterations")
        }
        
        for key, (_, description) in needs_options.items():
            print(f"{key}. {description}")
        
        needs_input = input("\nEnter numbers (e.g., 1,3,5): ").strip()
        selected_needs = []
        for choice in needs_input.split(","):
            choice = choice.strip()
            if choice in needs_options:
                selected_needs.append(needs_options[choice][0])
        
        if not selected_needs:
            selected_needs = [PolicyNeed.COMPREHENSIVE_SOLUTION]  # Default if nothing selected
        
        # Collect expertise level
        print("\nWhat is your level of expertise with policy development?")
        expertise_options = {
            "1": (UserExpertise.NOVICE, "Novice - I'm new to policy development"),
            "2": (UserExpertise.INTERMEDIATE, "Intermediate - I have some experience"),
            "3": (UserExpertise.EXPERT, "Expert - I have extensive experience")
        }
        
        for key, (_, description) in expertise_options.items():
            print(f"{key}. {description}")
        
        expertise_input = input("\nEnter number (1-3): ").strip()
        expertise_level = expertise_options.get(expertise_input, (UserExpertise.NOVICE, ""))[0]
        
        # Collect time available
        print("\nHow much time do you have available for this policy work?")
        time_options = {
            "1": (TimeAvailable.QUICK, "Quick - Under 10 minutes"),
            "2": (TimeAvailable.MEDIUM, "Medium - 10-30 minutes"),
            "3": (TimeAvailable.EXTENSIVE, "Extensive - 30+ minutes")
        }
        
        for key, (_, description) in time_options.items():
            print(f"{key}. {description}")
        
        time_input = input("\nEnter number (1-3): ").strip()
        time_available = time_options.get(time_input, (TimeAvailable.MEDIUM, ""))[0]
        
        # Check for local context and research
        has_local_context = input("\nDo you already have detailed information about your local context? (y/n): ").strip().lower() == 'y'
        has_research = input("Have you already gathered research on this policy topic? (y/n): ").strip().lower() == 'y'
        
        # Create user profile
        profile = UserProfile(
            primary_needs=selected_needs,
            expertise_level=expertise_level,
            time_available=time_available,
            has_local_context=has_local_context,
            has_research=has_research
        )
        
        # Generate recommendation
        recommendation = self.recommend_component(profile)
        
        # Display recommendation
        component_details = self.component_capabilities[recommendation.component_type]
        
        print("\n=== RECOMMENDATION ===\n")
        print(f"Recommended Component: {component_details['name']}")
        print(f"\nDescription: {component_details['description']}")
        
        print("\nWhy this component:")
        for reason in recommendation.reasons:
            print(f"• {reason}")
        
        if recommendation.limitations:
            print("\nLimitations to consider:")
            for limitation in recommendation.limitations:
                print(f"• {limitation}")
        
        print("\nNext steps:")
        for step in recommendation.next_steps:
            print(f"• {step}")
        
        print(f"\nConfidence in recommendation: {recommendation.confidence:.0%}")
        
        return recommendation

def main():
    """Run the component selector as a standalone tool."""
    selector = ComponentSelector()
    selector.guided_selection()

if __name__ == "__main__":
    main() 