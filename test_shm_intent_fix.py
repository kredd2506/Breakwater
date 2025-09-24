#!/usr/bin/env python3
"""
Test the fixed intent classification for shared memory questions.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.intent_router import IntentRouter
from nrp_k8s_system.agents.agent_types import IntentType


def test_shared_memory_intent():
    """Test intent classification for shared memory questions."""

    router = IntentRouter()

    test_questions = [
        "How do I add more shared memory (shm) to my GPU pods in YAML?",
        "How to increase shared memory for my pod?",
        "What is shared memory in Kubernetes?",
        "Explain shm configuration",
        "How do I configure /dev/shm in pods?",
        "Create a deployment YAML with shared memory",  # Should be CODE_REQUEST
        "Generate shm template"  # Should be CODE_REQUEST
    ]

    expected_results = [
        IntentType.QUESTION,  # How do I... -> QUESTION
        IntentType.QUESTION,  # How to... -> QUESTION
        IntentType.QUESTION,  # What is... -> QUESTION
        IntentType.QUESTION,  # Explain... -> QUESTION
        IntentType.QUESTION,  # How do I... -> QUESTION
        IntentType.CODE_REQUEST,  # Create... YAML -> CODE_REQUEST
        IntentType.CODE_REQUEST,  # Generate template -> CODE_REQUEST
    ]

    print("Testing Intent Classification for Shared Memory Questions")
    print("=" * 60)

    all_passed = True

    for i, (question, expected) in enumerate(zip(test_questions, expected_results)):
        print(f"\nTest {i+1}: {question}")

        try:
            request = router.classify_intent(question)
            actual = request.intent_type

            print(f"Expected: {expected.value}")
            print(f"Actual:   {actual.value}")
            print(f"Confidence: {request.confidence.value}")

            if "context" in request.context:
                print(f"Reasoning: {request.context.get('reasoning', 'N/A')}")
                print(f"Keywords: {request.context.get('keywords', [])}")

            if actual == expected:
                print("✓ PASS")
            else:
                print("✗ FAIL")
                all_passed = False

        except Exception as e:
            print(f"✗ ERROR: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All intent classifications correct!")
        print("\nKey fixes verified:")
        print("- 'How do I...' questions route to QUESTION/INFOGENT")
        print("- 'How to...' questions route to QUESTION/INFOGENT")
        print("- Shared memory topics route to QUESTION/INFOGENT")
        print("- 'Create/Generate' requests still route to CODE_REQUEST")
    else:
        print("Some tests failed. Intent classification needs more work.")

    return all_passed


if __name__ == "__main__":
    success = test_shared_memory_intent()
    sys.exit(0 if success else 1)