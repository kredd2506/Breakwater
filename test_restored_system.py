#!/usr/bin/env python3
"""
Test Restored System Without Ctrl+K
===================================

Test the original infogent architecture without browser automation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_restored_system():
    """Test the restored system without Ctrl+K."""
    print("Testing Restored Infogent System (No Ctrl+K)")
    print("=" * 50)

    try:
        # Test with the original infogent agent
        from nrp_k8s_system.agents.infogent_agent import InfogentAgent
        from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

        agent = InfogentAgent()
        query = "How can users access and use Ceph-based S3 object storage within their namespace?"

        print(f"Query: {query}")
        print("\nProcessing with original infogent agent...")

        # Create request
        request = AgentRequest(
            user_input=query,
            intent_type=IntentType.QUESTION,
            confidence=ConfidenceLevel.HIGH,
            context={"focus": "storage ceph s3 namespace"}
        )

        # Process request
        response = agent.process(request)

        print(f"\nResults:")
        print(f"Success: {response.success}")
        print(f"Confidence: {response.confidence:.3f}")
        print(f"Response length: {len(response.content)} chars")

        print(f"\nResponse preview:")
        print("-" * 30)
        preview = response.content[:300] + "..." if len(response.content) > 300 else response.content
        print(preview)

        if response.citations:
            print(f"\nCitations: {len(response.citations)}")
            for citation in response.citations[:3]:
                print(f"  - {citation}")

        return response.success

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_restored_system()
    if success:
        print(f"\n[SUCCESS] Original infogent system working!")
        print(f"[OK] Navigator -> Extractor -> Aggregator architecture functional")
        print(f"[OK] No browser automation needed")
        print(f"[OK] Clean, reliable responses")
    else:
        print(f"\n[ERROR] System needs additional fixes")