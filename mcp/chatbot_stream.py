#!/usr/bin/env python3
"""
Lightweight Streaming Chatbot for MCP
Using existing working MCP architecture
"""

import gradio as gr
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def chat_stream(message, history):
    """Stream chat responses using existing MCP architecture"""
    try:
        # Import the working interactive session
        from your_interactive_session import InteractiveNRPSession

        session = InteractiveNRPSession()

        # Classify intent
        intent = await session.classify_intent(message)

        # Start streaming response
        response = f"🎯 {intent}\n\n"
        yield response

        # Process based on intent
        if intent == "COMMAND":
            response += "⚙️ Processing K8s command...\n"
            yield response

            result = await session.process_k8s_command(message)
            response += f"```\n{result}\n```"

        elif intent == "QUESTION":
            response += "📚 Searching documentation...\n"
            yield response

            result = await session.ask_question(message)
            response += result

        else:
            response += "ℹ️ Ready for your next query!"

        yield response

    except Exception as e:
        yield f"❌ Error: {str(e)}"

def chat_wrapper(message, history):
    """Wrapper to handle async streaming in Gradio"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Convert async generator to sync for Gradio
        async_gen = chat_stream(message, history)

        async def collect_responses():
            responses = []
            async for response in async_gen:
                responses.append(response)
            return responses

        responses = loop.run_until_complete(collect_responses())

        # Yield each response for streaming effect
        for response in responses:
            yield response

    finally:
        loop.close()

# Create lightweight chatbot
demo = gr.ChatInterface(
    chat_wrapper,
    title="MCP K8s Assistant",
    type="messages",
    examples=[
        "list my pods",
        "How do I request A100 GPU?",
        "show deployments",
        "What is persistent storage?"
    ]
)

if __name__ == "__main__":
    print("Starting lightweight MCP chatbot with streaming...")
    print("Interface at: http://localhost:7861")

    demo.launch(
        server_name="127.0.0.1",
        server_port=7863,
        share=False
    )