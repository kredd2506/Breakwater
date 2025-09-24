#!/usr/bin/env python3
"""
Local Gradio test for NRP K8s MCP system
Tests the interface before deployment
"""

import gradio as gr
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add MCP path
mcp_path = Path(__file__).parent / "mcp"
sys.path.insert(0, str(mcp_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_query(query):
    if not query.strip():
        return "Please enter a query!"

    logger.info(f"Processing query: {query}")

    try:
        # Import from local MCP directory
        from fixed_interactive_session import FixedInteractiveNRPSession

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            session = FixedInteractiveNRPSession()
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

def test_local_files():
    """Test if local files exist"""
    mcp_files = [
        "mcp/ultimate_fastmcp_server.py",
        "mcp/fixed_interactive_session.py"
    ]

    results = []
    for file_path in mcp_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            results.append(f"✅ {file_path} - Found")
        else:
            results.append(f"❌ {file_path} - Missing")

    return "\n".join(results)

# Create Gradio interface
with gr.Blocks(title="Local NRP K8s MCP Test") as demo:
    gr.HTML("<h1>🧪 Local NRP K8s MCP Test</h1>")
    gr.HTML("<p>Testing the interface locally before deployment</p>")

    with gr.Tabs():
        with gr.TabItem("🎯 Query Interface"):
            query_input = gr.Textbox(
                label="Query",
                placeholder="list my pods\nHow do I request A100 GPU?",
                lines=3
            )
            submit_btn = gr.Button("Submit", variant="primary")
            output = gr.Markdown(label="Response", height=350)

        with gr.TabItem("🔧 System Status"):
            with gr.Row():
                with gr.Column():
                    gr.HTML("<h3>FastMCP Server Test</h3>")
                    fastmcp_status = gr.Markdown(label="FastMCP Status", height=100)
                    test_fastmcp_btn = gr.Button("Test FastMCP Connection")

                with gr.Column():
                    gr.HTML("<h3>Local Files Check</h3>")
                    files_status = gr.Markdown(label="Local Files Status", height=100)
                    test_files_btn = gr.Button("Check Local Files")

            test_fastmcp_btn.click(test_fastmcp, outputs=fastmcp_status)
            test_files_btn.click(test_local_files, outputs=files_status)

        with gr.TabItem("📋 Example Queries"):
            gr.HTML("<h3>Try these example queries:</h3>")
            examples = [
                "list my pods",
                "How do I request A100 GPU?",
                "show deployments",
                "What is persistent storage?",
                "get cluster info"
            ]

            for example in examples:
                example_btn = gr.Button(example, size="sm")
                example_btn.click(lambda x=example: x, outputs=query_input)

    submit_btn.click(process_query, inputs=query_input, outputs=output)
    query_input.submit(process_query, inputs=query_input, outputs=output)

if __name__ == "__main__":
    print("🚀 Starting LOCAL NRP K8s MCP Test Interface...")
    print("📁 Make sure FastMCP server is running on port 8024")
    print("🌐 Interface will be available at: http://localhost:7860")

    # Check if FastMCP server is running
    try:
        import requests
        response = requests.get("http://localhost:8024/mcp", timeout=2)
        print(f"✅ FastMCP server detected: {response.status_code}")
    except:
        print("⚠️  FastMCP server not detected - start it first with:")
        print("   cd mcp && python ultimate_fastmcp_server.py")

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )