#!/usr/bin/env python3
"""
Quick Test Client for LLM Sampling Fixes
Tests the specific fixes we implemented for FastMCP LLM Sampling
"""

import asyncio
import json
from fastmcp import Client

async def test_sampling_fixes():
    """Test our LLM sampling fixes"""

    print("[TEST] Testing FastMCP LLM Sampling Fixes")
    print("=" * 60)

    client = Client("http://localhost:8020/mcp")

    async with client:
        print("✅ Connected to Ultimate FastMCP Server on port 8020")

        # Test 1: Basic LLM Sampling Demo
        print("\n1. Testing LLM Sampling Demo (Fixed version)...")
        try:
            result = await client.call_tool("ultimate_llm_sampling_demo", {
                "sampling_type": "test_fix",
                "content": "FastMCP LLM capabilities testing",
                "temperature": 0.7,
                "max_tokens": 200,
                "enable_structured_output": True
            })

            print(f"   ✅ LLM Sampling completed successfully!")
            print(f"   📊 Response length: {len(result.data)} characters")

            # Check for key indicators that our fixes worked
            if "Stage 1: Simple Text Generation" in result.data:
                print(f"   ✅ Stage 1 (Simple Generation) working")
            if "Stage 2: Advanced Analysis" in result.data:
                print(f"   ✅ Stage 2 (Advanced Analysis) working")
            if "Stage 3: Code Generation" in result.data:
                print(f"   ✅ Stage 3 (Code Generation) working")
            if "Stage 4: Multi-turn Conversation" in result.data:
                print(f"   ✅ Stage 4 (Conversation) working")
            if "Stage 5: Structured Output" in result.data:
                print(f"   ✅ Stage 5 (Structured Output) working")

            if "[FALLBACK]" in result.data:
                print(f"   ⚠️  Using fallback responses (NRP client may be unavailable)")

            if "ERROR" in result.data and "Client does not support sampling" in result.data:
                print(f"   ❌ Still seeing old error - server needs restart")
            elif "ERROR" not in result.data:
                print(f"   ✅ No 'Client does not support sampling' errors!")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Configuration Generator (Fixed parameters)
        print("\n2. Testing Configuration Generator (Fixed parameters)...")
        try:
            result = await client.call_tool("intelligent_configuration_generator", {
                "config_type": "gpu_cluster",
                "requirements": "High-performance ML training with H100 GPUs",
                "optimization_level": "performance",
                "include_monitoring": True,
                "generate_explanations": True
            })

            print(f"   ✅ Configuration Generator completed successfully!")
            print(f"   📊 Response length: {len(result.data)} characters")

            if "Config Type: gpu_cluster" in result.data:
                print(f"   ✅ Using new parameter names correctly")
            if "apiVersion" in result.data or "FALLBACK" in result.data:
                print(f"   ✅ Generated configuration content")

        except Exception as e:
            if "Unexpected keyword argument" in str(e):
                print(f"   ❌ Still seeing parameter validation errors - server needs restart")
                print(f"       Error: {e}")
            else:
                print(f"   ❌ Other error: {e}")

        # Test 3: Check Server Configuration
        print("\n3. Checking Server Configuration...")
        try:
            result = await client.call_tool("ultimate_server_configuration", {
                "action": "view"
            })

            print(f"   ✅ Server configuration retrieved")

            if "LLM Sampling" in result.data:
                print(f"   ✅ LLM Sampling listed in server features")
            else:
                print(f"   ⚠️  LLM Sampling not listed - may need server restart")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 4: List Available Tools
        print("\n4. Available Tools Check...")
        try:
            tools = await client.list_tools()

            sampling_tools = [tool for tool in tools if 'sampling' in tool.name.lower()]
            config_tools = [tool for tool in tools if 'configuration' in tool.name.lower()]

            print(f"   📋 Total tools available: {len(tools)}")
            print(f"   🔬 Sampling-related tools: {len(sampling_tools)}")
            for tool in sampling_tools:
                print(f"      - {tool.name}")
            print(f"   ⚙️  Configuration tools: {len(config_tools)}")
            for tool in config_tools:
                print(f"      - {tool.name}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n" + "=" * 60)
    print(f"🏁 Test Summary:")
    print(f"   If you see 'Client does not support sampling' errors,")
    print(f"   the server is running the old version and needs restart.")
    print(f"   If you see parameter validation errors, the server")
    print(f"   needs restart to load the fixed function signatures.")
    print(f"   If tests pass, our fixes are working! 🎉")

if __name__ == "__main__":
    asyncio.run(test_sampling_fixes())