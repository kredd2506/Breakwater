#!/usr/bin/env python3
"""Simple test for the advanced infogent server"""

import asyncio
import json
from fastmcp import Client

async def test_advanced_server():
    client = Client("http://localhost:8004/mcp")

    async with client:
        print("Testing Advanced K8s Infogent Server")
        print("=" * 50)

        # Test 1: List pods with caching
        print("\n1. List Pods with Caching:")
        result = await client.call_tool("k8s_list_resources_advanced", {
            "resource_type": "pod",
            "namespace": "gsoc",
            "use_cache": True
        })
        print(f"Result: {result.data}")

        # Test 2: Content scraping
        print("\n2. Content Scraping Test:")
        config = {
            "url": "https://kubernetes.io/docs/concepts/workloads/pods/",
            "content_type": "documentation",
            "extract_yaml": True,
            "follow_links": False,
            "max_depth": 1,
            "cache_duration": 1800
        }
        result = await client.call_tool("scrape_content", {"config": config})
        print(f"Scraping Result: {result.data}")

        # Test 3: Search content
        print("\n3. Content Search:")
        result = await client.call_tool("search_content", {
            "query": "kubernetes",
            "limit": 3
        })
        print(f"Search Result: {result.data}")

        # Test 4: Cache statistics
        print("\n4. Cache Statistics:")
        result = await client.read_resource("infogent://cache/stats")
        if result and len(result) > 0:
            stats = json.loads(result[0].text)
            print(f"Cache Stats: {json.dumps(stats, indent=2)}")

        print("\nAdvanced server test completed!")

if __name__ == "__main__":
    asyncio.run(test_advanced_server())