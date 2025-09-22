#!/usr/bin/env python3
"""
Test Script for GLM-4.5V Enhanced NRP K8s System
===============================================
Demonstrates the enhanced capabilities with comprehensive explanations
alongside precise anchor links.
"""

import asyncio
import json
from fastmcp import Client

async def test_glm_enhanced_responses():
    """Test the GLM-4.5V enhanced responses with comprehensive explanations"""

    async with Client("http://localhost:8024/mcp") as client:
        print("=" * 80)
        print("[TEST] Testing GLM-4.5V Enhanced NRP K8s System")
        print("=" * 80)

        # Test queries that should trigger enhanced responses
        test_queries = [
            "How do I request an A100 GPU?",
            "What storage options are available?",
            "How to fix XFS corruption issues?",
            "How do I use my own domain name?",
            "What are the GPU allocation policies?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n[TEST {i}] Query: {query}")
            print("-" * 60)

            try:
                # Call the enhanced intelligent_k8s_query
                result = await client.call_tool("intelligent_k8s_query", {
                    "params": {
                        "query": query,
                        "context": "Testing GLM-4.5V enhanced responses"
                    }
                })

                print("[OK] Response received:")
                print(result.data)
                print("\n" + "=" * 80)

            except Exception as e:
                print(f"[ERROR] Error: {e}")
                print("=" * 80)

            # Add a small delay between requests
            await asyncio.sleep(2)

if __name__ == "__main__":
    print("Starting GLM-4.5V Integration Test...")
    asyncio.run(test_glm_enhanced_responses())