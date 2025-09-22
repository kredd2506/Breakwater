#!/usr/bin/env python3
"""
Test Enhanced Server with GLM-4.5V
==================================
Quick test to verify GLM-4.5V integration is working
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastmcp import Client

async def test_glm_direct():
    """Test GLM-4.5V directly"""
    print("=" * 60)
    print("Testing GLM-4.5V Direct Connection")
    print("=" * 60)

    # Load environment
    load_dotenv()

    print(f"NRP_API_KEY: {'✓ Set' if os.getenv('NRP_API_KEY') else '✗ Missing'}")
    print(f"NRP_BASE_URL: {os.getenv('NRP_BASE_URL', 'Missing')}")
    print(f"NRP_MODEL: {os.getenv('NRP_MODEL', 'Missing')}")

    try:
        # Test GLM-V client
        client = AsyncOpenAI(
            api_key=os.getenv("NRP_API_KEY"),
            base_url=os.getenv("NRP_BASE_URL")
        )

        print("\n[TEST] Testing GLM-4.5V response generation...")
        response = await client.chat.completions.create(
            model=os.getenv("NRP_MODEL", "glm-v"),
            messages=[
                {"role": "system", "content": "You are an expert NRP Nautilus platform specialist."},
                {"role": "user", "content": "How do I request an A100 GPU in NRP Nautilus? Provide a detailed explanation with steps."}
            ],
            temperature=0.7,
            max_tokens=500
        )

        print("[SUCCESS] GLM-4.5V Response:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)

        return True

    except Exception as e:
        print(f"[ERROR] GLM-4.5V test failed: {e}")
        return False

async def test_enhanced_server():
    """Test the enhanced server via FastMCP"""
    print("\n" + "=" * 60)
    print("Testing Enhanced Server via FastMCP")
    print("=" * 60)

    try:
        async with Client("http://localhost:8024/mcp") as client:
            print("[TEST] Testing enhanced intelligent_k8s_query...")
            result = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "How do I request an A100 GPU with detailed explanation?",
                    "context": "Testing enhanced GLM-4.5V response"
                }
            })

            response = result.data

            # Check if we get comprehensive explanation
            if "## Comprehensive Explanation" in response:
                print("[SUCCESS] ✓ Enhanced explanations working!")
                print("Response includes both links AND comprehensive explanation")
            elif "GLM-V explanation generation" in response:
                print("[PARTIAL] GLM-V integration present but may have failed")
            else:
                print("[ISSUE] ✗ Only getting basic link responses")
                print("GLM-4.5V enhanced explanations not working")

            print("\n[RESPONSE SAMPLE]")
            print(response[:500] + "..." if len(response) > 500 else response)

    except Exception as e:
        print(f"[ERROR] Server test failed: {e}")

async def main():
    """Run all tests"""
    glm_working = await test_glm_direct()

    if glm_working:
        await test_enhanced_server()
    else:
        print("\n[SKIP] Skipping server test due to GLM-4.5V connection issues")

if __name__ == "__main__":
    asyncio.run(main())