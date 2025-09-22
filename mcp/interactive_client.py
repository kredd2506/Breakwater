#!/usr/bin/env python3
"""
Interactive Ultimate FastMCP Client
===================================
Simple script to interact with your Ultimate FastMCP server.
Ask questions, run K8s commands, and explore capabilities.
"""

import asyncio
from fastmcp import Client

class InteractiveClient:
    def __init__(self, server_url="http://localhost:8024/mcp"):
        self.client = Client(server_url)
        self.server_url = server_url

    async def start_session(self):
        """Start an interactive session"""
        print("🚀 Ultimate FastMCP Interactive Client")
        print("=" * 50)
        print(f"Connected to: {self.server_url}")
        print("Type 'help' for commands, 'quit' to exit")
        print("=" * 50)

        async with self.client:
            # Quick connection test
            try:
                await self.client.ping()
                print("✅ Server connection successful!")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                return

            # Main interaction loop
            while True:
                try:
                    command = input("\n> ").strip()

                    if command.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    elif command.lower() == 'help':
                        await self.show_help()
                    elif command.lower() == 'tools':
                        await self.list_tools()
                    elif command.lower().startswith('ask '):
                        question = command[4:]
                        await self.ask_question(question)
                    elif command.lower() == 'pods':
                        await self.list_pods()
                    elif command.lower() == 'deployments':
                        await self.list_deployments()
                    elif command.lower() == 'services':
                        await self.list_services()
                    elif command.lower() == 'cluster':
                        await self.cluster_info()
                    elif command.lower().startswith('deploy '):
                        app_name = command[7:]
                        await self.quick_deploy(app_name)
                    elif command.lower().startswith('logs '):
                        pod_name = command[5:]
                        await self.get_logs(pod_name)
                    elif command.lower().startswith('describe '):
                        resource = command[9:]
                        await self.describe_resource(resource)
                    elif command.lower() == 'gpu':
                        await self.gpu_deployment()
                    elif command.lower() == 'config':
                        await self.server_config()
                    else:
                        print("❓ Unknown command. Type 'help' for available commands.")

                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")

    async def show_help(self):
        """Show available commands"""
        help_text = """
🔧 AVAILABLE COMMANDS:

📋 General:
  help          - Show this help
  tools         - List all available tools
  quit/exit/q   - Exit the client

🧠 AI & Questions:
  ask <question>    - Ask any Kubernetes or technical question
                     Example: ask How do I scale my pods?

☸️ Kubernetes Operations:
  cluster          - Get cluster information
  pods             - List all pods
  deployments      - List all deployments
  services         - List all services
  logs <pod-name>  - Get logs from a pod
  describe <name>  - Describe a resource (pod/deployment)
  deploy <name>    - Quick deploy an nginx pod with given name

🚀 Advanced:
  gpu             - Run GPU deployment simulation
  config          - View server configuration

💡 Examples:
  > ask What is a Kubernetes service?
  > pods
  > deploy my-test-app
  > logs my-test-app
  > ask How do I troubleshoot a failing pod?
        """
        print(help_text)

    async def list_tools(self):
        """List all available tools"""
        try:
            tools = await self.client.list_tools()
            print(f"\n📋 Available Tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"  {i:2d}. {tool.name}")
        except Exception as e:
            print(f"❌ Error listing tools: {e}")

    async def ask_question(self, question):
        """Ask an intelligent question"""
        print(f"🤔 Processing: {question}")
        try:
            result = await self.client.call_tool("intelligent_k8s_query", {
                "params": {"query": question}
            })
            print(f"\n💡 Answer:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def list_pods(self):
        """List all pods"""
        try:
            result = await self.client.call_tool("k8s_list_resources", {
                "resource_type": "pods"
            })
            print(f"\n📦 Pods in cluster:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def list_deployments(self):
        """List all deployments"""
        try:
            result = await self.client.call_tool("k8s_list_resources", {
                "resource_type": "deployments"
            })
            print(f"\n🚀 Deployments in cluster:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def list_services(self):
        """List all services"""
        try:
            result = await self.client.call_tool("k8s_list_resources", {
                "resource_type": "services"
            })
            print(f"\n🌐 Services in cluster:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def cluster_info(self):
        """Get cluster information"""
        try:
            result = await self.client.call_tool("k8s_get_cluster_info", {})
            print(f"\n☸️ Cluster Information:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def quick_deploy(self, app_name):
        """Quick deploy a simple nginx pod"""
        print(f"🚀 Deploying {app_name}...")
        try:
            result = await self.client.call_tool("k8s_create_pod", {
                "params": {
                    "name": app_name,
                    "image": "nginx",
                    "memory_limit": "128Mi",
                    "cpu_limit": "100m",
                    "memory_request": "64Mi",
                    "cpu_request": "50m"
                }
            })
            print(f"✅ Deployment result:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def get_logs(self, pod_name):
        """Get logs from a pod"""
        try:
            result = await self.client.call_tool("k8s_get_logs", {
                "pod_name": pod_name,
                "tail_lines": 20
            })
            print(f"\n📄 Logs for {pod_name}:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def describe_resource(self, resource_name):
        """Describe a resource"""
        try:
            result = await self.client.call_tool("k8s_describe_resource", {
                "resource_type": "pod",
                "resource_name": resource_name
            })
            print(f"\n📋 Description of {resource_name}:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def gpu_deployment(self):
        """Run GPU deployment simulation"""
        print("🎮 Running GPU deployment simulation...")
        try:
            result = await self.client.call_tool("ultimate_gpu_deployment_with_progress", {
                "gpu_type": "a100",
                "gpu_count": 1,
                "memory_gb": 16,
                "cpu_cores": 4,
                "namespace": "interactive-test",
                "workload_type": "ml_inference",
                "enable_monitoring": True,
                "user_id": "interactive_user"
            })
            print(f"🎯 GPU Deployment Result:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def server_config(self):
        """View server configuration"""
        try:
            result = await self.client.call_tool("ultimate_server_configuration", {
                "action": "view"
            })
            print(f"\n⚙️ Server Configuration:\n{result.data}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    client = InteractiveClient()
    await client.start_session()

if __name__ == "__main__":
    asyncio.run(main())