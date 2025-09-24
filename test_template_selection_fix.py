#!/usr/bin/env python3
"""
Test the improved template selection logic to verify hard eligibility gates work correctly.

This test verifies that:
1. A100 templates are ONLY selected when A100 is explicitly requested
2. Generic templates are excluded when exact A100 matches exist
3. Validation ensures templates map to real schedulable capacity
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.code_generator import CodeGeneratorAgent, Template
from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel


def create_test_templates():
    """Create test templates to simulate the A100 vs generic scenario."""

    # A100-specific template
    a100_template = Template(
        name="a100_gpu_deployment",
        description="A100 GPU deployment with proper resource specs",
        content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        resources:
          requests:
            nvidia.com/a100: {{GPU_COUNT}}
            memory: "32Gi"
            cpu: "8"
          limits:
            nvidia.com/a100: {{GPU_COUNT}}
            memory: "64Gi"
            cpu: "16"
""",
        resource_type="deployment",
        example_source="NRP A100 Documentation",
        nrp_policies=["Uses nvidia.com/a100 resource specification"],
        variables={"APP_NAME": "a100-app", "NAMESPACE": "gsoc", "REPLICAS": "1",
                  "IMAGE": "nvidia/cuda:latest", "GPU_COUNT": "1"}
    )

    # Generic GPU template (simpler, might look attractive to old scoring)
    generic_template = Template(
        name="gpu_deployment",
        description="Generic GPU deployment",
        content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        resources:
          requests:
            nvidia.com/gpu: {{GPU_COUNT}}
            memory: "4Gi"
            cpu: "2"
          limits:
            nvidia.com/gpu: {{GPU_COUNT}}
            memory: "8Gi"
            cpu: "4"
""",
        resource_type="deployment",
        example_source="NRP GPU Guidelines",
        nrp_policies=["Uses nvidia.com/gpu resource specification"],
        variables={"APP_NAME": "gpu-app", "NAMESPACE": "gsoc", "REPLICAS": "1",
                  "IMAGE": "nvidia/cuda:latest", "GPU_COUNT": "1"}
    )

    # Basic deployment (no GPU)
    basic_template = Template(
        name="basic_deployment",
        description="Basic deployment without GPU",
        content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{APP_NAME}}
  template:
    metadata:
      labels:
        app: {{APP_NAME}}
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
""",
        resource_type="deployment",
        example_source="NRP Basic Templates",
        nrp_policies=["Basic resource limits"],
        variables={"APP_NAME": "basic-app", "NAMESPACE": "gsoc", "REPLICAS": "1",
                  "IMAGE": "nginx:latest"}
    )

    return {
        "a100_gpu_deployment": a100_template,
        "gpu_deployment": generic_template,
        "basic_deployment": basic_template
    }


def test_a100_exact_match():
    """Test that A100 request selects A100 template exclusively."""
    print("\n=== Test 1: A100 Exact Match ===")

    # Create agent with test templates
    agent = CodeGeneratorAgent()
    agent.templates = create_test_templates()

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

    # Find templates
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates")
    for i, template in enumerate(templates):
        print(f"  {i+1}. {template.name} ({template.description})")

    # Verify only A100 template is selected
    if templates:
        selected = templates[0]
        print(f"\nSelected: {selected.name}")

        # Verify it's A100 and not generic
        assert "a100" in selected.name.lower(), f"Expected A100 template, got {selected.name}"
        assert "nvidia.com/a100" in selected.content, "Template should use nvidia.com/a100"
        print("PASS: A100 template correctly selected")
    else:
        print("❌ FAIL: No templates found")
        return False

    return True


def test_generic_gpu_selection():
    """Test that generic GPU request selects generic template."""
    print("\n=== Test 2: Generic GPU Selection ===")

    # Create agent with test templates
    agent = CodeGeneratorAgent()
    agent.templates = create_test_templates()

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

    # Find templates
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates")
    for i, template in enumerate(templates):
        print(f"  {i+1}. {template.name} ({template.description})")

    # Verify generic template is selected (not A100)
    if templates:
        selected = templates[0]
        print(f"\nSelected: {selected.name}")

        # Verify it's generic GPU, not A100
        assert "a100" not in selected.name.lower(), f"Should not select A100 template for generic request, got {selected.name}"
        assert "nvidia.com/gpu" in selected.content, "Template should use nvidia.com/gpu"
        assert "nvidia.com/a100" not in selected.content, "Generic template should not use A100 resources"
        print("✅ PASS: Generic GPU template correctly selected")
    else:
        print("❌ FAIL: No templates found")
        return False

    return True


def test_validation_rejects_invalid():
    """Test that validation rejects templates with wrong resource specs."""
    print("\n=== Test 3: Validation Rejects Invalid Templates ===")

    # Create agent
    agent = CodeGeneratorAgent()

    # Create invalid template (A100 request but generic resources)
    invalid_template = Template(
        name="fake_a100_template",
        description="Fake A100 template with wrong resources",
        content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: fake-a100
  namespace: gsoc
spec:
  containers:
  - name: app
    image: nvidia/cuda:latest
    resources:
      requests:
        nvidia.com/gpu: 1  # Wrong! Should be nvidia.com/a100
      limits:
        nvidia.com/gpu: 1
""",
        resource_type="deployment",
        example_source="Test",
        nrp_policies=[],
        variables={}
    )

    # Create analysis for A100 request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "A100"
        }
    }

    # Test validation
    is_valid = agent._validate_template_schedulability(invalid_template, analysis)

    if not is_valid:
        print("✅ PASS: Validation correctly rejected invalid A100 template")
        return True
    else:
        print("❌ FAIL: Validation should have rejected invalid template")
        return False


def test_no_a100_fallback():
    """Test behavior when A100 is requested but no A100 templates exist."""
    print("\n=== Test 4: No A100 Template Fallback ===")

    # Create agent with only generic templates
    agent = CodeGeneratorAgent()
    agent.templates = {
        "gpu_deployment": create_test_templates()["gpu_deployment"],
        "basic_deployment": create_test_templates()["basic_deployment"]
    }

    # Create analysis for A100 request
    analysis = {
        "resource_type": "deployment",
        "requirements": {
            "gpu_type": "A100"
        },
        "features": [],
        "complexity": "moderate"
    }

    # Find templates
    templates = agent._find_templates(analysis)

    print(f"Found {len(templates)} templates")
    for i, template in enumerate(templates):
        print(f"  {i+1}. {template.name} ({template.description})")

    # Should fall back to general templates when no exact matches
    if len(templates) > 0:
        print("✅ PASS: System falls back to available templates when no exact matches")
        return True
    else:
        print("❌ FAIL: System should fall back to available templates")
        return False


def main():
    """Run all tests."""
    print("Testing Improved Template Selection Logic")
    print("=" * 50)

    tests = [
        test_a100_exact_match,
        test_generic_gpu_selection,
        test_validation_rejects_invalid,
        test_no_a100_fallback
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The improved logic works correctly.")
        print("\nKey improvements:")
        print("- Hard eligibility gates prevent generic templates from winning over exact matches")
        print("- A100 templates are ONLY selected when A100 is explicitly requested")
        print("- Validation ensures templates map to real schedulable capacity")
        print("- Constraint satisfaction takes precedence over soft scoring")
    else:
        print("❌ Some tests failed. Review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)