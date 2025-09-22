#!/usr/bin/env python3
"""Quick test for K8s Infogent server natural language queries"""

import asyncio
from fastmcp import Client

async def quick_test():
    client = Client("http://localhost:8002/mcp")

    async with client:
        print("Quick K8s Infogent Test")
        print("=" * 30)

        # Test 1: List resources
        print("\n1. List Pods:")
        result = await client.call_tool("k8s_list_resources", {"resource_type": "pods"})
        print(f"Pods: {result.data}")

        # Test 2: Natural language command
        print("\n2. Natural Language Command:")
        result = await client.call_tool("intelligent_k8s_query", {"params": {"query": "List all pods"}})
        print(f"NL Command Result: {result.data}")

        # Test 3: Natural language explanation
        print("\n3. Natural Language Explanation:")
        result = await client.call_tool("intelligent_k8s_query", {"params": {"query": "What is a Kubernetes pod?"}})
        print(f"NL Explanation Result: {result.data}")

if __name__ == "__main__":
    asyncio.run(quick_test())