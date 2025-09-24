#!/usr/bin/env python3
"""
Test Gradio Interface for MCP Infogent Architecture
===================================================
Tests the local MCP system with Gradio UI
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
            result = f"🎯 Intent: {intent}\n\n"

            if intent == "COMMAND":
                cmd_result = loop.run_until_complete(session.process_k8s_command(query))
                result += f"🔧 K8s Result:\n{cmd_result}"

            elif intent == "QUESTION":
                doc_result = loop.run_until_complete(session.ask_question(query))
                result += f"📚 Answer:\n{doc_result}"

            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error: {e}")
        return f"❌ Error: {str(e)}"

def test_fastmcp():
    try:
        import requests
        response = requests.get("http://localhost:8024/mcp", timeout=5)
        return f"✅ FastMCP Status: {response.status_code}"
    except Exception as e:
        return f"❌ FastMCP Error: {str(e)}"

def test_mcp_files():
    """Check if MCP files exist"""
    files_to_check = [
        "ultimate_fastmcp_server.py",
        "your_interactive_session.py",
        "interactive_demo.py"
    ]

    results = []
    for file_name in files_to_check:
        file_path = Path(__file__).parent / file_name
        if file_path.exists():
            results.append(f"✅ {file_name}")
        else:
            results.append(f"❌ {file_name}")

    return "\n".join(results)

# Create Gradio interface
with gr.Blocks(title="MCP Infogent Test") as demo:
    gr.HTML("<h1>🚀 MCP Infogent Architecture Test</h1>")
    gr.HTML("<p>Testing local MCP system with K8s operations and NRP knowledge</p>")

    with gr.Tabs():
        with gr.TabItem("🎯 Query Interface"):
            with gr.Row():
                with gr.Column():
                    query_input = gr.Textbox(
                        label="Query",
                        placeholder="list my pods\nHow do I request A100 GPU?\nshow deployments",
                        lines=3
                    )
                    submit_btn = gr.Button("Submit", variant="primary")

                with gr.Column():
                    gr.HTML("<h3>Example Queries:</h3>")
                    examples = [
                        "list my pods",
                        "How do I request A100 GPU?",
                        "show deployments",
                        "What is persistent storage?",
                        "describe pods"
                    ]

                    for example in examples:
                        example_btn = gr.Button(example, size="sm")
                        example_btn.click(lambda x=example: x, outputs=query_input)

            output = gr.Markdown(
                label="Response",
                value="Ready! Using MCP infogent architecture with K8s operations.",
                height=400
            )

        with gr.TabItem("🔧 System Status"):
            with gr.Row():
                with gr.Column():
                    gr.HTML("<h3>FastMCP Server</h3>")
                    fastmcp_status = gr.Markdown(label="FastMCP Status", height=100)
                    test_fastmcp_btn = gr.Button("Test FastMCP")

                with gr.Column():
                    gr.HTML("<h3>MCP Files</h3>")
                    files_status = gr.Markdown(label="MCP Files Status", height=100)
                    test_files_btn = gr.Button("Check Files")

            test_fastmcp_btn.click(test_fastmcp, outputs=fastmcp_status)
            test_files_btn.click(test_mcp_files, outputs=files_status)

        with gr.TabItem("📋 Architecture Info"):
            gr.HTML("""
            <h3>🏗️ MCP Infogent Architecture</h3>
            <ul>
                <li><strong>FastMCP Server:</strong> ultimate_fastmcp_server.py</li>
                <li><strong>Interactive Session:</strong> your_interactive_session.py</li>
                <li><strong>Intent Classification:</strong> GLM-4.5V powered</li>
                <li><strong>K8s Operations:</strong> Direct Kubernetes API calls</li>
                <li><strong>Knowledge Base:</strong> NRP Nautilus documentation</li>
                <li><strong>Transport:</strong> HTTP MCP protocol on port 8024</li>
            </ul>
            """)

    submit_btn.click(process_query, inputs=query_input, outputs=output)
    query_input.submit(process_query, inputs=query_input, outputs=output)

if __name__ == "__main__":
    print("🚀 Starting MCP Infogent Architecture Test with Gradio...")
    print("📁 Make sure ultimate_fastmcp_server.py is running on port 8024")
    print("🌐 Interface will be available at: http://localhost:7860")

    # Check FastMCP server
    try:
        import requests
        response = requests.get("http://localhost:8024/mcp", timeout=2)
        print(f"✅ FastMCP server detected: {response.status_code}")
    except:
        print("⚠️  FastMCP server not detected")
        print("   Start with: cd mcp && python ultimate_fastmcp_server.py")

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )