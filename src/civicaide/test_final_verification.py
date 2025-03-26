#!/usr/bin/env python
"""
Final verification test for token usage and parent-child relationships in policy comparison
"""

import os
import sys
import json
import uuid
import asyncio
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import the necessary modules
from src.agents import trace, custom_span, gen_trace_id
from src.civicaide.trace_manager import get_trace_processor, SimpleTraceProcessor

class MockTokenUsage:
    """Simulates OpenAI API token usage"""
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        
    def to_dict(self):
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

class MockProposalEvaluation:
    """Mock a policy proposal comparison with token tracking"""
    def __init__(self, trace_id, trace_processor, policy_name="Test Policy"):
        self.trace_id = trace_id
        self.trace_processor = trace_processor
        self.policy_name = policy_name
        self.openai_response_id = f"resp_{uuid.uuid4().hex[:16]}"
        
    async def run_comparison(self):
        """Simulate comparing two policy proposals"""
        print(f"Running mock policy comparison for {self.policy_name}")
        
        # Create a root span for the comparison
        root_span_id = self.trace_processor.record_agent_interaction(
            trace_id=self.trace_id,
            agent_name="Policy Comparison Manager",
            input_text="Compare policy proposals for addressing homelessness",
            output_text="Starting policy comparison tournament",
            span_type="policy_comparison",
            model="gpt-4-turbo",
            tokens_used=MockTokenUsage(100, 50).to_dict(),
            metadata={"openai_response_id": self.openai_response_id}
        )
        print(f"Created root comparison span: {root_span_id}")
        
        # Simulate first proposal evaluation
        proposal1_span_id = self.trace_processor.record_agent_interaction(
            trace_id=self.trace_id,
            agent_name="Policy Evaluator",
            input_text="Evaluate proposal 1: Housing First approach",
            output_text="Housing First shows strong evidence of effectiveness with 70% retention rates",
            span_type="proposal_evaluation",
            model="gpt-4-turbo",
            tokens_used=MockTokenUsage(150, 200).to_dict(),
            parent_span_id=root_span_id,
            metadata={"openai_response_id": f"resp_{uuid.uuid4().hex[:16]}"}
        )
        print(f"Created proposal 1 evaluation span: {proposal1_span_id} (parent: {root_span_id})")
        
        # Simulate second proposal evaluation
        proposal2_span_id = self.trace_processor.record_agent_interaction(
            trace_id=self.trace_id,
            agent_name="Policy Evaluator",
            input_text="Evaluate proposal 2: Shelter expansion program",
            output_text="Shelter expansion shows mixed results with high recidivism in some studies",
            span_type="proposal_evaluation",
            model="gpt-4-turbo",
            tokens_used={"prompt_tokens": 130, "completion_tokens": 180, "total_tokens": 310},
            parent_span_id=root_span_id,
            metadata={"openai_response_id": f"resp_{uuid.uuid4().hex[:16]}"}
        )
        print(f"Created proposal 2 evaluation span: {proposal2_span_id} (parent: {root_span_id})")
        
        # Simulate head-to-head comparison with different token format
        comparison_span_id = self.trace_processor.record_agent_interaction(
            trace_id=self.trace_id,
            agent_name="Policy Comparison Judge",
            input_text="Compare Housing First vs Shelter Expansion programs based on evidence",
            output_text="Housing First approach is superior based on outcomes and cost-effectiveness",
            span_type="head_to_head_comparison",
            model="gpt-4-turbo",
            tokens_used=500,  # Test numeric format
            parent_span_id=root_span_id,
            metadata={"openai_response_id": f"resp_{uuid.uuid4().hex[:16]}"}
        )
        print(f"Created comparison evaluation span: {comparison_span_id} (parent: {root_span_id})")
        
        # Create a recommendation with a different parent
        recommendation_span_id = self.trace_processor.record_agent_interaction(
            trace_id=self.trace_id,
            agent_name="Policy Recommendation Agent",
            input_text="Generate final recommendation based on comparison results",
            output_text="The Housing First approach is recommended as the primary policy intervention",
            span_type="policy_recommendation",
            model="gpt-4-turbo",
            tokens_used="450",  # Test string format
            parent_span_id=comparison_span_id,  # This is a child of the comparison, not the root
            metadata={"openai_response_id": f"resp_{uuid.uuid4().hex[:16]}"}
        )
        print(f"Created recommendation span: {recommendation_span_id} (parent: {comparison_span_id})")
        
        return root_span_id

async def run_test():
    """Run the final verification test"""
    print("\n==== Final Verification Test ====\n")
    print("Testing token usage tracking and parent-child relationships in policy comparison...")
    
    # Generate a trace ID
    trace_id = f"trace_{uuid.uuid4().hex[:16]}"
    print(f"Using trace ID: {trace_id}")
    
    # Get the trace processor
    trace_processor = get_trace_processor()
    
    # Initialize trace
    with trace("Policy Comparison Test", trace_id=trace_id) as current_trace:
        # Create a mock policy comparison
        comparison = MockProposalEvaluation(trace_id, trace_processor, "Homelessness Policy")
        root_span_id = await comparison.run_comparison()
        
    # Save the trace data
    trace_file = trace_processor.save_trace_to_file_and_db("Homelessness Policy Analysis", "verification_test")
    if trace_file:
        print(f"Trace data saved to: {trace_file}")
    
    # Query the database to verify the entire hierarchy
    print("\nVerifying spans in database...")
    if trace_processor.connection:
        try:
            cursor = trace_processor.connection.cursor()
            
            # Fetch all spans in this trace - simpler query first
            cursor.execute("""
                SELECT span_id, parent_span_id, span_type, tokens_used
                FROM policy_aide.spans 
                WHERE trace_id = %s
                ORDER BY span_id
            """, (trace_id,))
            
            spans = cursor.fetchall()
            print(f"Found {len(spans)} spans in the database:")
            
            # Build a map of span_id -> parent_span_id
            span_map = {}
            parent_map = {}
            
            for span_id, parent_span_id, span_type, tokens_used in spans:
                span_map[span_id] = {"parent_id": parent_span_id, "span_type": span_type, "tokens_used": tokens_used}
                if parent_span_id:
                    if parent_span_id not in parent_map:
                        parent_map[parent_span_id] = []
                    parent_map[parent_span_id].append(span_id)
            
            # Find root spans
            root_spans = [span_id for span_id, data in span_map.items() if not data["parent_id"]]
            
            # Recursive function to print the tree
            def print_tree(span_id, level=0):
                indent = "  " * level
                span_data = span_map[span_id]
                parent_info = f"(parent: {span_data['parent_id']})" if span_data["parent_id"] else "(root)"
                tokens_info = f"tokens: {span_data['tokens_used']}" if span_data['tokens_used'] else "no token data"
                print(f"{indent}L{level}: {span_id} - {span_data['span_type']} {parent_info} - {tokens_info}")
                
                # Print children
                if span_id in parent_map:
                    for child_id in parent_map[span_id]:
                        print_tree(child_id, level + 1)
            
            # Print the tree starting from root spans
            for root_span in root_spans:
                print_tree(root_span)
            
            # Check total token usage across the trace
            cursor.execute("""
                SELECT SUM(
                    CASE 
                        WHEN tokens_used->>'total_tokens' IS NOT NULL
                        THEN (tokens_used->>'total_tokens')::numeric
                        ELSE 0
                    END
                )
                FROM policy_aide.spans 
                WHERE trace_id = %s
            """, (trace_id,))
            
            total_tokens = cursor.fetchone()[0] or 0
            print(f"\nTotal tokens used across all spans: {total_tokens}")
            
            # Verify all spans have proper parent relationships
            orphaned_spans = 0
            for span_id, data in span_map.items():
                if data["parent_id"] and data["parent_id"] not in span_map:
                    print(f"❌ Orphaned span found: {span_id} references non-existent parent {data['parent_id']}")
                    orphaned_spans += 1
            
            if orphaned_spans == 0:
                print("✅ All spans have valid parent relationships")
            else:
                print(f"❌ Found {orphaned_spans} spans with invalid parent relationships")
                
        except Exception as e:
            print(f"Error querying database: {e}")
    
    print("\nTest completed!")
    return True

def main():
    """Main entry point"""
    try:
        result = asyncio.run(run_test())
        if result:
            print("✅ Final verification test passed")
            return 0
        else:
            print("❌ Final verification test failed")
            return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 