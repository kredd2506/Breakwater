#!/usr/bin/env python3
"""
Simple Test of Intelligent Workflow
===================================

Quick test to verify the system works without issues.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_simple():
    """Simple test of the intelligent workflow."""
    try:
        from nrp_k8s_system.core.intelligent_workflow import IntelligentWorkflow

        print("Testing Intelligent Workflow...")
        workflow = IntelligentWorkflow()

        query = "How can users access and use Ceph-based S3 object storage within their namespace?"
        print(f"Query: {query}")

        print("\nProcessing...")
        response = await workflow.process_query(query)

        print(f"\nResponse received!")
        print(f"Confidence: {response.confidence:.3f}")
        print(f"Search time: {response.search_time:.2f}s")
        print(f"Extractions: {len(response.quick_extractions)}")
        print(f"K8s info: {'Yes' if response.kubernetes_info else 'No'}")

        # Show response preview
        if response.primary_answer:
            print(f"\nResponse preview:")
            print("-" * 40)
            preview = response.primary_answer[:200] + "..." if len(response.primary_answer) > 200 else response.primary_answer
            print(preview)

        # Clean up
        workflow.cleanup()
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())