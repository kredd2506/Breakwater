#!/usr/bin/env python3
"""
Simple Gradio Test for MCP Infogent Architecture
"""

import gradio as gr
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_query(query):
    if not query.strip():
        return "Please enter a query!"

    logger.info(f"Processing query: {query}")

    try:
        # Import the working interactive session
        from your_interactive_session import InteractiveNRPSession

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            session = InteractiveNRPSession()
            intent = loop.run_until_complete(session.classify_intent(query))
            result = f"Intent: {intent}\n\n"

            if intent == "COMMAND":
                cmd_result = loop.run_until_complete(session.process_k8s_command(query))
                result += f"K8s Result:\n{cmd_result}"

            elif intent == "QUESTION":
                doc_result = loop.run_until_complete(session.ask_question(query))
                result += f"Answer:\n{doc_result}"

            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {str(e)}"

def test_fastmcp():
    try:
        import requests
        response = requests.get("http://localhost:8024/mcp", timeout=5)
        return f"FastMCP Status: {response.status_code}"
    except Exception as e:
        return f"FastMCP Error: {str(e)}"

# Create simple Gradio interface
with gr.Blocks(title="MCP Test") as demo:
    gr.HTML("<h1>MCP Infogent Architecture Test</h1>")

    with gr.Row():
        with gr.Column():
            query_input = gr.Textbox(
                label="Query",
                placeholder="list my pods\nHow do I request A100 GPU?",
                lines=3
            )
            submit_btn = gr.Button("Submit", variant="primary")

        with gr.Column():
            fastmcp_status = gr.Markdown(label="FastMCP Status")
            test_btn = gr.Button("Test FastMCP")

    output = gr.Markdown(label="Response", height=300)

    submit_btn.click(process_query, inputs=query_input, outputs=output)
    test_btn.click(test_fastmcp, outputs=fastmcp_status)

if __name__ == "__main__":
    print("Starting MCP Infogent Test...")
    print("Interface at: http://localhost:7860")

    # Check FastMCP server
    try:
        import requests
        response = requests.get("http://localhost:8024/mcp", timeout=2)
        print(f"FastMCP server detected: {response.status_code}")
    except:
        print("FastMCP server not detected")

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )