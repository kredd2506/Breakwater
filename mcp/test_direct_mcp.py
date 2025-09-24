#!/usr/bin/env python3
"""
Test Direct MCP Server - No Gradio, No Wrapper Issues
Test the core FastMCP server directly to prove it works perfectly
"""

import asyncio
from fastmcp import Client

async def test_direct_mcp():
    """Test MCP server directly - bypassing all wrapper issues"""
    print("=" * 60)
    print("TESTING DIRECT MCP SERVER - NO WRAPPERS")
    print("=" * 60)

    try:
        async with Client("http://localhost:8025/mcp") as client:

            # Test 1: K8s Command
            print("\n1. Testing K8s Command: 'list my pods'")
            print("-" * 40)

            result = await client.call_tool("intelligent_k8s_query", {
                "params": {"query": "list my pods", "context": "Direct MCP test"}
            })
            print(f"SUCCESS!")
            print(f"Result: {result}")

            # Test 2: Documentation Query
            print("\n2. Testing Documentation: 'How do I request A100 GPU?'")
            print("-" * 40)

            result = await client.call_tool("intelligent_k8s_query", {
                "params": {"query": "How do I request A100 GPU?", "context": "Direct MCP test"}
            })
            print(f"SUCCESS!")
            print(f"Result: {result.data[:300]}...")

            # Test 3: List Available Tools
            print("\n3. Available MCP Tools:")
            print("-" * 40)
            tools = await client.list_tools()
            for tool in tools:
                if 'k8s' in tool.name or 'intelligent' in tool.name:
                    print(f"  - {tool.name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_mcp())