#!/usr/bin/env python3
"""
Test GLM-V Intent Classification
===============================

Simple test to verify GLM-V is properly configured for intent classification.
"""

import os
from .intent_router import IntentRouter, init_intent_router

def test_glm_intent_classification():
    """Test GLM-V intent classification with sample inputs."""

    print("Testing GLM-V Intent Classification")
    print("=" * 40)

    # Check if GLM-V is configured
    glm_api_key = os.getenv("nrp_key_2")
    if not glm_api_key:
        print("X nrp_key_2 not set")
        print("\nTo enable GLM-V, set environment variables:")
        print("export nrp_key_2=your_glm_api_key")
        print("export nrp_base_url=https://llm.nrp-nautilus.io/v1")
        print("export nrp_model2=glm-4v-plus")
        return False

    # Initialize intent router
    try:
        router = init_intent_router()
        print(f"✅ Intent Router initialized")

        # Test cases
        test_cases = [
            "list my pods",
            "How do I request GPUs?",
            "create a deployment YAML",
            "what is kubernetes?"
        ]

        for test_input in test_cases:
            print(f"\n📝 Testing: '{test_input}'")
            try:
                request = router.classify_intent(test_input)
                print(f"   Intent: {request.intent_type.value}")
                print(f"   Confidence: {request.confidence.value}")
                print(f"   Reasoning: {request.context.get('reasoning', 'N/A')}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize router: {e}")
        return False

if __name__ == "__main__":
    test_glm_intent_classification()