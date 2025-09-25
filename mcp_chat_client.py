#!/usr/bin/env python3
"""
MCP Chat Client for DeepSeek-R1 NRP K8s System
Interactive chat interface for the running MCP server
"""

import asyncio
import json
import sys
import aiohttp
from pathlib import Path
from datetime import datetime

class MCPChatClient:
    def __init__(self, server_url="http://127.0.0.1:8025/mcp"):
        self.server_url = server_url
        self.session_id = None
        self.conversation_history = []

    async def connect(self):
        """Initialize connection to MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json"
                }

                # Test connection
                async with session.get(self.server_url, headers=headers) as response:
                    if response.status == 200:
                        print("[OK] Connected to MCP server")
                        return True
                    else:
                        print(f"[ERROR] Server responded with status: {response.status}")
                        return False

        except Exception as e:
            print(f"[ERROR] Failed to connect to MCP server: {e}")
            return False

    def print_header(self):
        """Print chat interface header"""
        print("=" * 80)
        print("    NRP K8s System Chat Interface - DeepSeek-R1 Edition")
        print("    Connected to MCP Server: http://127.0.0.1:8025/mcp")
        print("=" * 80)
        print("Commands:")
        print("  - Type your questions about NRP, Kubernetes, GPUs, etc.")
        print("  - Type '/help' for assistance")
        print("  - Type '/history' to see conversation history")
        print("  - Type '/quit' or '/exit' to exit")
        print("=" * 80)

    def save_message(self, role, content):
        """Save message to conversation history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_history.append({
            "timestamp": timestamp,
            "role": role,
            "content": content
        })

    def show_history(self):
        """Display conversation history"""
        print("\n" + "-" * 60)
        print("CONVERSATION HISTORY")
        print("-" * 60)

        for msg in self.conversation_history:
            role_display = "YOU" if msg["role"] == "user" else "NRP-AI"
            print(f"[{msg['timestamp']}] {role_display}: {msg['content'][:100]}...")

        print("-" * 60)

    async def send_direct_api_query(self, user_input):
        """Send query directly to DeepSeek-R1 API as fallback"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key="60giG4L3xNAMC1FT2f2ivYnExpHYA1fD",
                base_url="https://ellm.nrp-nautilus.io/v1"
            )

            # Create a context-aware prompt for NRP/K8s queries
            system_prompt = """You are an expert assistant for the National Research Platform (NRP) Kubernetes system.
You help users with:
- Kubernetes operations and troubleshooting
- GPU allocation and resource management
- Container deployment and configuration
- NRP-specific features and capabilities
- Research computing workflows

Provide detailed, accurate, and actionable responses."""

            response = await client.chat.completions.create(
                model="deepseek-r1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"[ERROR] DeepSeek-R1 API call failed: {e}"

    async def chat_loop(self):
        """Main chat interaction loop"""
        self.print_header()

        # Test connection
        if not await self.connect():
            print("\n[WARNING] Could not connect to MCP server. Using direct DeepSeek-R1 API.")
            print("Note: You may want to ensure the MCP server is running on port 8025.\n")

        print("\nReady for chat! Ask me anything about NRP, Kubernetes, GPUs, etc.\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['/quit', '/exit']:
                    print("\nGoodbye! Thanks for using the NRP K8s Chat System.")
                    break

                elif user_input.lower() == '/help':
                    print("\n=== HELP ===")
                    print("This chat interface connects to the NRP K8s System with DeepSeek-R1 model.")
                    print("\nExample questions:")
                    print("- How do I request A100 GPUs in Kubernetes?")
                    print("- What are the differences between GPU types available?")
                    print("- How do I configure shared memory for GPU pods?")
                    print("- Show me examples of NRP deployment YAML files")
                    print("- What are the best practices for container resource limits?")
                    continue

                elif user_input.lower() == '/history':
                    self.show_history()
                    continue

                # Save user message
                self.save_message("user", user_input)

                # Show thinking indicator
                print("NRP-AI: [Thinking...]", end="", flush=True)

                # Get response from DeepSeek-R1 API
                response = await self.send_direct_api_query(user_input)

                # Clear thinking indicator and show response
                print("\r" + " " * 20 + "\r", end="")  # Clear the thinking message
                print(f"NRP-AI: {response}\n")

                # Save assistant response
                self.save_message("assistant", response)

            except KeyboardInterrupt:
                print("\n\nGoodbye! (Interrupted by user)")
                break
            except Exception as e:
                print(f"\n[ERROR] Chat error: {e}")
                continue

    async def run(self):
        """Run the chat client"""
        await self.chat_loop()

if __name__ == "__main__":
    print("Starting NRP K8s Chat Client with DeepSeek-R1...")

    try:
        client = MCPChatClient()
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"[ERROR] Failed to start chat client: {e}")
        sys.exit(1)