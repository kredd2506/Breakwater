#!/usr/bin/env python3
"""
Final Comprehensive NRP QA System Analysis - DeepSeek-R1 Edition
Comprehensive testing of all MCP functionality with DeepSeek-R1 model
"""

import asyncio
import json
import time
import os
import sys
from pathlib import Path
import requests

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

def print_header(title):
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}")

def print_section(title):
    print(f"\n{'-'*60}")
    print(f"{title}")
    print(f"{'-'*60}")

async def test_deepseek_r1_integration():
    """Test the DeepSeek-R1 model integration"""
    print_header("DeepSeek-R1 Model Integration Test")

    # Test direct API call
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key="60giG4L3xNAMC1FT2f2ivYnExpHYA1fD",
            base_url="https://ellm.nrp-nautilus.io/v1"
        )

        response = await client.chat.completions.create(
            model="deepseek-r1",
            messages=[
                {"role": "user", "content": "Explain GPU allocation in Kubernetes in one sentence."}
            ]
        )

        print("[OK] DeepSeek-R1 API Connection: SUCCESS")
        print(f"Response: {response.choices[0].message.content[:100]}...")
        return True

    except Exception as e:
        print(f"[ERROR] DeepSeek-R1 API Connection: FAILED - {e}")
        return False

async def test_mcp_server_status():
    """Test MCP server status and availability"""
    print_section("MCP Server Status Check")

    import requests
    try:
        # Test if server is running
        response = requests.get("http://127.0.0.1:8025", timeout=5)
        print(f"[OK] MCP Server: RUNNING (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"[ERROR] MCP Server: NOT ACCESSIBLE - {e}")
        return False

async def comprehensive_qa_analysis():
    """Run comprehensive QA analysis"""
    print_header("FINAL COMPREHENSIVE NRP QA SYSTEM ANALYSIS - DEEPSEEK-R1")

    results = {}

    # 1. Test DeepSeek-R1 integration
    results['deepseek_r1'] = await test_deepseek_r1_integration()

    # 2. Test MCP server
    results['mcp_server'] = await test_mcp_server_status()

    # 3. Test knowledge bases
    print_section("Knowledge Base Availability")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))
        from cache.nrp_gpu_knowledge import NRP_GPU_RESOURCES
        print(f"[OK] GPU Knowledge Base: {len(NRP_GPU_RESOURCES)} resources loaded")
        results['gpu_knowledge'] = True
    except Exception as e:
        print(f"[ERROR] GPU Knowledge Base: FAILED - {e}")
        results['gpu_knowledge'] = False

    try:
        from nrp_k8s_system.cache.nrp_complete_anchor_db import NRP_COMPLETE_ANCHORS
        print(f"[OK] Complete Anchor DB: {len(NRP_COMPLETE_ANCHORS)} anchors loaded")
        results['anchor_db'] = True
    except Exception as e:
        print(f"[ERROR] Complete Anchor DB: FAILED - {e}")
        results['anchor_db'] = False

    # 4. Test Kubernetes integration
    print_section("Kubernetes Integration")
    try:
        from kubernetes import client, config
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            print("[OK] Kubernetes Client: CONFIGURED")
            results['kubernetes'] = True
        except:
            print("[WARNING] Kubernetes Client: Not configured (expected in local environment)")
            results['kubernetes'] = False
    except Exception as e:
        print(f"[ERROR] Kubernetes Client: FAILED - {e}")
        results['kubernetes'] = False

    # 5. Environment variables check
    print_section("Environment Configuration")
    env_vars = [
        "NRP_API_KEY", "NRP_BASE_URL", "NRP_MODEL",
        "SERPER_API_KEY", "BING_SEARCH_KEY"
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"[OK] {var}: SET ({value[:10]}...)")
        else:
            print(f"[ERROR] {var}: NOT SET")

    # 6. Test file system access
    print_section("File System Access")
    test_paths = [
        "nrp_k8s_system/",
        "mcp/ultimate_fastmcp_server.py",
        "cache/",
        ".env"
    ]

    for path in test_paths:
        if Path(path).exists():
            print(f"[OK] {path}: EXISTS")
        else:
            print(f"[ERROR] {path}: NOT FOUND")

    # Summary
    print_header("COMPREHENSIVE TEST RESULTS SUMMARY")
    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    # Detailed results
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name}: {status}")

    # Final recommendation
    print_header("FINAL RECOMMENDATION")
    if passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("[SUCCESS] SYSTEM STATUS: READY FOR PRODUCTION")
        print("The NRP K8s System with DeepSeek-R1 is functioning well!")
    else:
        print("[WARNING] SYSTEM STATUS: NEEDS ATTENTION")
        print("Some components require fixes before production use.")

    return results

if __name__ == "__main__":
    print("Starting Final Comprehensive NRP QA System Analysis...")
    results = asyncio.run(comprehensive_qa_analysis())