#!/usr/bin/env python3
"""
Test what happens when asking about performance.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.intent_router import IntentRouter
from nrp_k8s_system.agents.agent_types import IntentType


def test_performance_questions():
    """Test intent classification for performance questions."""

    router = IntentRouter()

    performance_questions = [
        "How do I improve performance?",
        "What about performance optimization?",
        "How to optimize my pod performance?",
        "Why is my deployment slow?",
        "How do I monitor performance?",
        "What are performance best practices?",
        "Performance troubleshooting help"
    ]

    print("Testing Performance Question Intent Classification")
    print("=" * 60)

    for i, question in enumerate(performance_questions):
        print(f"\nTest {i+1}: {question}")

        try:
            request = router.classify_intent(question)
            print(f"Intent: {request.intent_type.value}")
            print(f"Confidence: {request.confidence.value}")

            if hasattr(request, 'context') and 'reasoning' in request.context:
                print(f"Reasoning: {request.context['reasoning']}")

            # Predict what would happen
            if request.intent_type == IntentType.QUESTION:
                print("→ Routes to INFOGENT Agent (documentation search)")
            elif request.intent_type == IntentType.CODE_REQUEST:
                print("→ Routes to Code Generator Agent (template creation)")
            elif request.intent_type == IntentType.COMMAND:
                print("→ Routes to K8s Operations Agent (kubectl commands)")
            else:
                print("→ Routes to clarification request")

        except Exception as e:
            print(f"ERROR: {e}")

    return True


if __name__ == "__main__":
    test_performance_questions()