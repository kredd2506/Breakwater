#!/usr/bin/env python3
"""Test NRP.ai Prompts FastMCP Server"""

import asyncio
import json
from fastmcp import Client

async def test_nrp_prompts():
    client = Client("http://localhost:8009/mcp")

    async with client:
        print("Testing NRP.ai Prompts FastMCP Server")
        print("=" * 70)

        # Test 1: List available prompts
        print("\n1. Available Prompts:")
        try:
            prompts = await client.list_prompts()
            print(f"  Found {len(prompts)} prompts:")
            for prompt in prompts:
                print(f"    - {prompt.name}: {prompt.description}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: GPU Request Prompt
        print("\n" + "=" * 70)
        print("2. GPU Request Prompt (A100):")
        try:
            result = await client.get_prompt("nrp-gpu-request", {
                "gpu_type": "a100",
                "gpu_count": 1,
                "memory_gb": 32,
                "cpu_cores": 8,
                "namespace": "gsoc"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"      {content_text[:200]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: A100 Specific Prompt
        print("\n" + "=" * 70)
        print("3. A100 Specific Prompt:")
        try:
            result = await client.get_prompt("nrp-a100-specific", {
                "workload_type": "ml_training",
                "memory_gb": 64,
                "cpu_cores": 16,
                "namespace": "research"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"      Length: {len(content_text)} characters")
                if "A100" in content_text:
                    print(f"      Contains A100 instructions: [OK]")
                if "reservation" in content_text.lower():
                    print(f"      Contains reservation info: [OK]")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Storage Configuration Prompt
        print("\n" + "=" * 70)
        print("4. Storage Configuration Prompt:")
        try:
            result = await client.get_prompt("nrp-storage-config", {
                "storage_type": "ceph_fs",
                "size": "100Gi",
                "access_mode": "ReadWriteMany",
                "namespace": "shared-data"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"      Storage Type: {'CephFS' if 'ceph' in content_text.lower() else 'Other'}")
                if "ReadWriteMany" in content_text:
                    print(f"      Multi-pod access: [OK]")
                print(f"      Preview: {content_text[:150]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 5: FPGA Deployment Prompt
        print("\n" + "=" * 70)
        print("5. FPGA Deployment Prompt:")
        try:
            result = await client.get_prompt("nrp-fpga-deployment", {
                "fpga_type": "esnet_smartnic",
                "application": "network_processing",
                "namespace": "fpga-dev"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                if "esnet" in content_text.lower():
                    print(f"      ESnet SmartNIC config: [OK]")
                if "privileged" in content_text.lower():
                    print(f"      Security considerations: [OK]")
                print(f"      Preview: {content_text[:150]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 6: Troubleshooting Prompt
        print("\n" + "=" * 70)
        print("6. Troubleshooting Prompt:")
        try:
            result = await client.get_prompt("nrp-troubleshooting", {
                "issue_type": "gpu_not_detected",
                "resource_type": "gpu",
                "namespace": "ml-experiments"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                if "kubectl" in content_text.lower():
                    print(f"      Contains kubectl commands: [OK]")
                if "diagnostic" in content_text.lower():
                    print(f"      Diagnostic procedures: [OK]")
                print(f"      Preview: {content_text[:150]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 7: Best Practices Prompt
        print("\n" + "=" * 70)
        print("7. Best Practices Prompt:")
        try:
            result = await client.get_prompt("nrp-best-practices", {
                "category": "gpu",
                "use_case": "deep_learning"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                print(f"    Message {i} ({message.role}):")
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                if "best practices" in content_text.lower():
                    print(f"      Best practices content: [OK]")
                if "optimization" in content_text.lower():
                    print(f"      Optimization tips: [OK]")
                print(f"      Content length: {len(content_text)} characters")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 8: Parameter Validation
        print("\n" + "=" * 70)
        print("8. Parameter Validation Test:")
        try:
            # Test with different GPU types
            gpu_types = ["general", "a100", "a40", "rtx6000"]
            for gpu_type in gpu_types:
                result = await client.get_prompt("nrp-gpu-request", {
                    "gpu_type": gpu_type,
                    "gpu_count": 2,
                    "memory_gb": 16,
                    "cpu_cores": 4
                })

                # Check if the correct GPU resource is used
                if len(result.messages) > 1:
                    content_obj = result.messages[1].content
                    content = content_obj.text if hasattr(content_obj, 'text') else str(content_obj)
                else:
                    content = ""
                if f"nvidia.com/{gpu_type}" in content or "nvidia.com/gpu" in content:
                    print(f"    GPU Type '{gpu_type}': [OK] Correct resource identifier")
                else:
                    print(f"    GPU Type '{gpu_type}': ? Resource identifier check")

        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)
        print("NRP.ai Prompts Testing Complete!")

async def demo_prompt_workflow():
    """Demonstrate a complete workflow using prompts"""

    print("\n" + "=" * 70)
    print("PROMPT WORKFLOW DEMONSTRATION")
    print("=" * 70)

    client = Client("http://localhost:8009/mcp")

    async with client:
        # Scenario: User wants to deploy ML training on A100
        print("\nScenario: ML Training on A100 GPU")
        print("-" * 40)

        # Step 1: Get A100 specific configuration
        print("1. Getting A100 configuration...")
        a100_result = await client.get_prompt("nrp-a100-specific", {
            "workload_type": "ml_training",
            "memory_gb": 80,
            "cpu_cores": 16,
            "namespace": "ml-research"
        })

        print(f"   Generated comprehensive A100 setup with {len(a100_result.messages)} messages")

        # Step 2: Get storage configuration for datasets
        print("2. Setting up storage for datasets...")
        storage_result = await client.get_prompt("nrp-storage-config", {
            "storage_type": "ceph_fs",
            "size": "1Ti",
            "access_mode": "ReadWriteMany",
            "namespace": "ml-research"
        })

        print(f"   Generated CephFS storage config with {len(storage_result.messages)} messages")

        # Step 3: Get troubleshooting guidance
        print("3. Getting troubleshooting guidance...")
        troubleshoot_result = await client.get_prompt("nrp-troubleshooting", {
            "issue_type": "pod_pending",
            "resource_type": "gpu",
            "namespace": "ml-research"
        })

        print(f"   Generated troubleshooting guide with {len(troubleshoot_result.messages)} messages")

        # Step 4: Get best practices
        print("4. Getting ML best practices...")
        practices_result = await client.get_prompt("nrp-best-practices", {
            "category": "gpu",
            "use_case": "research"
        })

        print(f"   Generated best practices guide with {len(practices_result.messages)} messages")

        print("\nWorkflow Complete: User now has:")
        print("  [OK] A100 GPU configuration with reservation notes")
        print("  [OK] Shared storage setup for datasets")
        print("  [OK] Troubleshooting procedures")
        print("  [OK] Best practices for ML workloads")

if __name__ == "__main__":
    asyncio.run(test_nrp_prompts())
    asyncio.run(demo_prompt_workflow())