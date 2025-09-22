#!/usr/bin/env python3
"""
GLM-V Setup Demonstration
========================

Shows how the Intent Agent is configured to use GLM-V instead of gemma3
for better intent classification with tool calling capabilities.
"""

import os
import sys
sys.path.append('.')

# Import the orchestrator through the main module path
try:
    from nrp_k8s_system.agents.orchestrator import init_orchestrator
except ImportError:
    print("Run this from the parent directory: python nrp_k8s_system/demo_glm_setup.py")
    sys.exit(1)

def demo_glm_configuration():
    """Demonstrate GLM-V configuration and fallback behavior."""

    print("GLM-V Configuration Demo")
    print("=" * 50)

    # Check current environment (updated to use user's environment variables)
    glm_key = os.getenv("nrp_key_2")
    glm_url = os.getenv("nrp_base_url", "https://llm.nrp-nautilus.io/v1")
    glm_model = os.getenv("nrp_model2", "glm-4v-plus")

    print(f"Environment Status:")
    print(f"  nrp_key_2: {'[Set]' if glm_key else '[Not set]'}")
    print(f"  nrp_base_url: {glm_url}")
    print(f"  nrp_model2: {glm_model}")
    print()

    # Initialize orchestrator to show agent status
    print("Initializing Agent System...")
    try:
        orchestrator = init_orchestrator()
        status = orchestrator.get_system_status()

        intent_status = status['agents']['intent_router']
        print(f"Intent Router Status:")
        print(f"  Model Used: {intent_status.get('model_used', 'unknown')}")
        print(f"  GLM-V Available: {intent_status.get('glm_v_available', False)}")

        if intent_status.get('fallback_model'):
            print(f"  Fallback Model: {intent_status['fallback_model']}")

        print()

        if not intent_status.get('glm_v_available'):
            print("To Enable GLM-V:")
            print("   1. Set environment variables:")
            print("      export nrp_key_2=your_glm_api_key")
            print("      export nrp_base_url=https://llm.nrp-nautilus.io/v1")
            print("      export nrp_model2=glm-4v-plus")
            print()
            print("   2. Restart the system")
            print()
            print("   GLM-V provides:")
            print("   - Tool calling capabilities for command discovery")
            print("   - 65,536 token context window")
            print("   - Multimodal support (vision, video)")
            print("   - GPT-4o level performance")
            print("   - Better intent classification accuracy")
        else:
            print("[Success] GLM-V is active and ready for enhanced intent classification!")

    except Exception as e:
        print(f"[Error] Error initializing system: {e}")

if __name__ == "__main__":
    demo_glm_configuration()