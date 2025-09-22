#!/usr/bin/env python3
"""
Kubernetes Infogent FastMCP Client
=================================
Comprehensive test client for the K8s Infogent FastMCP server.
Tests all Kubernetes operations, natural language queries, and infogent architecture features.
"""

import asyncio
import json
from fastmcp import Client

# Create client for the K8s Infogent server
client = Client("http://localhost:8002/mcp")

async def test_k8s_infogent_server():
    """Test all capabilities of the K8s Infogent server"""

    async with client:
        print("Testing K8s Infogent FastMCP Server")
        print("=" * 60)

        # Test 1: Get cluster information
        print("\n1. Cluster Information:")
        try:
            cluster_info = await client.call_tool("k8s_get_cluster_info", {})
            print(f"Cluster Info: {json.dumps(cluster_info.data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: List resources
        print("\n2. Resource Listing:")
        for resource_type in ["pods", "deployments", "services"]:
            try:
                result = await client.call_tool("k8s_list_resources", {"resource_type": resource_type})
                print(f"{resource_type.title()}: {result.data}")
            except Exception as e:
                print(f"Error listing {resource_type}: {e}")

        # Test 3: Natural language queries - Operational commands
        print("\n3. Natural Language Operational Queries:")
        operational_queries = [
            "List all pods",
            "Show me deployments",
            "Get services in the cluster"
        ]

        for query in operational_queries:
            try:
                result = await client.call_tool("intelligent_k8s_query", {"params": {"query": query}})
                print(f"Query: '{query}'")
                print(f"Response: {result.data}\n")
            except Exception as e:
                print(f"Error with query '{query}': {e}")

        # Test 4: Natural language queries - Explanations
        print("\n4. Natural Language Explanation Queries:")
        explanation_queries = [
            "What is a Kubernetes pod?",
            "How do deployments work?",
            "Explain services in Kubernetes"
        ]

        for query in explanation_queries:
            try:
                result = await client.call_tool("intelligent_k8s_query", {"params": {"query": query}})
                print(f"Query: '{query}'")
                print(f"Response: {result.data}\n")
            except Exception as e:
                print(f"Error with query '{query}': {e}")

        # Test 5: YAML validation
        print("\n5. YAML Validation:")
        test_yaml = """apiVersion: v1
kind: Pod
metadata:
  name: test-validation-pod
  namespace: gsoc
spec:
  containers:
  - name: nginx
    image: nginx:latest
    resources:
      limits:
        memory: 128Mi
        cpu: 100m
      requests:
        memory: 64Mi
        cpu: 50m"""

        try:
            result = await client.call_tool("k8s_validate_yaml", {"yaml_content": test_yaml})
            print(f"YAML Validation Result: {json.dumps(result.data, indent=2)}")
        except Exception as e:
            print(f"Error validating YAML: {e}")

        # Test 6: Pod creation (programmatic)
        print("\n6. Pod Creation (Programmatic):")
        pod_params = {
            "name": "test-mcp-pod",
            "image": "nginx",
            "memory_limit": "128Mi",
            "cpu_limit": "100m",
            "memory_request": "64Mi",
            "cpu_request": "50m"
        }

        try:
            result = await client.call_tool("k8s_create_pod", {"params": pod_params})
            print(f"Pod Creation Result: {result.data}")
        except Exception as e:
            print(f"Error creating pod: {e}")

        # Test 7: Describe the created pod
        print("\n7. Describe Created Pod:")
        try:
            result = await client.call_tool("k8s_describe_resource", {
                "resource_type": "pod",
                "resource_name": "test-mcp-pod"
            })
            print(f"Pod Description: {result.data}")
        except Exception as e:
            print(f"Error describing pod: {e}")

        # Test 8: Get pod logs
        print("\n8. Get Pod Logs:")
        try:
            result = await client.call_tool("k8s_get_logs", {
                "pod_name": "test-mcp-pod",
                "tail_lines": 10
            })
            print(f"Pod Logs: {result.data}")
        except Exception as e:
            print(f"Error getting logs: {e}")

        # Test 9: YAML resource creation
        print("\n9. YAML Resource Creation:")
        deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-mcp-deployment
  namespace: gsoc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-mcp
  template:
    metadata:
      labels:
        app: test-mcp
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        resources:
          limits:
            memory: 256Mi
            cpu: 200m
          requests:
            memory: 128Mi
            cpu: 100m"""

        try:
            result = await client.call_tool("k8s_create_from_yaml", {"params": {
                "yaml_content": deployment_yaml,
                "resource_type": "deployment"
            }})
            print(f"YAML Deployment Creation: {result.data}")
        except Exception as e:
            print(f"Error creating deployment from YAML: {e}")

        # Test 10: Complex natural language query
        print("\n10. Complex Natural Language Query:")
        complex_query = "I want to understand how to scale my application and what resources I need to monitor"
        try:
            result = await client.call_tool("intelligent_k8s_query", {"params": {
                "query": complex_query,
                "context": "Running applications in gsoc namespace"
            }})
            print(f"Complex Query: '{complex_query}'")
            print(f"Response: {result.data}")
        except Exception as e:
            print(f"Error with complex query: {e}")

        # Test 11: Read server resources
        print("\n11. Server Resources:")
        resources_to_test = [
            "k8s://cluster/status",
            "k8s://examples/yaml",
            "k8s://help/commands"
        ]

        for resource_uri in resources_to_test:
            try:
                result = await client.read_resource(resource_uri)
                print(f"Resource '{resource_uri}':")
                if result and len(result) > 0:
                    content = json.loads(result[0].text) if result[0].text.startswith('{') else result[0].text
                    print(json.dumps(content, indent=2) if isinstance(content, dict) else content)
                print()
            except Exception as e:
                print(f"Error reading resource '{resource_uri}': {e}")

        # Test 12: Cleanup - Delete created resources
        print("\n12. Cleanup:")
        cleanup_resources = [
            {"type": "pod", "name": "test-mcp-pod"},
            {"type": "deployment", "name": "test-mcp-deployment"}
        ]

        for resource in cleanup_resources:
            try:
                result = await client.call_tool("k8s_delete_resource", {
                    "resource_type": resource["type"],
                    "resource_name": resource["name"]
                })
                print(f"Deleted {resource['type']} '{resource['name']}': {result.data}")
            except Exception as e:
                print(f"Error deleting {resource['type']} '{resource['name']}': {e}")

        # Test 13: Final status check
        print("\n13. Final Resource List:")
        try:
            pods = await client.call_tool("k8s_list_resources", {"resource_type": "pods"})
            deployments = await client.call_tool("k8s_list_resources", {"resource_type": "deployments"})
            print(f"Remaining Pods: {pods.data}")
            print(f"Remaining Deployments: {deployments.data}")
        except Exception as e:
            print(f"Error in final status check: {e}")

        print("\nAll tests completed!")

async def demo_natural_language_interface():
    """Demo the natural language interface capabilities"""

    print("\n" + "=" * 60)
    print("NATURAL LANGUAGE INTERFACE DEMO")
    print("=" * 60)

    demo_queries = [
        # Operational queries
        ("Show me all running pods", "COMMAND"),
        ("List deployments in the cluster", "COMMAND"),
        ("Get the status of my services", "COMMAND"),

        # Explanation queries
        ("What is the difference between pods and deployments?", "EXPLANATION"),
        ("How do I expose a pod to external traffic?", "EXPLANATION"),
        ("Explain Kubernetes namespaces", "EXPLANATION"),

        # Mixed/unclear queries
        ("I need help with scaling", "UNCLEAR"),
        ("Something is wrong with my application", "UNCLEAR"),
        ("Kubernetes networking", "UNCLEAR"),
    ]

    async with client:
        for query, expected_intent in demo_queries:
            try:
                print(f"\nQuery: '{query}' (Expected: {expected_intent})")
                result = await client.call_tool("intelligent_k8s_query", {"params": {"query": query}})
                print(f"Response: {result.data}")
                print("-" * 40)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting K8s Infogent FastMCP Client Tests...")

    # Run main tests
    asyncio.run(test_k8s_infogent_server())

    # Run natural language demo
    asyncio.run(demo_natural_language_interface())