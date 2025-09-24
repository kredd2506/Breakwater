#!/usr/bin/env python3
"""
Simple K8s Operations Test
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_k8s_direct():
    """Test direct K8s access"""
    print("=" * 50)
    print("TESTING DIRECT K8S API ACCESS")
    print("=" * 50)

    try:
        from kubernetes import client, config

        # Load K8s config
        try:
            config.load_kube_config()
            print("Loaded local kube config")
        except:
            try:
                config.load_incluster_config()
                print("Loaded in-cluster config")
            except Exception as e:
                print(f"Could not load K8s config: {e}")
                return

        # Test basic operations
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        # List pods
        print("\nTesting: List pods in 'gsoc' namespace")
        try:
            pods = v1.list_namespaced_pod(namespace="gsoc", limit=5)
            print(f"Found {len(pods.items)} pods:")
            for pod in pods.items:
                print(f"  - {pod.metadata.name}: {pod.status.phase}")
        except Exception as e:
            print(f"Pods error: {e}")

        # List deployments
        print("\nTesting: List deployments in 'gsoc' namespace")
        try:
            deployments = apps_v1.list_namespaced_deployment(namespace="gsoc", limit=5)
            print(f"Found {len(deployments.items)} deployments:")
            for dep in deployments.items:
                ready = dep.status.ready_replicas or 0
                replicas = dep.spec.replicas or 0
                print(f"  - {dep.metadata.name}: {ready}/{replicas} ready")
        except Exception as e:
            print(f"Deployments error: {e}")

    except Exception as e:
        print(f"K8s API error: {e}")

async def test_mcp_session():
    """Test MCP session operations"""
    print("\n" + "=" * 50)
    print("TESTING MCP SESSION OPERATIONS")
    print("=" * 50)

    try:
        from your_interactive_session import InteractiveNRPSession
        session = InteractiveNRPSession()

        # Test K8s commands
        commands = ["list my pods", "show deployments"]

        for command in commands:
            print(f"\nTesting: '{command}'")

            try:
                intent = await session.classify_intent(command)
                print(f"Intent: {intent}")

                if intent == "COMMAND":
                    result = await session.process_k8s_command(command)
                    print(f"K8s Result: {result[:200]}...")

            except Exception as e:
                print(f"Error: {str(e)}")

    except Exception as e:
        print(f"Session error: {e}")

async def test_documentation():
    """Test documentation queries"""
    print("\n" + "=" * 50)
    print("TESTING DOCUMENTATION QUERIES")
    print("=" * 50)

    try:
        from your_interactive_session import InteractiveNRPSession
        session = InteractiveNRPSession()

        # Test documentation
        queries = ["How do I request A100 GPU?", "What is persistent storage?"]

        for query in queries:
            print(f"\nTesting: '{query}'")

            try:
                intent = await session.classify_intent(query)
                print(f"Intent: {intent}")

                if intent == "QUESTION":
                    result = await session.ask_question(query)
                    print(f"Documentation: {result[:200]}...")

            except Exception as e:
                print(f"Error: {str(e)}")

    except Exception as e:
        print(f"Documentation error: {e}")

async def main():
    """Run all tests"""
    print("Starting K8s Operations Test")

    await test_k8s_direct()
    await test_mcp_session()
    await test_documentation()

    print("\nK8s Operations Test Complete")

if __name__ == "__main__":
    asyncio.run(main())