#!/usr/bin/env python3
"""
Test the specific GPU vs CPU encoding performance question.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.intent_router import IntentRouter
from nrp_k8s_system.agents.orchestrator import AgentOrchestrator
from nrp_k8s_system.agents.agent_types import IntentType


def test_gpu_cpu_encoding_question():
    """Test the GPU vs CPU encoding performance question."""

    # The specific question
    question = "When deciding between GPU and CPU encoding, how do performance trade-offs—such as CPU usage, resolution requirements, and network bandwidth efficiency—affect which option is more suitable?"

    print("Testing GPU vs CPU Encoding Performance Question")
    print("=" * 70)
    print(f"Question: {question}")
    print("=" * 70)

    # Test 1: Intent Classification
    print("\n1. INTENT CLASSIFICATION:")
    router = IntentRouter()

    try:
        request = router.classify_intent(question)
        print(f"Intent: {request.intent_type.value}")
        print(f"Confidence: {request.confidence.value}")

        if hasattr(request, 'context') and 'reasoning' in request.context:
            print(f"Reasoning: {request.context['reasoning']}")
            print(f"Keywords: {request.context.get('keywords', [])}")

        if request.intent_type == IntentType.QUESTION:
            print("✓ Correctly routes to INFOGENT Agent for documentation search")
        else:
            print(f"✗ Wrong routing - should be QUESTION, got {request.intent_type.value}")

    except Exception as e:
        print(f"✗ Intent classification failed: {e}")
        return False

    # Test 2: Full System Processing (if possible)
    print("\n2. FULL SYSTEM PROCESSING:")
    print("Expected behavior:")
    print("- INFOGENT searches NRP documentation")
    print("- Should find: https://nrp.ai/documentation/userdocs/running/gui-desktop/#performance-considerations")
    print("- Should return performance trade-off information")

    try:
        orchestrator = AgentOrchestrator()
        response, success = orchestrator.process_request(question)

        print(f"\nSystem Response Success: {success}")
        print(f"Response (first 500 chars):")
        print("-" * 50)
        print(response[:500] + "..." if len(response) > 500 else response)

        # Check if response mentions the correct concepts
        key_concepts = [
            "gpu", "cpu", "encoding", "performance", "bandwidth", "resolution"
        ]

        response_lower = response.lower()
        found_concepts = [concept for concept in key_concepts if concept in response_lower]

        print(f"\nKey concepts found: {found_concepts}")

        if len(found_concepts) >= 4:
            print("✓ Response appears to address the performance question")
        else:
            print("✗ Response may not fully address the performance question")

        return success

    except Exception as e:
        print(f"✗ Full system processing failed: {e}")
        return False


if __name__ == "__main__":
    success = test_gpu_cpu_encoding_question()