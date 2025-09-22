#!/usr/bin/env python3
"""
Test Anchor-Based NRP Knowledge System
======================================
Test the updated server with precise anchor-based documentation links.
"""

import asyncio
from fastmcp import Client

class AnchorKnowledgeTest:
    def __init__(self, server_url="http://localhost:8024/mcp"):
        self.client = Client(server_url)
        self.server_url = server_url

    async def test_anchor_specific_queries(self):
        """Test queries that should return specific anchor links"""
        print("[ANCHOR-TEST] Testing Anchor-Based NRP Knowledge System")
        print("=" * 65)

        test_queries = [
            # GPU-specific anchor tests
            ("How can users request an A100 GPU for their Kubernetes pod?", "requesting-special-gpus"),
            ("Which GPU type should I choose?", "choosing-gpu-type"),
            ("How do I select CUDA version?", "selecting-cuda-version"),

            # Getting started anchor tests
            ("How do I configure kubectl for NRP?", "cluster-access-via-kubectl"),
            ("How do I get access and log in?", "get-access-and-log-in"),
            ("What GUI tools are available?", "gui-tools-for-kubernetes"),

            # Policy anchor tests
            ("What are the resource allocation policies?", "resource-allocation"),
            ("What happens if I violate usage rules?", "resource-usage-violations"),
            ("How long can interactive pods run?", "interactive-use-6-hours-max-runtime"),

            # Storage anchor tests
            ("How do I create a PVC?", "creating-a-persistent-volume-claim"),
            ("What storage classes are available?", "exploring-storageclasses"),
            ("How do I create an emptyDir volume?", "create-an-emptydir"),

            # Job anchor tests
            ("How do I run batch jobs?", "batch-jobs"),
            ("What are the learning objectives for jobs?", "learning-objectives")
        ]

        async with self.client:
            print(f"[OK] Connected to server: {self.server_url}")

            for i, (query, expected_anchor) in enumerate(test_queries, 1):
                print(f"\n[TEST] {i:2d}: {query}")
                print(f"Expected anchor: #{expected_anchor}")
                print("-" * 60)

                try:
                    result = await self.client.call_tool("intelligent_k8s_query", {
                        "params": {"query": query, "context": "Testing anchor-based retrieval"}
                    })

                    response = result.data

                    # Check if it provides NRP-specific documentation with anchor
                    if "NRP Nautilus Documentation:" in response:
                        if expected_anchor in response:
                            print("[PERFECT] Exact anchor match found!")
                        elif "Source: https://nrp.ai/documentation" in response:
                            print("[GOOD] NRP documentation provided")
                        else:
                            print("[OK] NRP-specific documentation found")

                        # Show first few lines
                        lines = response.split('\n')[:8]
                        for line in lines:
                            print(f"   {line}")
                        if len(response.split('\n')) > 8:
                            print("   ...")
                    else:
                        print("[WARN] No NRP-specific documentation found")
                        lines = response.split('\n')[:3]
                        for line in lines:
                            print(f"   {line}")

                except Exception as e:
                    print(f"[ERROR] {e}")

                await asyncio.sleep(0.3)

    async def test_anchor_tools(self):
        """Test the new anchor-specific tools"""
        print(f"\n[TOOLS] Testing Anchor-Based Tools")
        print("=" * 40)

        async with self.client:
            # Test quick reference with anchors
            print("[TOOL] Testing nrp_quick_reference with anchors...")
            try:
                result = await self.client.call_tool("nrp_quick_reference", {})
                print("[OK] Anchor-based quick reference generated:")
                print(result.data[:400] + "..." if len(result.data) > 400 else result.data)
            except Exception as e:
                print(f"[ERROR] {e}")

            print(f"\n[TOOL] Testing nrp_anchor_urls...")
            try:
                result = await self.client.call_tool("nrp_anchor_urls", {})
                print("[OK] All anchor URLs retrieved:")
                print(result.data[:500] + "..." if len(result.data) > 500 else result.data)
            except Exception as e:
                print(f"[ERROR] {e}")

    async def test_anchor_precision(self):
        """Test that we get precise anchor links for specific queries"""
        print(f"\n[PRECISION] Testing Anchor Link Precision")
        print("=" * 45)

        precision_tests = [
            ("A100 GPU request", "requesting-special-gpus"),
            ("kubectl setup", "cluster-access-via-kubectl"),
            ("resource limits", "resource-allocation"),
            ("storage classes", "exploring-storageclasses"),
        ]

        async with self.client:
            for query, expected_anchor in precision_tests:
                print(f"\nQuery: '{query}' -> Expected: #{expected_anchor}")
                try:
                    result = await self.client.call_tool("intelligent_k8s_query", {
                        "params": {"query": query, "context": "Precision test"}
                    })

                    if expected_anchor in result.data:
                        print("[PERFECT] ✓ Exact anchor found in response")
                    elif "https://nrp.ai/documentation" in result.data:
                        print("[GOOD] ✓ NRP documentation referenced")
                    else:
                        print("[WARN] ? No specific anchor or documentation link")

                except Exception as e:
                    print(f"[ERROR] {e}")

    async def run_all_tests(self):
        """Run all anchor-based tests"""
        await self.test_anchor_specific_queries()
        await self.test_anchor_tools()
        await self.test_anchor_precision()

        print(f"\n[COMPLETE] Anchor-Based Knowledge System Testing Complete!")
        print("=" * 65)

async def main():
    tester = AnchorKnowledgeTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())