#!/usr/bin/env python3
"""
Demo: NRP Search Integration
===========================

Demonstrates how the enhanced system now uses NRP's built-in search functionality
(Ctrl+K) for more accurate and complete information extraction.

This addresses the original concern about incorrect information extraction
by leveraging the site's own search index.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from systems.nrp_search_navigator import NRPSearchNavigator
from systems.enhanced_navigator import EnhancedNavigator
from agents.infogent_agent import InfogentAgent
from agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

def demo_nrp_search_vs_manual():
    """Compare NRP search results vs manual link discovery."""
    print("🔍 NRP Search Integration Demo")
    print("=" * 50)

    query = "How do I request A100 GPUs for machine learning?"
    print(f"Query: {query}\n")

    # Method 1: Direct NRP Search
    print("📊 Method 1: Using NRP's Built-in Search (Ctrl+K)")
    print("-" * 45)

    search_navigator = NRPSearchNavigator()
    try:
        search_results = search_navigator.search_nrp_documentation(query, limit=5)

        print(f"✅ Found {len(search_results)} results using NRP's search")

        for i, result in enumerate(search_results[:3], 1):
            print(f"  {i}. {result['title']}")
            print(f"     📍 {result['url']}")
            print(f"     🎯 Relevance: {result.get('relevance_score', 0):.2f}")
            print(f"     🏷️  Topic: {result.get('topic', 'general')}")

            if result.get('snippet'):
                snippet = result['snippet'][:120] + "..." if len(result['snippet']) > 120 else result['snippet']
                print(f"     💭 {snippet}")
            print()

        # Show search suggestions
        suggestions = search_navigator.get_search_suggestions(query)
        if suggestions:
            print(f"💡 Search suggestions: {', '.join(suggestions[:3])}")

    except Exception as e:
        print(f"❌ NRP search failed: {e}")

    print("\n" + "=" * 50)

    # Method 2: Enhanced Navigator (integrates both methods)
    print("🚀 Method 2: Enhanced Navigator (NRP Search + Fallbacks)")
    print("-" * 52)

    navigator = EnhancedNavigator()
    try:
        links = navigator.discover_relevant_links(query)

        print(f"✅ Found {len(links)} total results (search + fallbacks)")

        for i, link in enumerate(links[:3], 1):
            print(f"  {i}. {link['title']}")
            print(f"     📍 {link['url']}")
            print(f"     🎯 Relevance: {link.get('relevance', 0):.2f}")
            print(f"     🔧 Method: {link.get('search_method', 'manual')}")
            print(f"     📑 Type: {link.get('source_type', 'unknown')}")
            print()

    except Exception as e:
        print(f"❌ Enhanced navigation failed: {e}")

def demo_a100_gpu_accuracy():
    """Demonstrate improved accuracy for A100 GPU requests."""
    print("\n🎯 A100 GPU Query Accuracy Demo")
    print("=" * 40)

    test_queries = [
        "A100 GPU configuration",
        "Request A100 for PyTorch",
        "A100 vs V100 differences",
        "NVIDIA A100 resource limits"
    ]

    search_navigator = NRPSearchNavigator()

    for query in test_queries:
        print(f"\n🔎 Query: {query}")
        print("-" * 30)

        try:
            results = search_navigator.search_nrp_documentation(query, limit=3)

            if results:
                best_result = results[0]
                print(f"✅ Best match: {best_result['title']}")
                print(f"   🎯 Relevance: {best_result.get('relevance_score', 0):.2f}")
                print(f"   🏷️  Topic: {best_result.get('topic', 'general')}")
                print(f"   🔗 URL: {best_result['url']}")

                if best_result.get('snippet'):
                    snippet = best_result['snippet'][:100] + "..." if len(best_result['snippet']) > 100 else best_result['snippet']
                    print(f"   📝 Preview: {snippet}")
            else:
                print("❌ No results found")

        except Exception as e:
            print(f"❌ Search failed: {e}")

def demo_full_infogent_integration():
    """Demonstrate the full infogent agent with NRP search integration."""
    print("\n🤖 Full Infogent Agent Demo (with NRP Search)")
    print("=" * 50)

    agent = InfogentAgent()

    request = AgentRequest(
        user_input="How do I configure A100 GPUs for a machine learning training job in NRP?",
        intent_type=IntentType.QUESTION,
        confidence=ConfidenceLevel.HIGH,
        context={"framework": "machine_learning", "gpu_type": "a100"}
    )

    print(f"🔍 Query: {request.user_input}")
    print("-" * 60)

    try:
        print("🔄 Processing with enhanced infogent agent...")
        response = agent.process(request)

        if response.success:
            print("✅ Agent Response Generated Successfully!")
            print(f"🤖 Agent Type: {response.agent_type}")
            print(f"🎯 Confidence: {response.confidence}")

            print("\n📊 Response Metadata:")
            for key, value in response.metadata.items():
                print(f"   {key}: {value}")

            print("\n📝 Response Preview:")
            preview = response.content[:400] + "..." if len(response.content) > 400 else response.content
            print(preview)

            if response.follow_up_suggestions:
                print(f"\n💡 Follow-up Suggestions:")
                for suggestion in response.follow_up_suggestions:
                    print(f"   • {suggestion}")

        else:
            print(f"❌ Agent failed: {response.content}")

    except Exception as e:
        print(f"❌ Full integration failed: {e}")

def main():
    """Run the demo."""
    print("🚀 NRP Search Integration Demonstration")
    print("=" * 60)
    print("This demo shows how the enhanced system now uses NRP's")
    print("built-in search functionality for better accuracy.\n")

    # Run demos
    demo_nrp_search_vs_manual()
    demo_a100_gpu_accuracy()
    demo_full_infogent_integration()

    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("\n📋 Key Benefits of NRP Search Integration:")
    print("  ✅ Uses NRP's own search index (more accurate)")
    print("  ✅ Gets pre-ranked results (better relevance)")
    print("  ✅ Accesses same results users see (consistency)")
    print("  ✅ Automatic fallback to manual methods if needed")
    print("  ✅ Enhanced relevance scoring for GPU queries")
    print("  ✅ Better handling of specific hardware requests")

if __name__ == "__main__":
    main()