#!/usr/bin/env python3
"""Test A100 GPU query with fixed server"""

import asyncio
import time
from fastmcp import Client

async def test_fixed_a100_query():
    # Wait for server to start
    await asyncio.sleep(3)

    try:
        async with Client("http://localhost:8025/mcp") as client:
            result = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "How can users request an A100 GPU for their Kubernetes pod?",
                    "context": "Testing fixed A100 GPU request"
                }
            })
            print("=" * 70)
            print("FIXED A100 GPU QUERY TEST (Port 8025)")
            print("=" * 70)
            print(result.data)
    except Exception as e:
        print(f"Error connecting to port 8025: {e}")
        print("Trying original port 8024...")

        try:
            async with Client("http://localhost:8024/mcp") as client:
                result = await client.call_tool("intelligent_k8s_query", {
                    "params": {
                        "query": "How can users request an A100 GPU for their Kubernetes pod?",
                        "context": "Testing A100 GPU request on original port"
                    }
                })
                print("=" * 70)
                print("A100 GPU QUERY TEST (Port 8024)")
                print("=" * 70)
                print(result.data)
        except Exception as e2:
            print(f"Error connecting to both ports: {e2}")

if __name__ == "__main__":
    asyncio.run(test_fixed_a100_query())