#!/usr/bin/env python3
"""
Direct Test of K8s Operations
Test the K8s functionality without MCP server dependencies
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_k8s_operations():
    """Test K8s operations directly"""
    print("=" * 60)
    print("TESTING K8S OPERATIONS DIRECTLY")
    print("=" * 60)

    try:
        # Import the working interactive session
        from your_interactive_session import InteractiveNRPSession

        session = InteractiveNRPSession()

        # Test commands that should work
        test_commands = [
            "list my pods",
            "show deployments",
            "get pods in gsoc namespace",
            "describe pods",
            "list services"
        ]

        for command in test_commands:
            print(f"\n🧪 Testing: '{command}'")
            print("-" * 40)

            # Test intent classification
            try:
                intent = await session.classify_intent(command)
                print(f"✅ Intent: {intent}")

                if intent == "COMMAND":
                    # Test K8s command processing
                    result = await session.process_k8s_command(command)
                    print(f"📊 K8s Result:\n{result}")

                elif intent == "QUESTION":
                    # Test documentation
                    result = await session.ask_question(command)
                    print(f"📚 Documentation Result:\n{result}")

            except Exception as e:
                print(f"❌ Error: {str(e)}")

    except Exception as e:
        print(f"❌ Failed to import session: {str(e)}")

async def test_direct_k8s_access():
    """Test direct Kubernetes API access"""
    print("\n" + "=" * 60)
    print("TESTING DIRECT K8S API ACCESS")
    print("=" * 60)

    try:
        from kubernetes import client, config

        # Try to load K8s config
        try:
            config.load_kube_config()
            print("✅ Loaded local kube config")
        except:
            try:
                config.load_incluster_config()
                print("✅ Loaded in-cluster config")
            except Exception as e:
                print(f"❌ Could not load K8s config: {e}")
                return

        # Test basic K8s operations
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        # Test listing pods
        try:
            print("\n🔍 Testing: List pods in 'gsoc' namespace")
            pods = v1.list_namespaced_pod(namespace="gsoc", limit=5)
            print(f"✅ Found {len(pods.items)} pods:")
            for pod in pods.items:
                print(f"  - {pod.metadata.name}: {pod.status.phase}")
        except Exception as e:
            print(f"❌ Pods error: {e}")

        # Test listing deployments
        try:
            print("\n🔍 Testing: List deployments in 'gsoc' namespace")
            deployments = apps_v1.list_namespaced_deployment(namespace="gsoc", limit=5)
            print(f"✅ Found {len(deployments.items)} deployments:")
            for dep in deployments.items:
                ready = dep.status.ready_replicas or 0
                replicas = dep.spec.replicas or 0
                print(f"  - {dep.metadata.name}: {ready}/{replicas} ready")
        except Exception as e:
            print(f"❌ Deployments error: {e}")

        # Test listing services
        try:
            print("\n🔍 Testing: List services in 'gsoc' namespace")
            services = v1.list_namespaced_service(namespace="gsoc", limit=5)
            print(f"✅ Found {len(services.items)} services:")
            for svc in services.items:
                svc_type = svc.spec.type
                print(f"  - {svc.metadata.name}: {svc_type}")
        except Exception as e:
            print(f"❌ Services error: {e}")

    except ImportError:
        print("❌ Kubernetes client not available")
    except Exception as e:
        print(f"❌ K8s API error: {e}")

async def test_documentation_queries():
    """Test documentation and reference queries"""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENTATION QUERIES")
    print("=" * 60)

    try:
        from your_interactive_session import InteractiveNRPSession
        session = InteractiveNRPSession()

        doc_queries = [
            "How do I request A100 GPU?",
            "What is persistent storage?",
            "How do I use nodeSelector?",
            "NRP Nautilus documentation"
        ]

        for query in doc_queries:
            print(f"\n📚 Testing: '{query}'")
            print("-" * 40)

            try:
                intent = await session.classify_intent(query)
                print(f"✅ Intent: {intent}")

                result = await session.ask_question(query)
                print(f"📄 Documentation:\n{result[:500]}...")

            except Exception as e:
                print(f"❌ Error: {str(e)}")

    except Exception as e:
        print(f"❌ Failed to test documentation: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive K8s Operations Test")

    await test_direct_k8s_access()
    await test_k8s_operations()
    await test_documentation_queries()

    print("\n" + "=" * 60)
    print("✅ K8s Operations Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())