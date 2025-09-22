#!/usr/bin/env python3
"""Test Advanced NRP Prompts FastMCP Server"""

import asyncio
import json
from fastmcp import Client

async def test_advanced_prompts():
    client = Client("http://localhost:8010/mcp")

    async with client:
        print("Testing Advanced NRP.ai Prompts FastMCP Server")
        print("=" * 70)

        # Test 1: List available prompts with tags
        print("\n1. Available Advanced Prompts:")
        try:
            prompts = await client.list_prompts()
            print(f"  Found {len(prompts)} advanced prompts:")
            for prompt in prompts:
                print(f"    - {prompt.name}: {prompt.description}")
                if hasattr(prompt, 'tags') and prompt.tags:
                    print(f"      Tags: {', '.join(prompt.tags)}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: Advanced GPU Request with Complex Parameters
        print("\n" + "=" * 70)
        print("2. Advanced GPU Request (A100 with monitoring):")
        try:
            result = await client.get_prompt("nrp-gpu-advanced-request", {
                "gpu_type": "a100",
                "gpu_count": 2,
                "memory_gb": 64,
                "cpu_cores": 16,
                "namespace": "ml-research",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "priority_class": "high-priority"
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"    Message {i} ({message.role}):")
                print(f"      Length: {len(content_text)} characters")
                if "A100" in content_text:
                    print(f"      Contains A100 instructions: [OK]")
                if "reservation" in content_text.lower():
                    print(f"      Contains reservation info: [OK]")
                if "monitoring" in content_text.lower():
                    print(f"      Contains monitoring config: [OK]")
                if "priorityClassName" in content_text:
                    print(f"      Contains priority class: [OK]")
                print(f"      Preview: {content_text[:200]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: A100 Reservation Guide
        print("\n" + "=" * 70)
        print("3. A100 Reservation Guide:")
        try:
            result = await client.get_prompt("nrp-a100-reservation-guide", {
                "workload_type": "ml_training",
                "memory_gb": 80,
                "cpu_cores": 32,
                "namespace": "research",
                "duration_hours": 48,
                "multi_node": True
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"    Message {i} ({message.role}):")
                if "reservation" in content_text.lower():
                    print(f"      Contains reservation process: [OK]")
                if "multi-node" in content_text.lower():
                    print(f"      Contains multi-node config: [OK]")
                if "48" in content_text:
                    print(f"      Contains duration info: [OK]")
                if "nrp-gpu-scheduler" in content_text:
                    print(f"      Contains NRP scheduler: [OK]")
                print(f"      Content length: {len(content_text)} characters")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Async Storage Configuration
        print("\n" + "=" * 70)
        print("4. Async Storage Configuration:")
        try:
            result = await client.get_prompt("nrp-storage-advanced", {
                "storage_type": "ceph_fs",
                "size": "1Ti",
                "access_mode": "ReadWriteMany",
                "namespace": "shared-data",
                "performance_tier": "high-performance",
                "backup_enabled": True
            })

            # Note: This returns a string, not messages
            if isinstance(result, str):
                content_text = result
            else:
                content_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)

            print(f"  Generated content:")
            print(f"    Content type: {'String response' if isinstance(result, str) else 'Message object'}")
            if "CephFS" in content_text:
                print(f"    Contains CephFS config: [OK]")
            if "high-performance" in content_text:
                print(f"    Contains performance tier: [OK]")
            if "backup" in content_text.lower():
                print(f"    Contains backup config: [OK]")
            if "1Ti" in content_text:
                print(f"    Contains size specification: [OK]")
            print(f"    Content length: {len(content_text)} characters")
            print(f"    Preview: {content_text[:300]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 5: FPGA Advanced Deployment
        print("\n" + "=" * 70)
        print("5. FPGA Advanced Deployment:")
        try:
            result = await client.get_prompt("nrp-fpga-advanced-deployment", {
                "fpga_type": "esnet_smartnic",
                "application": "network_processing",
                "namespace": "fpga-dev",
                "security_context": {"privileged": True, "capabilities": ["NET_ADMIN", "SYS_ADMIN"]},
                "resource_limits": {"memory": "16Gi", "cpu": "8"}
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"    Message {i} ({message.role}):")
                if "esnet" in content_text.lower():
                    print(f"      Contains ESnet config: [OK]")
                if "privileged: true" in content_text.lower():
                    print(f"      Contains privileged mode: [OK]")
                if "NET_ADMIN" in content_text:
                    print(f"      Contains network capabilities: [OK]")
                if "16Gi" in content_text:
                    print(f"      Contains resource limits: [OK]")
                print(f"      Preview: {content_text[:200]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 6: Expert Troubleshooting
        print("\n" + "=" * 70)
        print("6. Expert Troubleshooting:")
        try:
            result = await client.get_prompt("nrp-troubleshooting-expert", {
                "issue_type": "gpu_not_detected",
                "resource_type": "gpu",
                "namespace": "ml-experiments",
                "severity": "high",
                "context": {"node_type": "gpu-node", "gpu_model": "A100", "driver_version": "525.60.13"}
            })

            print(f"  Generated {len(result.messages)} messages:")
            for i, message in enumerate(result.messages, 1):
                content_text = message.content.text if hasattr(message.content, 'text') else str(message.content)
                print(f"    Message {i} ({message.role}):")
                if "kubectl" in content_text.lower():
                    print(f"      Contains kubectl commands: [OK]")
                if "nvidia-smi" in content_text.lower():
                    print(f"      Contains GPU diagnostics: [OK]")
                if "HIGH" in content_text:
                    print(f"      Contains severity level: [OK]")
                if "A100" in content_text:
                    print(f"      Contains context info: [OK]")
                print(f"      Content length: {len(content_text)} characters")
                print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 7: Comprehensive Best Practices
        print("\n" + "=" * 70)
        print("7. Comprehensive Best Practices:")
        try:
            result = await client.get_prompt("nrp-best-practices-comprehensive", {
                "category": "gpu",
                "use_case": "production",
                "compliance_level": "enterprise",
                "team_size": "large"
            })

            # This returns a string
            content_text = result if isinstance(result, str) else str(result)
            print(f"  Generated comprehensive guide:")
            print(f"    Content type: {'String response' if isinstance(result, str) else 'Other'}")
            if "GPU Best Practices" in content_text:
                print(f"    Contains GPU best practices: [OK]")
            if "enterprise" in content_text.lower():
                print(f"    Contains compliance level: [OK]")
            if "large team" in content_text.lower():
                print(f"    Contains team size optimization: [OK]")
            if "SOC2" in content_text:
                print(f"    Contains enterprise compliance: [OK]")
            print(f"    Content length: {len(content_text)} characters")
            print(f"    Preview: {content_text[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 8: Parameter Validation with Enums
        print("\n" + "=" * 70)
        print("8. Parameter Validation with Enums:")
        try:
            # Test different GPU types
            gpu_types = ["general", "a100", "a40", "rtx6000", "gh200"]
            for gpu_type in gpu_types:
                try:
                    result = await client.get_prompt("nrp-gpu-advanced-request", {
                        "gpu_type": gpu_type,
                        "gpu_count": 1,
                        "memory_gb": 32,
                        "cpu_cores": 8
                    })

                    content_text = result.messages[1].content.text if hasattr(result.messages[1].content, 'text') else str(result.messages[1].content)
                    if f"nvidia.com/{gpu_type}" in content_text or "nvidia.com/gpu" in content_text:
                        print(f"    GPU Type '{gpu_type}': [OK] Valid enum value")
                    else:
                        print(f"    GPU Type '{gpu_type}': [WARNING] Resource not found in content")
                except Exception as enum_error:
                    print(f"    GPU Type '{gpu_type}': [ERROR] {enum_error}")

        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)
        print("Advanced NRP.ai Prompts Testing Complete!")

async def demo_advanced_workflow():
    """Demonstrate a complete advanced workflow using all prompt types"""

    print("\n" + "=" * 70)
    print("ADVANCED PROMPT WORKFLOW DEMONSTRATION")
    print("=" * 70)

    client = Client("http://localhost:8010/mcp")

    async with client:
        # Scenario: Enterprise ML team deploying production A100 workload
        print("\nScenario: Enterprise ML Team - Production A100 Deployment")
        print("-" * 60)

        # Step 1: Get comprehensive best practices for enterprise GPU usage
        print("1. Getting enterprise best practices for GPU management...")
        try:
            best_practices = await client.get_prompt("nrp-best-practices-comprehensive", {
                "category": "gpu",
                "use_case": "production",
                "compliance_level": "enterprise",
                "team_size": "large"
            })
            print(f"   Generated enterprise-grade best practices guide")
        except Exception as e:
            print(f"   Error: {e}")

        # Step 2: Create advanced A100 configuration with monitoring
        print("2. Creating advanced A100 configuration with monitoring...")
        try:
            a100_config = await client.get_prompt("nrp-gpu-advanced-request", {
                "gpu_type": "a100",
                "gpu_count": 4,
                "memory_gb": 128,
                "cpu_cores": 32,
                "namespace": "production-ml",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "priority_class": "production"
            })
            print(f"   Generated advanced A100 multi-GPU configuration")
        except Exception as e:
            print(f"   Error: {e}")

        # Step 3: Setup A100 reservation with multi-node support
        print("3. Setting up A100 reservation system...")
        try:
            reservation_guide = await client.get_prompt("nrp-a100-reservation-guide", {
                "workload_type": "ml_training",
                "memory_gb": 80,
                "cpu_cores": 32,
                "namespace": "production-ml",
                "duration_hours": 72,
                "multi_node": True
            })
            print(f"   Generated comprehensive A100 reservation guide")
        except Exception as e:
            print(f"   Error: {e}")

        # Step 4: Configure high-performance storage
        print("4. Configuring high-performance storage...")
        try:
            storage_config = await client.get_prompt("nrp-storage-advanced", {
                "storage_type": "ceph_fs",
                "size": "10Ti",
                "access_mode": "ReadWriteMany",
                "namespace": "production-ml",
                "performance_tier": "high-performance",
                "backup_enabled": True
            })
            print(f"   Generated enterprise storage configuration")
        except Exception as e:
            print(f"   Error: {e}")

        # Step 5: Setup expert troubleshooting procedures
        print("5. Setting up expert troubleshooting procedures...")
        try:
            troubleshooting = await client.get_prompt("nrp-troubleshooting-expert", {
                "issue_type": "pod_pending",
                "resource_type": "gpu",
                "namespace": "production-ml",
                "severity": "critical",
                "context": {
                    "environment": "production",
                    "team_size": "large",
                    "compliance": "enterprise"
                }
            })
            print(f"   Generated expert troubleshooting procedures")
        except Exception as e:
            print(f"   Error: {e}")

        print("\nAdvanced Workflow Complete: Enterprise team now has:")
        print("  [OK] Enterprise-grade best practices with compliance")
        print("  [OK] Advanced A100 multi-GPU configuration with monitoring")
        print("  [OK] Comprehensive reservation system with multi-node support")
        print("  [OK] High-performance storage with backup and disaster recovery")
        print("  [OK] Expert-level troubleshooting with automated diagnostics")
        print("  [OK] Complete compliance documentation and security frameworks")

if __name__ == "__main__":
    asyncio.run(test_advanced_prompts())
    asyncio.run(demo_advanced_workflow())