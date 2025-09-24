#!/usr/bin/env python3
"""
Simple test for shared memory intent classification.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.intent_router import IntentRouter
from nrp_k8s_system.agents.agent_types import IntentType


def main():
    print("Testing Shared Memory Intent Classification")
    print("=" * 50)

    router = IntentRouter()

    # Test the key question
    question = "How do I add more shared memory (shm) to my GPU pods in YAML?"
    request = router.classify_intent(question)

    print(f"Question: {question}")
    print(f"Intent: {request.intent_type.value}")
    print(f"Confidence: {request.confidence.value}")

    if request.intent_type == IntentType.QUESTION:
        print("SUCCESS: Routes to INFOGENT Agent for documentation lookup")
        print("This should find: https://nrp.ai/documentation/userdocs/running/gpu-pods/#adding-shared-memory-shm")
        return True
    else:
        print("FAIL: Should route to QUESTION/INFOGENT, not CODE_REQUEST")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)