#!/usr/bin/env python3
"""
Test Fixed K8s Operations
Quick test to verify that both K8s commands and questions work with the fixed MCP server
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_fixed_operations():
    """Test that both commands and questions work with fixed MCP server"""
    print("=" * 60)
    print("TESTING FIXED K8S OPERATIONS")
    print("=" * 60)

    try:
        from your_interactive_session import InteractiveNRPSession
        session = InteractiveNRPSession()

        # Test K8s command
        print("\n1. Testing K8s Command: 'list my pods'")
        print("-" * 40)
        try:
            intent = await session.classify_intent("list my pods")
            print(f"Intent: {intent}")

            if intent == "COMMAND":
                result = await session.process_k8s_command("list my pods")
                if result and "Pods in 'gsoc' namespace:" in result:
                    print("✅ K8s Command SUCCESS!")
                    print(f"Result: {result[:200]}...")
                else:
                    print("❌ K8s Command FAILED - No proper result")
                    print(f"Result: {result}")
            else:
                print("❌ K8s Command FAILED - Wrong intent classification")

        except Exception as e:
            print(f"❌ K8s Command ERROR: {e}")

        # Test question
        print("\n2. Testing Question: 'How do I request A100 GPU?'")
        print("-" * 40)
        try:
            intent = await session.classify_intent("How do I request A100 GPU?")
            print(f"Intent: {intent}")

            if intent == "QUESTION":
                result = await session.ask_question("How do I request A100 GPU?")
                if result and "A100" in result and "GPU" in result:
                    print("✅ Question SUCCESS!")
                    print(f"Result: {result[:200]}...")
                else:
                    print("❌ Question FAILED - No proper result")
                    print(f"Result: {result}")
            else:
                print("❌ Question FAILED - Wrong intent classification")

        except Exception as e:
            print(f"❌ Question ERROR: {e}")

    except Exception as e:
        print(f"❌ Session ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_operations())