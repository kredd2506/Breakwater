#!/usr/bin/env python3
"""Test A100 GPU query"""

import asyncio
from fastmcp import Client

async def test_a100_query():
    async with Client("http://localhost:8024/mcp") as client:
        result = await client.call_tool("intelligent_k8s_query", {
            "params": {
                "query": "How can users request an A100 GPU for their Kubernetes pod?",
                "context": "Testing A100 GPU request"
            }
        })
        print("=" * 70)
        print("A100 GPU QUERY TEST")
        print("=" * 70)
        print(result.data)

if __name__ == "__main__":
    asyncio.run(test_a100_query())