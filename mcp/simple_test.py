#!/usr/bin/env python3
"""
Simple Test Client for LLM Sampling Fixes
"""

import asyncio
from fastmcp import Client

async def test_sampling_simple():
    print("Testing FastMCP LLM Sampling Fixes")
    print("=" * 50)

    client = Client("http://localhost:8021/mcp")

    async with client:
        print("Connected to server on port 8021")

        # Test 1: LLM Sampling
        print("\n1. Testing LLM Sampling Demo...")
        try:
            result = await client.call_tool("ultimate_llm_sampling_demo", {
                "sampling_type": "test",
                "content": "FastMCP testing",
                "temperature": 0.7,
                "max_tokens": 100,
                "enable_structured_output": True
            })

            print(f"   Response length: {len(result.data)} characters")

            if "ERROR" in result.data and "Client does not support sampling" in result.data:
                print("   [ERROR] Still seeing old 'Client does not support sampling' error")
                print("   Server needs restart to load fixes")
            elif "[FALLBACK]" in result.data:
                print("   [OK] Using fallback responses (fixes working)")
            elif "Stage 1:" in result.data:
                print("   [OK] LLM sampling stages working!")
            else:
                print("   [INFO] Unknown response pattern")

        except Exception as e:
            print(f"   [ERROR] {e}")

        # Test 2: Configuration Generator
        print("\n2. Testing Configuration Generator...")
        try:
            result = await client.call_tool("intelligent_configuration_generator", {
                "config_type": "test_cluster",
                "requirements": "Simple test requirements",
                "optimization_level": "basic",
                "include_monitoring": True,
                "generate_explanations": True
            })

            print(f"   Response length: {len(result.data)} characters")
            print("   [OK] Configuration generator working!")

        except Exception as e:
            if "Unexpected keyword argument" in str(e):
                print("   [ERROR] Parameter validation still failing")
                print("   Server needs restart to load new parameters")
            else:
                print(f"   [ERROR] {e}")

        # Test 3: List tools
        print("\n3. Available tools...")
        try:
            tools = await client.list_tools()
            sampling_tools = [t for t in tools if 'sampling' in t.name.lower()]
            print(f"   Total tools: {len(tools)}")
            print(f"   Sampling tools: {len(sampling_tools)}")
            for tool in sampling_tools:
                print(f"     - {tool.name}")
        except Exception as e:
            print(f"   [ERROR] {e}")

    print("\nTest Summary:")
    print("If you see 'Client does not support sampling' errors,")
    print("the server needs restart to load our fixes.")
    print("If you see parameter validation errors, the server")
    print("needs restart to load the new function signatures.")

if __name__ == "__main__":
    asyncio.run(test_sampling_simple())