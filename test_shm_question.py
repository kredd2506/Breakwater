#!/usr/bin/env python3
"""
Test what answer the system gives for shared memory questions.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.code_generator import CodeGeneratorAgent
from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel


def test_shm_question():
    """Test how the system responds to shared memory questions."""

    print("Testing shared memory question...")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create request about shared memory
    request = AgentRequest(
        user_input="How do I add more shared memory (shm) to my GPU pods in YAML?",
        intent_type=IntentType.CODE_REQUEST,
        confidence=ConfidenceLevel.HIGH,
        context={}
    )

    # Process the request
    response = agent.process(request)

    print(f"Success: {response.success}")
    print(f"Agent: {response.agent_type}")
    print(f"Response:\n{response.content}")

    if response.follow_up_suggestions:
        print(f"\nFollow-up suggestions:")
        for suggestion in response.follow_up_suggestions:
            print(f"- {suggestion}")

    return response


if __name__ == "__main__":
    test_shm_question()