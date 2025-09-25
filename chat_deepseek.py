#!/usr/bin/env python3
"""
Simple Chat Interface for DeepSeek-R1 NRP K8s System
Direct interaction with DeepSeek-R1 API for continuous conversation
"""

import asyncio
from openai import AsyncOpenAI

class DeepSeekChat:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key="60giG4L3xNAMC1FT2f2ivYnExpHYA1fD",
            base_url="https://ellm.nrp-nautilus.io/v1"
        )
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an expert assistant for the National Research Platform (NRP) Kubernetes system with DeepSeek-R1 intelligence.

You help users with:
- Kubernetes operations and troubleshooting
- GPU allocation and resource management (A100, A40, RTX series)
- Container deployment and configuration
- NRP-specific features and capabilities
- Research computing workflows
- YAML configuration and best practices

Provide detailed, accurate, and actionable responses. Be conversational and helpful."""
            }
        ]

    def print_header(self):
        print("=" * 80)
        print("    🚀 NRP K8s DeepSeek-R1 Chat Interface")
        print("    Connected to: https://ellm.nrp-nautilus.io/v1")
        print("    Model: deepseek-r1")
        print("=" * 80)
        print("Ask me anything about NRP, Kubernetes, GPUs, deployments, etc.")
        print("Commands: '/help' for help, '/history' to see chat, '/quit' to exit")
        print("=" * 80)

    def show_help(self):
        print("\n=== 🤖 HELP - DeepSeek-R1 NRP Assistant ===")
        print("I can help you with:")
        print("• GPU Requests: 'How do I request A100 GPUs?'")
        print("• Deployments: 'Show me a deployment YAML for TensorFlow'")
        print("• Troubleshooting: 'My pod is stuck in Pending, why?'")
        print("• Resources: 'What GPU types are available on NRP?'")
        print("• Storage: 'How do I mount persistent volumes?'")
        print("• Networking: 'How do I expose my service?'")
        print("• Best Practices: 'What are the resource limits I should set?'")
        print("==========================================\n")

    def show_history(self):
        print("\n=== 📚 CONVERSATION HISTORY ===")
        for i, msg in enumerate(self.conversation_history[1:], 1):  # Skip system message
            role = "🧑 YOU" if msg["role"] == "user" else "🤖 DeepSeek-R1"
            content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{i}. {role}: {content_preview}")
        print("==============================\n")

    async def get_response(self, user_input):
        """Get response from DeepSeek-R1"""
        try:
            # Add user message to conversation
            self.conversation_history.append({"role": "user", "content": user_input})

            # Get response from DeepSeek-R1
            response = await self.client.chat.completions.create(
                model="deepseek-r1",
                messages=self.conversation_history,
                max_tokens=3000,
                temperature=0.7,
                top_p=0.9
            )

            assistant_response = response.choices[0].message.content

            # Add assistant response to conversation
            self.conversation_history.append({"role": "assistant", "content": assistant_response})

            return assistant_response

        except Exception as e:
            return f"🚨 Error: {str(e)}\n\nPlease try again or check your connection."

    def format_response(self, response):
        """Format the response with encoding safety"""
        try:
            return response
        except UnicodeEncodeError:
            # Handle any encoding issues
            return response.encode('ascii', errors='replace').decode('ascii')

    async def chat_loop(self):
        """Main chat interaction loop"""
        self.print_header()

        while True:
            try:
                # Get user input
                print("\n" + "─" * 60)
                user_input = input("🧑 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("\n👋 Goodbye! Thanks for using DeepSeek-R1 NRP Chat!")
                    break

                elif user_input.lower() in ['/help', 'help']:
                    self.show_help()
                    continue

                elif user_input.lower() in ['/history', 'history']:
                    self.show_history()
                    continue

                # Show thinking indicator
                print("🤖 DeepSeek-R1: [Analyzing and thinking...]", end="", flush=True)

                # Get response
                response = await self.get_response(user_input)

                # Clear thinking indicator and show response
                print("\r" + " " * 50 + "\r", end="")
                print(f"🤖 DeepSeek-R1:\n\n{self.format_response(response)}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! (Interrupted by Ctrl+C)")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n🚨 Unexpected error: {e}")
                continue

async def main():
    print("🚀 Starting DeepSeek-R1 NRP Chat Interface...")
    chat = DeepSeekChat()
    await chat.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())