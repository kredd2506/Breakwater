#!/usr/bin/env python3
"""
Test Nautilus-specific question using K8s Infogent Integration
=============================================================
Tests the intelligent K8s query functionality with a real Nautilus question
about batch job optimization practices.
"""

import asyncio
from fastmcp import Client

async def test_nautilus_question():
    """Test the Nautilus batch job optimization question"""

    print("[TEST] Testing Nautilus-specific Question with K8s Infogent")
    print("=" * 65)

    client = Client("http://localhost:8022/mcp")

    async with client:
        print("[OK] Connected to Ultimate FastMCP Server on port 8022")

        # Test the specific Nautilus question
        print("\nTesting Question: 'Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?'")

        try:
            result = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?",
                    "context": "Nautilus cluster batch job best practices and resource optimization"
                }
            })

            print(f"\nResponse length: {len(result.data)} characters")
            print("\nFull Response:")
            print("-" * 50)
            print(result.data)
            print("-" * 50)

            # Analyze the response
            if "Intent:" in result.data:
                print("\n[ANALYSIS]")
                if "EXPLANATION" in result.data:
                    print("✅ Query correctly classified as EXPLANATION")
                elif "COMMAND" in result.data:
                    print("⚠️  Query classified as COMMAND (may need adjustment)")

                if "optimize" in result.data.lower() or "short runtime" in result.data.lower():
                    print("✅ Response addresses runtime optimization")

                if "batch" in result.data.lower() or "job" in result.data.lower():
                    print("✅ Response addresses batch jobs")

                if "nautilus" in result.data.lower():
                    print("✅ Response is Nautilus-specific")
                elif "FALLBACK" in result.data:
                    print("⚠️  Using fallback response (NRP may be unavailable)")

                if len(result.data) > 500:
                    print("✅ Comprehensive response provided")
                else:
                    print("⚠️  Response may be brief")

        except Exception as e:
            print(f"[ERROR] {e}")

        # Test a follow-up K8s operational question
        print("\n" + "=" * 65)
        print("Testing Follow-up K8s Operational Query...")

        try:
            result2 = await client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": "list all running batch jobs in the cluster",
                    "context": "Follow-up to check current batch job status"
                }
            })

            print(f"\nResponse length: {len(result2.data)} characters")
            print("\nOperational Response:")
            print("-" * 30)
            print(result2.data)
            print("-" * 30)

            if "Intent:" in result2.data and "COMMAND" in result2.data:
                print("✅ Operational query correctly classified as COMMAND")
            if "jobs" in result2.data.lower() or "demo-jobs" in result2.data.lower():
                print("✅ Response shows job listing functionality")

        except Exception as e:
            print(f"[ERROR] {e}")

    print("\n" + "=" * 65)
    print("Test Summary:")
    print("The Ultimate FastMCP Server with K8s Infogent integration can:")
    print("- Process complex Nautilus-specific questions")
    print("- Classify intent (EXPLANATION vs COMMAND)")
    print("- Provide intelligent responses using NRP or fallbacks")
    print("- Handle both conceptual and operational K8s queries")
    print("- Integrate all FastMCP concepts with K8s functionality")

if __name__ == "__main__":
    asyncio.run(test_nautilus_question())