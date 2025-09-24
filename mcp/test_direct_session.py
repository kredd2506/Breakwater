#!/usr/bin/env python3
"""
Test Direct Session Operations (bypass MCP server)
Test K8s operations directly through your_interactive_session.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_session_direct():
    """Test session operations bypassing MCP server"""
    print("Testing Direct Session Operations (Bypass MCP Server)")
    print("=" * 60)

    try:
        from your_interactive_session import InteractiveNRPSession
        session = InteractiveNRPSession()

        # Test K8s operations directly (not through MCP)
        test_cases = [
            ("list my pods", "COMMAND"),
            ("show deployments", "QUESTION"),  # This one got misclassified, let's see
            ("How do I request A100 GPU?", "QUESTION")
        ]

        for query, expected_intent in test_cases:
            print(f"\nTesting: '{query}'")
            print("-" * 40)

            # Test intent classification
            intent = await session.classify_intent(query)
            print(f"Intent: {intent} (expected: {expected_intent})")

            if intent == "COMMAND":
                # Bypass MCP server and test K8s directly
                print("Testing K8s operations directly...")
                try:
                    # Let's see what happens when we call process_k8s_command
                    result = await session.process_k8s_command(query)
                    print(f"K8s Result: {result[:300]}...")
                except Exception as e:
                    print(f"K8s Error: {e}")

            elif intent == "QUESTION":
                print("Testing documentation directly...")
                try:
                    result = await session.ask_question(query)
                    print(f"Doc Result: {result[:300]}...")
                except Exception as e:
                    print(f"Doc Error: {e}")

    except Exception as e:
        print(f"Session error: {e}")

async def test_k8s_direct_api():
    """Test K8s API directly"""
    print("\n" + "=" * 60)
    print("Testing Direct K8s API")
    print("=" * 60)

    try:
        from kubernetes import client, config
        config.load_kube_config()
        v1 = client.CoreV1Api()

        # Test direct API calls
        print("\nDirect API: List pods in gsoc namespace")
        pods = v1.list_namespaced_pod(namespace="gsoc", limit=3)
        print(f"Found {len(pods.items)} pods:")
        for pod in pods.items:
            print(f"  - {pod.metadata.name}: {pod.status.phase}")

        return True

    except Exception as e:
        print(f"Direct K8s API error: {e}")
        return False

async def main():
    print("Testing K8s Operations - Direct vs MCP Server")

    # Test 1: Direct K8s API
    k8s_works = await test_k8s_direct_api()

    # Test 2: Session operations
    await test_session_direct()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Direct K8s API: {'✅ Working' if k8s_works else '❌ Failed'}")
    print("Session Testing: See results above")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())