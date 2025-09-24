#!/usr/bin/env python3
"""
Comprehensive test for all NRP GPU types to verify hard eligibility gates.

Tests all GPU types from https://nrp.ai/documentation/userdocs/running/gpu-pods/#requesting-special-gpus:
- A40 (nvidia.com/a40)
- A100 (nvidia.com/a100)
- Nvidia RTX A6000 (nvidia.com/rtxa6000)
- Quadro RTX 8000 (nvidia.com/rtx8000)
- Grace Hopper GH200 (nvidia.com/gh200)
- A100 MIG 1g.10gb (nvidia.com/mig-small)
- Generic GPU (nvidia.com/gpu)
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.code_generator import CodeGeneratorAgent


def test_gpu_type_selection(gpu_type: str, expected_resource: str):
    """Test that a specific GPU type selects the correct template."""
    print(f"\n=== Testing {gpu_type} ({expected_resource}) ===")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create analysis for specific GPU request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": gpu_type,
            "gpu": expected_resource
        },
        "features": [],
        "complexity": "moderate"
    }

    # Find templates
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates")

    if templates:
        selected = templates[0]
        print(f"Selected: {selected.name}")
        print(f"Description: {selected.description}")

        # Verify the template uses the correct resource
        if expected_resource in selected.content:
            print(f"SUCCESS: Template uses correct resource {expected_resource}")

            # Check that it doesn't use other GPU resources
            other_resources = [
                "nvidia.com/a40", "nvidia.com/a100", "nvidia.com/rtxa6000",
                "nvidia.com/rtx8000", "nvidia.com/gh200", "nvidia.com/mig-small",
                "nvidia.com/gpu"
            ]
            other_resources = [r for r in other_resources if r != expected_resource]

            conflicting = [r for r in other_resources if r in selected.content]
            if conflicting:
                print(f"WARNING: Template also contains {conflicting}")
                return False
            else:
                print("SUCCESS: No conflicting GPU resources found")
                return True
        else:
            print(f"FAIL: Template doesn't use {expected_resource}")
            return False
    else:
        print("FAIL: No templates found")
        return False


def test_generic_exclusion():
    """Test that generic GPU request excludes specific GPU templates."""
    print(f"\n=== Testing Generic GPU Exclusion ===")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create analysis for generic GPU request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "GENERIC",
            "gpu": "nvidia.com/gpu"
        },
        "features": [],
        "complexity": "simple"
    }

    # Find templates
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates")

    if templates:
        selected = templates[0]
        print(f"Selected: {selected.name}")

        # Should use nvidia.com/gpu and not have any specific resources
        if "nvidia.com/gpu" in selected.content:
            specific_resources = [
                "nvidia.com/a40", "nvidia.com/a100", "nvidia.com/rtxa6000",
                "nvidia.com/rtx8000", "nvidia.com/gh200", "nvidia.com/mig-small"
            ]

            conflicting = [r for r in specific_resources if r in selected.content]
            if conflicting:
                print(f"FAIL: Generic template contains specific resources: {conflicting}")
                return False
            else:
                print("SUCCESS: Generic template excludes specific GPU resources")
                return True
        else:
            print("FAIL: Generic template doesn't use nvidia.com/gpu")
            return False
    else:
        print("FAIL: No generic templates found")
        return False


def test_template_validation():
    """Test that validation correctly accepts/rejects templates."""
    print(f"\n=== Testing Template Validation ===")

    agent = CodeGeneratorAgent()

    # Test A100 validation
    analysis_a100 = {
        "resource_type": "deployment",
        "requirements": {"gpu_type": "A100"}
    }

    # Find A100 template
    templates = agent._find_templates(analysis_a100)
    if templates:
        template = templates[0]
        is_valid = agent._validate_template_schedulability(template, analysis_a100)
        print(f"A100 template validation: {'PASS' if is_valid else 'FAIL'}")
        return is_valid
    else:
        print("FAIL: No A100 template found for validation")
        return False


def main():
    """Run comprehensive tests for all GPU types."""
    print("Comprehensive NRP GPU Types Test")
    print("=" * 50)
    print("Testing hard eligibility gates for all supported GPU types")

    # GPU type mapping from NRP documentation
    gpu_tests = [
        ("A40", "nvidia.com/a40"),
        ("A100", "nvidia.com/a100"),
        ("RTX_A6000", "nvidia.com/rtxa6000"),
        ("RTX_8000", "nvidia.com/rtx8000"),
        ("GH200", "nvidia.com/gh200"),
        ("MIG", "nvidia.com/mig-small")
    ]

    results = []

    # Test each specific GPU type
    for gpu_type, resource_spec in gpu_tests:
        try:
            result = test_gpu_type_selection(gpu_type, resource_spec)
            results.append((f"{gpu_type} Selection", result))
        except Exception as e:
            print(f"ERROR testing {gpu_type}: {e}")
            results.append((f"{gpu_type} Selection", False))

    # Test generic GPU exclusion
    try:
        result = test_generic_exclusion()
        results.append(("Generic GPU Exclusion", result))
    except Exception as e:
        print(f"ERROR testing generic exclusion: {e}")
        results.append(("Generic GPU Exclusion", False))

    # Test validation
    try:
        result = test_template_validation()
        results.append(("Template Validation", result))
    except Exception as e:
        print(f"ERROR testing validation: {e}")
        results.append(("Template Validation", False))

    # Summary
    print(f"\n{'=' * 50}")
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25}: {status}")
        if result:
            passed += 1

    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS: All GPU types work with hard eligibility gates!")
        print("\nKey improvements verified:")
        print("- Hard eligibility gates prevent wrong GPU resource selection")
        print("- Each GPU type maps to correct nvidia.com/* resource")
        print("- Generic GPU excludes all specific GPU resources")
        print("- Template validation ensures correct resource specifications")
        print("- Exactness is now a hard constraint, not soft preference")
    else:
        print(f"\nSome tests failed. {total-passed} issues need to be resolved.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)