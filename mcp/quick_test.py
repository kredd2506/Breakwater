#!/usr/bin/env python3
"""Quick Test Script for GLM-4.5V Enhanced System"""

import asyncio
import sys
from fastmcp import Client

async def main():
    """Test the enhanced system"""

    print("=" * 70)
    print("GLM-4.5V Enhanced NRP K8s System - Quick Test")
    print("=" * 70)

    try:
        # Test connection
        async with Client("http://localhost:8024/mcp") as client:
            print("[1] Testing A100 GPU request query...")
            result1 = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "How do I request an A100 GPU?",
                    "context": "Test query for A100 GPU"
                }
            })
            print(f"[RESULT] {result1.data[:200]}...")
            print()

            print("[2] Testing storage options query...")
            result2 = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "What storage options are available?",
                    "context": "Test query for storage"
                }
            })
            print(f"[RESULT] {result2.data[:200]}...")
            print()

            print("[SUCCESS] Enhanced system is working!")

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("Make sure the server is running on port 8024")
        print("Run: python ultimate_fastmcp_server.py")

if __name__ == "__main__":
    asyncio.run(main())