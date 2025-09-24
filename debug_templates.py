#!/usr/bin/env python3
"""
Debug script to see what templates are loaded.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.code_generator import CodeGeneratorAgent


def main():
    print("Debug: Template Loading")
    print("=" * 30)

    # Create agent
    agent = CodeGeneratorAgent()

    print(f"\nTotal templates loaded: {len(agent.templates)}")
    print("\nAll templates:")
    for name, template in agent.templates.items():
        print(f"  - {name}: {template.description}")
        print(f"    Resource type: {template.resource_type}")
        print(f"    Content contains 'nvidia.com/a100': {'nvidia.com/a100' in template.content}")
        print(f"    Content contains 'nvidia.com/gpu': {'nvidia.com/gpu' in template.content}")
        print()

    # Test A100 analysis
    print("=" * 30)
    print("Testing A100 analysis...")

    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "A100",
            "gpu": "nvidia.com/a100"
        },
        "features": [],
        "complexity": "moderate"
    }

    print("Looking for A100 templates...")
    for name, template in agent.templates.items():
        print(f"Checking {name}:")
        print(f"  - Resource type matches: {template.resource_type == analysis['resource_type']}")
        print(f"  - Has 'a100' in name: {'a100' in template.name.lower()}")
        print(f"  - Has 'nvidia.com/a100' in content: {'nvidia.com/a100' in template.content}")

        gpu_type = analysis['requirements'].get('gpu_type')
        if gpu_type == "A100":
            if ("a100" in template.name.lower() or "nvidia.com/a100" in template.content):
                if template.resource_type == analysis['resource_type']:
                    print(f"  *** THIS SHOULD BE SELECTED: {name} ***")
        print()


if __name__ == "__main__":
    main()