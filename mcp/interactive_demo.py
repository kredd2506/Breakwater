#!/usr/bin/env python3
"""
Interactive Demo: Ask Questions + K8s Operations
===============================================
This demo shows how to:
1. Ask questions and get enhanced explanations
2. Perform actual K8s operations
3. Switch between explanation and command modes
"""

import asyncio
import json
from fastmcp import Client

class InteractiveDemo:
    def __init__(self):
        self.client = None

    async def connect(self):
        """Connect to the enhanced FastMCP server"""
        try:
            self.client = Client("http://localhost:8024/mcp")
            await self.client.__aenter__()
            print("[OK] Connected to GLM-4.5V Enhanced NRP K8s System")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    async def ask_question(self, question):
        """Ask a question and get enhanced explanation"""
        print(f"\n[QUESTION] {question}")
        print("=" * 60)

        try:
            result = await self.client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": question,
                    "context": "Interactive demo question"
                }
            })
            print("[ENHANCED RESPONSE]")
            print(result.data)
        except Exception as e:
            print(f"[ERROR] {e}")

    async def run_k8s_command(self, command_type, **kwargs):
        """Execute K8s operations"""
        print(f"\n[K8S OPERATION] {command_type}")
        print("-" * 40)

        try:
            if command_type == "list_pods":
                result = await self.client.call_tool("k8s_list_resources", {
                    "resource_type": "pods"
                })
            elif command_type == "list_deployments":
                result = await self.client.call_tool("k8s_list_resources", {
                    "resource_type": "deployments"
                })
            elif command_type == "get_cluster_info":
                result = await self.client.call_tool("k8s_get_cluster_info", {})
            elif command_type == "describe_pod" and "pod_name" in kwargs:
                result = await self.client.call_tool("k8s_describe_resource", {
                    "resource_type": "pod",
                    "resource_name": kwargs["pod_name"]
                })
            else:
                print(f"[INFO] Command '{command_type}' not implemented in demo")
                return

            print("[RESULT]")
            print(result.data)
        except Exception as e:
            print(f"[ERROR] {e}")

    async def demo_session(self):
        """Run a complete demo session"""
        print("=" * 70)
        print("INTERACTIVE DEMO: Questions + K8s Operations")
        print("=" * 70)

        if not await self.connect():
            return

        # Demo 1: Ask about GPU resources
        await self.ask_question("How do I request an A100 GPU in NRP Nautilus?")

        # Demo 2: Get cluster info
        await self.run_k8s_command("get_cluster_info")

        # Demo 3: Ask about storage
        await self.ask_question("What storage options are available?")

        # Demo 4: List pods
        await self.run_k8s_command("list_pods")

        # Demo 5: Ask about troubleshooting
        await self.ask_question("How do I troubleshoot pod startup issues?")

        # Demo 6: List deployments
        await self.run_k8s_command("list_deployments")

        print("\n" + "=" * 70)
        print("DEMO COMPLETE - You can now use the system interactively!")
        print("=" * 70)

        await self.client.__aexit__(None, None, None)

async def main():
    """Run the interactive demo"""
    demo = InteractiveDemo()
    await demo.demo_session()

if __name__ == "__main__":
    asyncio.run(main())