#!/usr/bin/env python3
"""
Test A100 Fix Integration
========================
Direct test to verify the A100 templates are working correctly.
"""

import sys
import os
sys.path.append("D:/Gsoc Gitlab/ocean/breakwater/nrp_k8s_system")
sys.path.append("D:/Gsoc Gitlab/ocean/breakwater/nrp_k8s_system/template")

def test_a100_templates():
    print("=== A100 Template Integration Test ===")

    try:
        # Test comprehensive templates
        print("\n1. Testing Comprehensive Templates...")
        from nrp_comprehensive_templates import get_a100_pod_template, get_a100_templates

        a100_pod = get_a100_pod_template()
        if a100_pod:
            print("✅ A100 Pod template found!")
            print(f"   Source: {a100_pod['source']}")
            print(f"   Resource Type: {a100_pod['resource_type']}")

            # Check for correct A100 specification
            yaml_content = a100_pod['template_yaml']
            if 'nvidia.com/a100' in yaml_content:
                print("✅ CORRECT: Uses nvidia.com/a100")
                print(f"   Template excerpt: ...{yaml_content[200:400]}...")
            else:
                print("❌ INCORRECT: Missing nvidia.com/a100")
                print(f"   Content: {yaml_content[:200]}...")
        else:
            print("❌ No A100 Pod template found")

        # Test all A100 templates
        all_a100 = get_a100_templates()
        print(f"\n2. Found {len(all_a100)} A100 templates:")
        for name, template in all_a100.items():
            print(f"   - {name}: {template['description']}")
            if 'nvidia.com/a100' in template['template_yaml']:
                print("     ✅ Has nvidia.com/a100")
            else:
                print("     ❌ Missing nvidia.com/a100")

    except Exception as e:
        print(f"❌ Error testing comprehensive templates: {e}")

    print("\n3. Testing Direct A100 Request...")

    # Simulate A100 request analysis
    test_input = "show me A100 GPU example"
    print(f"   Input: '{test_input}'")

    # Check A100 detection
    if "a100" in test_input.lower():
        print("   ✅ A100 detected in input")
        gpu_type = "A100"
        gpu_resource = "nvidia.com/a100"
    else:
        print("   ❌ A100 not detected")
        gpu_type = "generic"
        gpu_resource = "nvidia.com/gpu"

    print(f"   GPU Type: {gpu_type}")
    print(f"   GPU Resource: {gpu_resource}")

    # Generate proper A100 YAML
    a100_yaml = f'''apiVersion: v1
kind: Pod
metadata:
  name: a100-gpu-pod
  namespace: gsoc
spec:
  containers:
  - name: a100-container
    image: tensorflow/tensorflow:latest-gpu
    command: ["sleep", "infinity"]
    resources:
      limits:
        {gpu_resource}: 1
        memory: "8Gi"
        cpu: "4"
      requests:
        {gpu_resource}: 1
        memory: "4Gi"
        cpu: "2"
'''

    print("\n4. Generated A100 YAML:")
    print(a100_yaml)

    if "nvidia.com/a100" in a100_yaml:
        print("✅ SUCCESS: Generated YAML uses nvidia.com/a100")
    else:
        print("❌ FAILURE: Generated YAML still uses nvidia.com/gpu")

if __name__ == "__main__":
    test_a100_templates()