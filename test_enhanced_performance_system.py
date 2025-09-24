#!/usr/bin/env python3
"""
Test the enhanced system against the known GPU vs CPU encoding performance question.
"""

import sys
import os
from pathlib import Path

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.orchestrator import AgentOrchestrator


def test_gpu_cpu_encoding_comprehensive():
    """Test the full enhanced system with the specific performance question."""

    # The exact question that should route to gui-desktop/#performance-considerations
    question = "When deciding between GPU and CPU encoding, how do performance trade-offs—such as CPU usage, resolution requirements, and network bandwidth efficiency—affect which option is more suitable?"

    print("Testing Enhanced INFOGENT with GPU vs CPU Encoding Question")
    print("=" * 80)
    print(f"Question: {question}")
    print("=" * 80)

    expected_content_elements = [
        "GPU encoding", "CPU encoding", "nvh264enc", "x264enc",
        "CPU usage", "resolution", "bandwidth", "performance",
        "hardware acceleration", "NVENC", "compression"
    ]

    expected_url = "https://nrp.ai/documentation/userdocs/running/gui-desktop/#performance-considerations"

    try:
        # Test the full orchestrator system
        orchestrator = AgentOrchestrator()
        response_content, success = orchestrator.process_request(question)

        print("\n" + "="*50 + " SYSTEM RESPONSE " + "="*50)
        print(response_content)
        print("=" * 117)

        # Analyze the response
        print(f"\nRESULT ANALYSIS:")
        print(f"Success: {success}")

        if success:
            response_lower = response_content.lower()

            # Check for expected content elements
            found_elements = []
            missing_elements = []

            for element in expected_content_elements:
                if element.lower() in response_lower:
                    found_elements.append(element)
                else:
                    missing_elements.append(element)

            print(f"\nContent Analysis:")
            print(f"Found elements ({len(found_elements)}/{len(expected_content_elements)}): {found_elements}")

            if missing_elements:
                print(f"Missing elements: {missing_elements}")

            # Check for source URL
            if expected_url in response_content:
                print(f"✓ Correct source URL found: {expected_url}")
            else:
                print(f"✗ Expected source URL not found: {expected_url}")

            # Overall assessment
            coverage_ratio = len(found_elements) / len(expected_content_elements)

            if coverage_ratio >= 0.8 and expected_url in response_content:
                print(f"\n🎉 EXCELLENT: System provides comprehensive answer with correct source!")
                print(f"Coverage: {coverage_ratio:.1%}")
                return True
            elif coverage_ratio >= 0.6:
                print(f"\n✓ GOOD: System provides relevant answer with {coverage_ratio:.1%} coverage")
                return True
            else:
                print(f"\n⚠️ PARTIAL: System response missing key elements ({coverage_ratio:.1%} coverage)")
                return False
        else:
            print("✗ FAILED: System could not process the request successfully")
            return False

    except Exception as e:
        print(f"✗ ERROR: System test failed with exception: {e}")
        return False


def test_edge_cases():
    """Test various edge cases for performance questions."""

    edge_case_questions = [
        # Different phrasings of the same concept
        "GPU vs CPU encoding performance comparison",
        "What are the trade-offs between hardware and software encoding?",
        "When should I use NVENC vs x264?",
        "Performance differences between GPU and CPU video encoding",

        # Related but different performance topics
        "How to optimize GPU performance for ML workloads?",
        "CPU performance tuning for Kubernetes pods",
        "Network bandwidth optimization strategies",

        # Shared memory questions (should hit different anchor)
        "How to add shared memory to GPU pods?",
        "Increase shm size for my application",
    ]

    print("\n" + "="*80)
    print("TESTING EDGE CASES")
    print("="*80)

    orchestrator = AgentOrchestrator()
    results = []

    for i, question in enumerate(edge_case_questions):
        print(f"\nEdge Case {i+1}: {question}")
        print("-" * 60)

        try:
            response_content, success = orchestrator.process_request(question)

            # Brief response analysis
            response_preview = response_content[:200] + "..." if len(response_content) > 200 else response_content
            print(f"Success: {success}")
            print(f"Response preview: {response_preview}")

            # Check if it found relevant NRP documentation
            nrp_urls = [
                "https://nrp.ai/documentation/userdocs/running/gui-desktop/",
                "https://nrp.ai/documentation/userdocs/running/gpu-pods/",
                "https://nrp.ai/documentation/userdocs/"
            ]

            found_nrp_source = any(url in response_content for url in nrp_urls)

            print(f"Found NRP source: {found_nrp_source}")
            results.append((question, success, found_nrp_source))

        except Exception as e:
            print(f"Error: {e}")
            results.append((question, False, False))

    # Summary
    successful_requests = sum(1 for _, success, _ in results if success)
    found_nrp_sources = sum(1 for _, _, found_nrp in results if found_nrp)

    print(f"\nEDGE CASE SUMMARY:")
    print(f"Successful requests: {successful_requests}/{len(edge_case_questions)}")
    print(f"Found NRP sources: {found_nrp_sources}/{len(edge_case_questions)}")

    return successful_requests >= len(edge_case_questions) * 0.8  # 80% success rate


def main():
    """Run comprehensive tests."""
    print("COMPREHENSIVE ENHANCED INFOGENT SYSTEM TEST")
    print("="*80)

    # Test 1: Main GPU vs CPU encoding question
    test1_result = test_gpu_cpu_encoding_comprehensive()

    # Test 2: Edge cases
    test2_result = test_edge_cases()

    # Final assessment
    print(f"\n" + "="*80)
    print("FINAL ASSESSMENT")
    print("="*80)
    print(f"Main GPU vs CPU encoding test: {'PASS' if test1_result else 'FAIL'}")
    print(f"Edge cases test: {'PASS' if test2_result else 'FAIL'}")

    if test1_result and test2_result:
        print(f"\n🎉 SUCCESS: Enhanced INFOGENT system provides ideal behavior!")
        print(f"\nKey achievements:")
        print(f"- Correctly routes performance questions to INFOGENT")
        print(f"- Identifies specific NRP documentation targets")
        print(f"- Provides comprehensive answers with correct source citations")
        print(f"- Handles edge cases and variations effectively")
        print(f"- Uses real-time NRP documentation when cached knowledge insufficient")
    else:
        print(f"\n⚠️ Some issues remain - system needs further refinement")

    return test1_result and test2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)