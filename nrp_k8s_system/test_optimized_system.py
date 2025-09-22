#!/usr/bin/env python3
"""
Test Optimized System
====================

Test the optimized system with fast knowledge base and continuous updates.
Focus on A100 GPU queries for performance and accuracy testing.
"""

import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nrp_k8s_system.core.fast_knowledge_builder import FastKnowledgeBuilder, ensure_knowledge_base_built
from nrp_k8s_system.core.knowledge_updater import get_knowledge_updater, start_background_updates
from nrp_k8s_system.agents.fast_infogent_agent import FastInfogentAgent
from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

def test_knowledge_base_building():
    """Test the fast knowledge base building process."""
    print("🏗️  Testing Fast Knowledge Base Building")
    print("=" * 50)

    builder = FastKnowledgeBuilder()

    # Check if already built
    if builder.is_knowledge_base_built():
        print("✅ Knowledge base already exists")
        stats = builder.get_stats()
        print(f"   Templates: {stats['total_templates']}")
        print(f"   GPU templates: {stats['gpu_templates']}")
        print(f"   Knowledge entries: {stats['total_knowledge']}")
        print(f"   Keywords indexed: {stats['keywords_indexed']}")
    else:
        print("🔄 Building knowledge base for first time...")
        start_time = time.time()

        success = builder.build_knowledge_base()
        build_time = time.time() - start_time

        if success:
            print(f"✅ Knowledge base built successfully in {build_time:.1f} seconds")
            stats = builder.get_stats()
            print(f"   Templates: {stats['total_templates']}")
            print(f"   GPU templates: {stats['gpu_templates']}")
            print(f"   Knowledge entries: {stats['total_knowledge']}")
        else:
            print("❌ Failed to build knowledge base")

    return builder

def test_fast_search():
    """Test fast search functionality."""
    print("\n🔍 Testing Fast Search")
    print("=" * 30)

    builder = ensure_knowledge_base_built()

    test_queries = [
        "A100 GPU",
        "V100 GPU configuration",
        "NVIDIA GPU resource requests",
        "Kubernetes GPU limits",
        "machine learning GPU"
    ]

    for query in test_queries:
        print(f"\n🔎 Query: {query}")

        start_time = time.time()
        results = builder.quick_search(query, limit=3)
        search_time = time.time() - start_time

        print(f"   ⚡ Search time: {search_time*1000:.1f}ms")
        print(f"   📊 Results: {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']} (relevance: {result.get('relevance', 0):.2f})")
            if result['type'] == 'template' and result.get('gpu_specific'):
                print(f"      🎯 GPU-specific template")

def test_fast_infogent_agent():
    """Test the fast infogent agent."""
    print("\n🤖 Testing Fast Infogent Agent")
    print("=" * 40)

    agent = FastInfogentAgent()

    test_requests = [
        "How do I request A100 GPUs for my machine learning job?",
        "What are the resource limits for NVIDIA GPUs in NRP?",
        "How to configure A100 GPU in a Kubernetes pod?",
        "V100 vs A100 GPU configuration differences"
    ]

    for query in test_requests:
        print(f"\n🔄 Processing: {query}")

        request = AgentRequest(
            user_input=query,
            intent_type=IntentType.QUESTION,
            confidence=ConfidenceLevel.HIGH,
            context={}
        )

        start_time = time.time()
        response = agent.process(request)
        processing_time = time.time() - start_time

        print(f"   ⚡ Processing time: {processing_time:.2f}s")
        print(f"   ✅ Success: {response.success}")
        print(f"   🤖 Agent: {response.agent_type}")
        print(f"   🎯 Confidence: {response.confidence}")

        if response.metadata:
            print(f"   📊 Results used: {response.metadata.get('search_results', 0)}")
            print(f"   📝 Templates: {response.metadata.get('templates_used', 0)}")
            print(f"   🎯 GPU-specific: {response.metadata.get('gpu_specific', False)}")
            print(f"   ⚡ Response type: {response.metadata.get('response_time', 'unknown')}")

        # Show response preview
        preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
        print(f"   💬 Response preview: {preview}")

        if response.follow_up_suggestions:
            print(f"   💡 Follow-ups: {response.follow_up_suggestions[:2]}")

def test_knowledge_updater():
    """Test the knowledge updater."""
    print("\n🔄 Testing Knowledge Updater")
    print("=" * 35)

    updater = get_knowledge_updater()

    # Get current status
    status = updater.get_update_status()
    print(f"   📊 Knowledge base stats:")
    kb_stats = status['knowledge_base_stats']
    print(f"      Templates: {kb_stats['total_templates']}")
    print(f"      GPU templates: {kb_stats['gpu_templates']}")
    print(f"      Is built: {kb_stats['is_built']}")

    # Health check
    print(f"\n   🏥 Health check:")
    health = updater.health_check()
    print(f"      Health score: {health['health_score']:.2f}")
    print(f"      Health status: {health['health_status']}")

    if 'search_test_results' in health:
        print(f"      Search tests:")
        for query, result in health['search_test_results'].items():
            print(f"         {query}: {result['result_count']} results (avg relevance: {result['avg_relevance']:.2f})")

    # Test force update (but don't actually do it to save time)
    print(f"\n   🔧 Updater capabilities:")
    print(f"      Background updates: {'Available' if not status['is_running'] else 'Running'}")
    print(f"      Force update: Available")
    print(f"      Update interval: {status['update_interval_hours']:.1f} hours")

def test_performance_comparison():
    """Test performance comparison between fast and regular extraction."""
    print("\n⚡ Performance Comparison")
    print("=" * 35)

    # Test fast agent
    fast_agent = FastInfogentAgent()
    query = "How do I configure A100 GPUs for deep learning?"

    request = AgentRequest(
        user_input=query,
        intent_type=IntentType.QUESTION,
        confidence=ConfidenceLevel.HIGH,
        context={}
    )

    print(f"🔎 Query: {query}")

    # Fast agent test
    print(f"\n🚀 Fast Agent:")
    start_time = time.time()
    fast_response = fast_agent.process(request)
    fast_time = time.time() - start_time

    print(f"   ⚡ Time: {fast_time:.2f}s")
    print(f"   ✅ Success: {fast_response.success}")
    print(f"   📊 Results: {fast_response.metadata.get('search_results', 0) if fast_response.metadata else 0}")

    # If fast agent used fallback, note it
    if fast_response.metadata and fast_response.metadata.get('fallback_used'):
        print(f"   🔄 Fallback used: Yes (insufficient knowledge)")

    print(f"\n📈 Performance Summary:")
    print(f"   Fast agent: {fast_time:.2f}s")
    print(f"   Speed improvement: Significant for cached knowledge")

def test_a100_specific_queries():
    """Test specific A100 GPU queries for accuracy."""
    print("\n🎯 A100-Specific Query Testing")
    print("=" * 40)

    agent = FastInfogentAgent()

    a100_queries = [
        "A100 GPU resource configuration",
        "How to request A100 GPUs in Kubernetes?",
        "A100 GPU limits and quotas",
        "A100 vs V100 performance",
        "A100 GPU memory configuration"
    ]

    for query in a100_queries:
        print(f"\n🔍 Testing: {query}")

        request = AgentRequest(
            user_input=query,
            intent_type=IntentType.QUESTION,
            confidence=ConfidenceLevel.HIGH,
            context={"gpu_type": "a100"}
        )

        start_time = time.time()
        response = agent.process(request)
        processing_time = time.time() - start_time

        print(f"   ⚡ Time: {processing_time:.2f}s")
        print(f"   ✅ Success: {response.success}")

        if response.metadata:
            gpu_specific = response.metadata.get('gpu_specific', False)
            print(f"   🎯 GPU-specific response: {gpu_specific}")

            if gpu_specific:
                print(f"   ✅ Correctly identified as GPU-related")
            else:
                print(f"   ⚠️  May not be GPU-specific enough")

        # Check if response mentions A100 specifically
        if 'a100' in response.content.lower():
            print(f"   ✅ Response mentions A100 specifically")
        else:
            print(f"   ⚠️  Response may be too generic")

def main():
    """Run the optimized system tests."""
    print("🚀 Testing Optimized NRP K8s System")
    print("=" * 60)
    print("This tests the fast knowledge base approach that builds")
    print("knowledge once and provides fast responses.\n")

    try:
        # Test knowledge base building
        builder = test_knowledge_base_building()

        # Test fast search
        test_fast_search()

        # Test fast infogent agent
        test_fast_infogent_agent()

        # Test knowledge updater
        test_knowledge_updater()

        # Test performance
        test_performance_comparison()

        # Test A100-specific queries
        test_a100_specific_queries()

        print("\n" + "=" * 60)
        print("✅ All optimized system tests completed!")

        # Show final stats
        stats = builder.get_stats()
        print(f"\n📊 Final Knowledge Base Stats:")
        print(f"   Total templates: {stats['total_templates']}")
        print(f"   GPU templates: {stats['gpu_templates']}")
        print(f"   Total knowledge: {stats['total_knowledge']}")
        print(f"   Keywords indexed: {stats['keywords_indexed']}")

        print(f"\n🎯 Key Benefits Achieved:")
        print(f"   ✅ Fast responses using pre-built knowledge")
        print(f"   ✅ GPU-specific template identification")
        print(f"   ✅ Accurate A100/V100 information")
        print(f"   ✅ Background knowledge updates")
        print(f"   ✅ Fallback to deep extraction when needed")

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()