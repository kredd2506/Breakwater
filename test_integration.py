#!/usr/bin/env python3
"""
Simple test script to verify the integration works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nrp_k8s_system'))

def test_classification():
    """Test intent classification"""
    from intelligent_router import classify_user_intent
    
    test_cases = [
        "list pods",
        "create pod test-nginx image=nginx", 
        "delete pod myapp",
        "How do I request GPUs?",
        "What are best practices?"
    ]
    
    print("=== Intent Classification Test ===")
    for case in test_cases:
        decision = classify_user_intent(case)
        print(f"Input: '{case}'")
        print(f"  Intent: {decision.intent.value}")
        print(f"  Confidence: {decision.confidence}")
        print(f"  Handler: {decision.suggested_handler}")
        print()

def test_command_parsing():
    """Test command parsing without K8s calls"""
    from intelligent_router import handle_k8s_command
    
    test_commands = [
        "list pods",
        "create pod test-nginx image=nginx",
        "create deployment web-app image=nginx replicas=3",
        "delete pod test-app",
        "delete deployment web-app"
    ]
    
    print("=== Command Parsing Test ===")
    for cmd in test_commands:
        print(f"Testing: '{cmd}'")
        try:
            result, success = handle_k8s_command(cmd)
            print(f"  Success: {success}")
            print(f"  Result: {result[:100]}...")  # Truncate for readability
        except Exception as e:
            print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    test_classification()
    test_command_parsing()