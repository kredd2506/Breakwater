#!/usr/bin/env python3
"""
Local Test Gradio UI for MCP System
Simulates what will happen in the deployment
"""
import gradio as gr
import asyncio
import sys
import os
from pathlib import Path

# Add the MCP system to Python path
mcp_path = Path(__file__).parent / "mcp"
sys.path.append(str(mcp_path))

# Import the FIXED MCP interactive session
try:
    from fixed_interactive_session import FixedInteractiveNRPSession
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import fixed MCP system: {e}")
    MCP_AVAILABLE = False

def process_mcp_query(query):
    """Process a query through the local MCP system"""
    if not query.strip():
        return "❌ Please enter a query!"

    if not MCP_AVAILABLE:
        return "❌ **MCP System Not Available**: Could not import InteractiveNRPSession"

    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            session = FixedInteractiveNRPSession()

            # Step 1: Classify intent
            intent = loop.run_until_complete(session.classify_intent(query))

            result = f"**Intent Classification**: {intent}\n\n"

            # Step 2: Process based on intent
            if intent == "COMMAND":
                # Handle K8s command
                k8s_result = loop.run_until_complete(session.process_k8s_command(query))
                result += f"**K8s Command Result**:\n```\n{k8s_result}\n```"

            elif intent == "QUESTION":
                # Handle documentation question
                doc_result = loop.run_until_complete(session.ask_question(query))
                result += f"**Documentation Response**:\n{doc_result}"

            elif intent == "QUIT":
                result += "**System Response**: Session would exit in interactive mode"

            else:
                result += f"**Unknown Intent**: {intent}\nUnable to process this query type."

            return f"✅ **Success!**\n\n{result}"

        finally:
            loop.close()

    except Exception as e:
        return f"❌ **Error**: {str(e)}\n\nThis simulates what might happen in the deployment if there are environment or dependency issues."

def get_system_info():
    """Get MCP system information"""
    try:
        info = f"""
**MCP System Information:**
- MCP Path: {mcp_path}
- MCP Available: {MCP_AVAILABLE}
- Working Directory: {os.getcwd()}
- Python Version: {sys.version.split()[0]}
"""

        if MCP_AVAILABLE:
            try:
                # Try to create a session to check dependencies
                session = FixedInteractiveNRPSession()
                info += "- FixedInteractiveNRPSession: ✅ Initialized successfully\n"
                info += "- GLM Client: ✅ Available\n"
                info += "- FastMCP Client: ✅ Available\n"
            except Exception as e:
                info += f"- Session Init Error: ❌ {str(e)}\n"

        return info
    except Exception as e:
        return f"Error getting system info: {e}"

# Create the Gradio interface
with gr.Blocks(
    title="Local MCP System Test - Gradio UI",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1400px !important;
        margin: auto;
    }
    """
) as demo:

    gr.HTML("""
    <div style="text-align: center; padding: 20px;">
        <h1>🚀 Local MCP System Test - Gradio UI</h1>
        <p>Testing the NRP K8s Interactive Session locally to simulate deployment behavior</p>
        <p><strong>This simulates what will run at bw.nrp-nautilus.io</strong></p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            # Input section
            query_input = gr.Textbox(
                label="Enter your command or query",
                placeholder="Examples:\n• List my pods\n• How do I request GPUs?\n• Show me my deployments\n• What is a persistent volume?\n• quit",
                lines=4,
                max_lines=6
            )

            with gr.Row():
                submit_btn = gr.Button("🔍 Submit Query", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Clear", size="lg")

        with gr.Column(scale=1):
            # Quick examples
            gr.HTML("<h3>🔥 Quick Examples:</h3>")

            example_btns = []
            examples = [
                ("list my pods", "🔍 List my pods"),
                ("How do I request GPUs?", "💡 How do I request GPUs?"),
                ("show deployments in gsoc namespace", "📦 Show deployments"),
                ("What is a service mesh?", "❓ What is a service mesh?"),
                ("describe pod status", "🔧 Describe pod status"),
                ("quit", "🚪 Test quit intent")
            ]

            for query, label in examples:
                btn = gr.Button(label, size="sm")
                btn.click(lambda x=query: x, outputs=query_input)

    # Output section
    output_display = gr.Markdown(
        label="MCP System Output",
        value="**Ready!** Enter a query above to test the local MCP system.\n\n*This simulates the exact behavior that will occur in the deployment.*",
        height=500
    )

    # System info section (collapsible)
    with gr.Accordion("🔧 System Information & Debug", open=False):
        system_info = gr.Markdown(value=get_system_info())
        refresh_info_btn = gr.Button("🔄 Refresh System Info", size="sm")
        refresh_info_btn.click(get_system_info, outputs=system_info)

    # Event handlers
    submit_btn.click(
        process_mcp_query,
        inputs=query_input,
        outputs=output_display
    )

    clear_btn.click(
        lambda: ("", "**Cleared!** Enter a new query to test the MCP system."),
        outputs=[query_input, output_display]
    )

    # Allow Enter key to submit
    query_input.submit(
        process_mcp_query,
        inputs=query_input,
        outputs=output_display
    )

if __name__ == "__main__":
    print("Starting Local MCP System Test with Gradio...")
    print(f"MCP Path: {mcp_path}")
    print(f"MCP Available: {MCP_AVAILABLE}")

    if not MCP_AVAILABLE:
        print("Warning: MCP system not available - UI will show error messages")

    print("\nThis simulates the exact behavior of the deployment at bw.nrp-nautilus.io")

    # Launch the interface
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,  # Different port to avoid conflicts
        share=False,
        show_error=True,
        debug=True
    )