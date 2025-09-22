#!/usr/bin/env python3
"""
Simple A100 GPU Test
===================

Quick test of the optimized system for A100 GPU queries.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nrp_k8s_system.agents.fast_infogent_agent import FastInfogentAgent
from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel
from nrp_k8s_system.core.fast_knowledge_builder import ensure_knowledge_base_built

def main():
    print("Testing A100 GPU Query with Optimized System")
    print("=" * 50)

    # Ensure knowledge base is built
    print("Ensuring knowledge base is ready...")
    builder = ensure_knowledge_base_built()
    stats = builder.get_stats()
    print(f"Knowledge base: {stats['total_templates']} templates, {stats['gpu_templates']} GPU templates")

    # Test fast agent
    agent = FastInfogentAgent()

    test_queries = [
        "How do I request A100 GPUs?",
        "A100 GPU configuration for PyTorch",
        "What are A100 GPU resource limits?"
    ]

    for query in test_queries:
        print(f"\nTesting: {query}")

        request = AgentRequest(
            user_input=query,
            intent_type=IntentType.QUESTION,
            confidence=ConfidenceLevel.HIGH,
            context={}
        )

        try:
            response = agent.process(request)

            print(f"Success: {response.success}")
            print(f"Agent: {response.agent_type}")

            if response.metadata:
                print(f"Results: {response.metadata.get('search_results', 0)}")
                print(f"GPU-specific: {response.metadata.get('gpu_specific', False)}")

            # Show preview
            preview = response.content[:150] + "..." if len(response.content) > 150 else response.content
            print(f"Response: {preview}")

        except Exception as e:
            print(f"Error: {e}")

    print("\nTest completed!")

if __name__ == "__main__":
    main()