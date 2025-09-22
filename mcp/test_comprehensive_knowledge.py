#!/usr/bin/env python3
"""
Test Comprehensive NRP Knowledge Base
=====================================
Test the updated server with comprehensive NRP documentation knowledge.
"""

import asyncio
from fastmcp import Client

class ComprehensiveKnowledgeTest:
    def __init__(self, server_url="http://localhost:8024/mcp"):
        self.client = Client(server_url)
        self.server_url = server_url

    async def test_comprehensive_queries(self):
        """Test various NRP-specific queries with the comprehensive knowledge base"""
        print("[TEST] Testing Comprehensive NRP Knowledge Base")
        print("=" * 60)

        test_queries = [
            # Storage queries
            "How do I use persistent storage on NRP?",
            "What storage classes are available?",
            "How do I mount volumes to pods?",

            # Policy queries
            "What are the resource limits on NRP?",
            "What are the cluster policies I need to follow?",
            "How long can my pods run?",

            # Jobs queries
            "How do I create a Kubernetes job?",
            "What's the difference between jobs and pods?",
            "How do I run batch processing?",

            # Getting started queries
            "How do I get started with NRP Nautilus?",
            "How do I configure kubectl for NRP?",
            "What do I need to know as a new user?",

            # Networking queries
            "How do I expose my service?",
            "What service types are available?",
            "How do I set up ingress?",

            # GPU queries (should still work)
            "How can users request an A100 GPU for their Kubernetes pod?",

            # General queries
            "How do I troubleshoot failing pods?",
            "What are best practices for resource management?"
        ]

        async with self.client:
            print(f"[OK] Connected to server: {self.server_url}")

            for i, query in enumerate(test_queries, 1):
                print(f"\n[TEST] Test {i:2d}: {query}")
                print("-" * 50)

                try:
                    result = await self.client.call_tool("intelligent_k8s_query", {
                        "params": {"query": query, "context": "Testing comprehensive knowledge"}
                    })

                    response = result.data

                    # Check if it's providing NRP-specific information
                    if "NRP Nautilus Documentation:" in response:
                        print("[OK] NRP-Specific Documentation Found")
                        # Show first few lines of response
                        lines = response.split('\n')[:8]
                        for line in lines:
                            print(f"   {line}")
                        if len(response.split('\n')) > 8:
                            print("   ...")
                    elif "Source: https://nrp.ai/documentation" in response:
                        print("[OK] NRP Documentation Source Cited")
                        # Show first few lines
                        lines = response.split('\n')[:5]
                        for line in lines:
                            print(f"   {line}")
                    else:
                        print("[WARN] Generic Response (not NRP-specific)")
                        # Show first few lines to understand what we got
                        lines = response.split('\n')[:3]
                        for line in lines:
                            print(f"   {line}")

                except Exception as e:
                    print(f"[ERROR] Error: {e}")

                # Add small delay between tests
                await asyncio.sleep(0.5)

    async def test_quick_reference(self):
        """Test the new quick reference tool"""
        print(f"\n[TOOL] Testing NRP Quick Reference Tool")
        print("=" * 40)

        async with self.client:
            try:
                result = await self.client.call_tool("nrp_quick_reference", {})
                print("[OK] Quick Reference Generated:")
                print(result.data[:500] + "..." if len(result.data) > 500 else result.data)
            except Exception as e:
                print(f"[ERROR] Error: {e}")

    async def run_all_tests(self):
        """Run all comprehensive tests"""
        await self.test_comprehensive_queries()
        await self.test_quick_reference()

        print(f"\n[COMPLETE] Comprehensive Knowledge Base Testing Complete!")
        print("=" * 60)

async def main():
    tester = ComprehensiveKnowledgeTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())