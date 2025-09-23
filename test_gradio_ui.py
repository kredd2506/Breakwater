#!/usr/bin/env python3
"""
Simple Gradio UI for testing NRP K8s System MCP functionality
"""
import gradio as gr
import subprocess
import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to Python path
sys.path.append(str(Path(__file__).parent / "nrp_k8s_system"))

def process_mcp_query(query):
    """Process a query through the MCP system"""
    if not query.strip():
        return "❌ Please enter a query!"

    try:
        # Try to run the intelligent router
        result = subprocess.run([
            sys.executable, "-m", "nrp_k8s_system.intelligent_router", query
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(Path(__file__).parent)
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if result.stderr:
                output += f"\n\n⚠️ Warnings:\n{result.stderr}"
            return f"✅ **Success!**\n\n```\n{output}\n```"
        else:
            error_msg = result.stderr or "Unknown error occurred"
            return f"❌ **Error (Exit code: {result.returncode})**\n\n```\n{error_msg}\n```"

    except subprocess.TimeoutExpired:
        return "⏰ **Timeout**: Query took too long (>30 seconds)"
    except FileNotFoundError:
        return "❌ **MCP System Not Found**: Make sure the nrp_k8s_system module is available"
    except Exception as e:
        return f"❌ **Unexpected Error**: {str(e)}"

def get_system_info():
    """Get basic system information"""
    try:
        import platform
        info = f"""
**System Information:**
- Python Version: {sys.version.split()[0]}
- Platform: {platform.system()} {platform.release()}
- Working Directory: {os.getcwd()}
- MCP System Path: {Path(__file__).parent / 'nrp_k8s_system'}
- Path Exists: {(Path(__file__).parent / 'nrp_k8s_system').exists()}
"""
        return info
    except Exception as e:
        return f"Error getting system info: {e}"

# Create the Gradio interface
with gr.Blocks(
    title="NRP K8s System - MCP Interface",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1200px !important;
        margin: auto;
    }
    """
) as demo:

    gr.HTML("""
    <div style="text-align: center; padding: 20px;">
        <h1>🚀 NRP K8s System - MCP Interface</h1>
        <p>Intelligent routing system combining NRP LLM with Kubernetes operations</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            # Input section
            query_input = gr.Textbox(
                label="Enter your command or query",
                placeholder="Examples:\n• List my pods\n• How do I request GPUs?\n• Show me my deployments\n• What is a persistent volume?",
                lines=3,
                max_lines=5
            )

            with gr.Row():
                submit_btn = gr.Button("🔍 Submit Query", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Clear", size="lg")

        with gr.Column(scale=1):
            # Quick examples
            gr.HTML("<h3>Quick Examples:</h3>")

            example_btns = []
            examples = [
                "list my pods",
                "How do I request GPUs?",
                "show deployments in gsoc namespace",
                "What is a service mesh?",
                "describe pod status",
                "How do I create a persistent volume?"
            ]

            for example in examples:
                btn = gr.Button(f"💡 {example}", size="sm")
                btn.click(lambda x=example: x, outputs=query_input)
                example_btns.append(btn)

    # Output section
    output_display = gr.Markdown(
        label="Output",
        value="**Ready!** Enter a query above to test the MCP system.",
        height=400
    )

    # System info section (collapsible)
    with gr.Accordion("System Information", open=False):
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
    print("🚀 Starting NRP K8s System MCP Interface...")
    print("📍 Make sure your MCP system is set up in the nrp_k8s_system directory")

    # Launch with public sharing for testing
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True if you want public URL
        show_error=True,
        debug=True
    )