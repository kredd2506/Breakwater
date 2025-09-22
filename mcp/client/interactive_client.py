#!/usr/bin/env python3
"""
Interactive NRP K8s Client with Intent Classification Agent
==========================================================
Enhanced interactive client featuring intelligent intent classification
and conversational interface for NRP Kubernetes operations.

Features:
- Real-time intent classification (COMMAND, EXPLANATION, UNCLEAR)
- Interactive chat interface with command history
- Intelligent query routing and context awareness
- Ultra-comprehensive NRP documentation integration
- Session management and conversation memory
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

from fastmcp import Client

class IntentClassificationAgent:
    """Intelligent agent for classifying user intent"""

    def __init__(self, client: Client):
        self.client = client
        self.intent_history = []

    async def classify_intent(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Classify user intent using the server's intelligent routing"""
        try:
            # Use the server's intelligent query function which includes intent classification
            result = await self.client.call_tool("intelligent_k8s_query", {
                "params": {
                    "query": user_input,
                    "context": f"Intent classification request. {context}"
                }
            })

            # Parse the result to extract intent information
            response_text = result.data

            # Simple intent detection based on response patterns
            if "Intent: COMMAND" in response_text:
                intent_type = "COMMAND"
            elif "Intent: EXPLANATION" in response_text:
                intent_type = "EXPLANATION"
            else:
                intent_type = "UNCLEAR"

            classification = {
                "intent": intent_type,
                "confidence": 0.9 if intent_type != "UNCLEAR" else 0.3,
                "user_input": user_input,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "full_response": response_text
            }

            self.intent_history.append(classification)
            return classification

        except Exception as e:
            return {
                "intent": "ERROR",
                "confidence": 0.0,
                "user_input": user_input,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_intent_summary(self) -> Dict[str, Any]:
        """Get summary of intent classification history"""
        if not self.intent_history:
            return {"total": 0, "breakdown": {}}

        breakdown = {}
        for classification in self.intent_history:
            intent = classification["intent"]
            breakdown[intent] = breakdown.get(intent, 0) + 1

        return {
            "total": len(self.intent_history),
            "breakdown": breakdown,
            "recent_intents": [c["intent"] for c in self.intent_history[-5:]]
        }

class InteractiveNRPClient:
    """Interactive client with intent classification and conversation management"""

    def __init__(self, server_url: str = "http://localhost:8024/mcp"):
        self.server_url = server_url
        self.client = Client(server_url)
        self.intent_agent = None
        self.conversation_history = []
        self.session_start = datetime.now()
        self.command_count = 0

        # Setup readline for command history
        self.setup_readline()

    def setup_readline(self):
        """Setup readline for command history and completion"""
        if not READLINE_AVAILABLE:
            return

        try:
            # Common K8s and NRP commands for completion
            self.common_commands = [
                "list pods", "describe pod", "get services", "create deployment",
                "delete pod", "apply manifest", "get nodes", "check cluster status",
                "how to request GPU", "what is Nautilus", "storage options",
                "networking guide", "troubleshooting help", "upgrade procedures",
                "help", "exit", "quit", "status", "history", "clear"
            ]

            def completer(text, state):
                options = [cmd for cmd in self.common_commands if cmd.startswith(text)]
                return options[state] if state < len(options) else None

            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")

        except Exception:
            # readline setup failed
            pass

    async def __aenter__(self):
        """Async context manager entry"""
        await self.client.__aenter__()
        self.intent_agent = IntentClassificationAgent(self.client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def display_banner(self):
        """Display interactive client banner"""
        print("+" + "=" * 70 + "+")
        print("|" + " " * 8 + "Interactive NRP K8s Client with Intent Classification" + " " * 8 + "|")
        print("|" + " " * 22 + "Ultra-Comprehensive Knowledge Base" + " " * 14 + "|")
        print("+" + "=" * 70 + "+")
        print("| Commands: help, exit, status, history, clear                      |")
        print("| Features: Intent classification, K8s operations, NRP docs         |")
        print("| Coverage: 115 pages, 1,386 anchors (100% sidebar navigation)     |")
        print("+" + "=" * 70 + "+")
        print()

    def display_help(self):
        """Display help information"""
        print("\n[HELP] Interactive NRP K8s Client Help")
        print("=" * 40)
        print("[EXAMPLES] Query Examples:")
        print("   * 'list my pods'")
        print("   * 'How do I request an A100 GPU?'")
        print("   * 'What storage options are available?'")
        print("   * 'create a deployment with 2 replicas'")
        print("   * 'troubleshoot XFS corruption issues'")
        print()
        print("[INTENT] Intent Types:")
        print("   * COMMAND: Direct K8s operations (list, create, delete, etc.)")
        print("   * EXPLANATION: Documentation and guidance queries")
        print("   * UNCLEAR: Ambiguous requests needing clarification")
        print()
        print("[COMMANDS] System Commands:")
        print("   * help     - Show this help")
        print("   * status   - Show session status")
        print("   * history  - Show conversation history")
        print("   * clear    - Clear screen")
        print("   * exit/quit - Exit the client")
        print()

    def display_status(self):
        """Display current session status"""
        session_duration = datetime.now() - self.session_start
        intent_summary = self.intent_agent.get_intent_summary() if self.intent_agent else {"total": 0}

        print(f"\n[STATUS] Session Status")
        print("=" * 30)
        print(f"[TIME] Session Duration: {session_duration}")
        print(f"[COUNT] Total Queries: {self.command_count}")
        print(f"[INTENT] Intent Classifications: {intent_summary['total']}")
        if intent_summary.get('breakdown'):
            for intent, count in intent_summary['breakdown'].items():
                print(f"   * {intent}: {count}")
        print(f"[SERVER] Server: {self.server_url}")
        print()

    def display_history(self):
        """Display conversation history"""
        print(f"\n[HISTORY] Conversation History")
        print("=" * 40)

        if not self.conversation_history:
            print("No conversation history yet.")
            return

        for i, entry in enumerate(self.conversation_history[-10:], 1):  # Show last 10
            timestamp = entry['timestamp']
            intent = entry.get('intent', 'UNKNOWN')
            query = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']

            print(f"{i:2d}. [{timestamp}] [{intent}] {query}")

        if len(self.conversation_history) > 10:
            print(f"... (showing last 10 of {len(self.conversation_history)} total)")
        print()

    async def process_query(self, user_input: str) -> Dict[str, Any]:
        """Process user query with intent classification and routing"""
        self.command_count += 1

        print(f"\n[BOT] Processing query... (#{self.command_count})")

        # Classify intent
        print("[INTENT] Classifying intent...")
        classification = await self.intent_agent.classify_intent(user_input)

        intent = classification['intent']
        confidence = classification.get('confidence', 0.0)

        print(f"   Intent: {intent} (confidence: {confidence:.1f})")

        # Store in conversation history
        conversation_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "query": user_input,
            "intent": intent,
            "confidence": confidence
        }

        # Get the full response
        response = classification.get('full_response', 'No response available')
        conversation_entry['response'] = response

        self.conversation_history.append(conversation_entry)

        # Display response
        print(f"\n[RESPONSE] Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)

        return conversation_entry

    async def run_interactive_session(self):
        """Run the main interactive session"""
        self.display_banner()

        # Test server connection
        try:
            await self.client.call_tool("k8s_get_cluster_info", {})
            print("[OK] Connected to NRP K8s server successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to connect to server: {e}")
            print("Please ensure the Ultimate FastMCP server is running on port 8024")
            return

        print("\nType 'help' for usage information, or start asking questions!")
        print("Examples: 'list my pods', 'How do I request GPUs?', 'help'\n")

        while True:
            try:
                # Get user input
                user_input = input("[NRP-K8s]> ").strip()

                if not user_input:
                    continue

                # Handle system commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n[EXIT] Thank you for using the Interactive NRP K8s Client!")
                    self.display_status()
                    break
                elif user_input.lower() == 'help':
                    self.display_help()
                    continue
                elif user_input.lower() == 'status':
                    self.display_status()
                    continue
                elif user_input.lower() == 'history':
                    self.display_history()
                    continue
                elif user_input.lower() == 'clear':
                    print("\033[2J\033[H")  # Clear screen
                    self.display_banner()
                    continue

                # Process the query
                await self.process_query(user_input)

            except KeyboardInterrupt:
                print("\n\n[INTERRUPT] Interrupted. Type 'exit' to quit gracefully.")
                continue
            except EOFError:
                print("\n\n[EOF] EOF detected. Exiting...")
                break
            except Exception as e:
                print(f"\n[ERROR] Error processing query: {e}")
                continue

async def main():
    """Main entry point for interactive client"""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive NRP K8s Client with Intent Classification")
    parser.add_argument("--server", default="http://localhost:8024/mcp",
                       help="FastMCP server URL (default: http://localhost:8024/mcp)")

    args = parser.parse_args()

    async with InteractiveNRPClient(args.server) as client:
        await client.run_interactive_session()

if __name__ == "__main__":
    asyncio.run(main())