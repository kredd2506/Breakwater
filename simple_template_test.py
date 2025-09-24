#!/usr/bin/env python3
"""
Simple test to verify the improved template selection logic.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.code_generator import CodeGeneratorAgent


def test_a100_selection():
    """Test A100 template selection."""
    print("Testing A100 template selection...")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create analysis for A100 request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "A100",
            "gpu": "nvidia.com/a100"
        },
        "features": [],
        "complexity": "moderate"
    }

    # Test the template finding logic
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates for A100 request")

    if templates:
        selected = templates[0]
        print(f"Selected template: {selected.name}")
        print(f"Template description: {selected.description}")

        # Check if it's A100-specific
        if "a100" in selected.name.lower():
            print("SUCCESS: A100-specific template selected")
            return True
        else:
            print("WARNING: Non-A100 template selected")
            return False
    else:
        print("No templates found")
        return False


def test_generic_gpu_selection():
    """Test generic GPU template selection."""
    print("\nTesting generic GPU template selection...")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create analysis for generic GPU request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "generic",
            "gpu": "nvidia.com/gpu"
        },
        "features": [],
        "complexity": "simple"
    }

    # Test the template finding logic
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates for generic GPU request")

    if templates:
        selected = templates[0]
        print(f"Selected template: {selected.name}")
        print(f"Template description: {selected.description}")

        # Check if it's NOT A100-specific
        if "a100" not in selected.name.lower():
            print("SUCCESS: Generic template selected (not A100)")
            return True
        else:
            print("WARNING: A100 template selected for generic request")
            return False
    else:
        print("No templates found")
        return False


def main():
    """Run the tests."""
    print("Template Selection Logic Test")
    print("=" * 40)

    test1_result = test_a100_selection()
    test2_result = test_generic_gpu_selection()

    print("\n" + "=" * 40)
    print("Results:")
    print(f"A100 test: {'PASS' if test1_result else 'FAIL'}")
    print(f"Generic test: {'PASS' if test2_result else 'FAIL'}")

    if test1_result and test2_result:
        print("\nAll tests passed! The improved logic is working.")
        print("Key improvements implemented:")
        print("- Hard eligibility gates for exact matches")
        print("- A100 templates only selected when A100 explicitly requested")
        print("- Generic templates excluded when exact matches exist")
    else:
        print("\nSome tests failed. Check the implementation.")


if __name__ == "__main__":
    main()