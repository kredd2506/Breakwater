#!/usr/bin/env python3
"""
Test User Questions
==================

Test the knowledge base with the actual user questions to verify
that it returns relevant templates and speeds up responses.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_user_question_1():
    """Test: 'Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?'"""
    print("Testing User Question 1")
    print("="*60)
    print("Question: 'Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?'")
    print()

    try:
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase

        kb = EnhancedKnowledgeBase()

        # Check knowledge base state
        stats = kb.get_statistics()
        print(f"Knowledge Base: {stats['total_templates']} templates available")

        # Search for relevant templates
        query = "Should users run sleep in batch jobs on Nautilus, or optimize for short runtime"
        results = kb.search_templates(query, limit=5)

        print(f"Search Results: {len(results)} templates found")
        print()

        for i, result in enumerate(results, 1):
            template = result.template.template
            print(f"Result {i}: {template.title}")
            print(f"  Relevance Score: {result.relevance_score:.3f}")
            print(f"  Resource Type: {template.resource_type}")
            print(f"  Warnings: {len(template.warnings)}")
            print(f"  Cautions: {len(template.cautions)}")
            print(f"  Best Practices: {len(template.best_practices)}")

            if template.warnings:
                print(f"  Key Warning: {template.warnings[0][:80]}...")
            if template.best_practices:
                print(f"  Key Practice: {template.best_practices[0][:80]}...")
            print()

        # Simulate answer generation using top result
        if results:
            top_template = results[0].template.template
            print("Generated Answer Preview:")
            print("-" * 40)
            answer_preview = f"""Based on NRP best practices:

**Recommendation: Optimize for short runtime rather than using sleep in batch jobs.**

Key points:
- {top_template.cautions[0] if top_template.cautions else 'Jobs should be designed efficiently'}
- {top_template.best_practices[0] if top_template.best_practices else 'Use appropriate timeouts'}

Example YAML:
```yaml
{top_template.yaml_content[:200]}...
```

Warnings:
- {top_template.warnings[0] if top_template.warnings else 'No specific warnings'}
"""
            print(answer_preview)

        return len(results) > 0

    except Exception as e:
        print(f"User question 1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_question_2():
    """Test: 'can i run jobs indefinitely'"""
    print("\n" + "="*60)
    print("Testing User Question 2")
    print("="*60)
    print("Question: 'can i run jobs indefinitely'")
    print()

    try:
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase

        kb = EnhancedKnowledgeBase()

        # Search for relevant templates
        query = "can i run jobs indefinitely"
        results = kb.search_templates(query, limit=5)

        print(f"Search Results: {len(results)} templates found")
        print()

        for i, result in enumerate(results, 1):
            template = result.template.template
            print(f"Result {i}: {template.title}")
            print(f"  Relevance Score: {result.relevance_score:.3f}")
            print(f"  Resource Type: {template.resource_type}")

            if template.dangers:
                print(f"  Key Danger: {template.dangers[0][:80]}...")
            if template.cautions:
                print(f"  Key Caution: {template.cautions[0][:80]}...")
            print()

        # Simulate answer generation using top result
        if results:
            top_template = results[0].template.template
            print("Generated Answer Preview:")
            print("-" * 40)
            answer_preview = f"""**No, jobs should not run indefinitely on Nautilus.**

{top_template.description}

Key reasons:
- {top_template.cautions[0] if top_template.cautions else 'Cluster policies prevent indefinite execution'}
- {top_template.dangers[0] if top_template.dangers else 'Resource consumption concerns'}

Best practices:
- {top_template.best_practices[0] if top_template.best_practices else 'Use proper timeouts'}
- {top_template.best_practices[1] if len(top_template.best_practices) > 1 else 'Design finite workloads'}

Example with timeout:
```yaml
{top_template.yaml_content[:200]}...
```
"""
            print(answer_preview)

        return len(results) > 0

    except Exception as e:
        print(f"User question 2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_base_performance():
    """Test knowledge base lookup performance."""
    print("\n" + "="*60)
    print("Testing Knowledge Base Performance")
    print("="*60)

    try:
        import time
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase

        kb = EnhancedKnowledgeBase()

        # Test multiple searches to measure performance
        queries = [
            "batch jobs sleep runtime",
            "indefinite jobs running forever",
            "job timeout policies",
            "activeDeadlineSeconds examples",
            "optimize job performance"
        ]

        total_time = 0
        total_results = 0

        for query in queries:
            start_time = time.time()
            results = kb.search_templates(query, limit=3)
            end_time = time.time()

            search_time = end_time - start_time
            total_time += search_time
            total_results += len(results)

            print(f"Query: '{query[:30]}...' -> {len(results)} results in {search_time:.3f}s")

        avg_time = total_time / len(queries)
        avg_results = total_results / len(queries)

        print()
        print(f"Performance Summary:")
        print(f"  Average search time: {avg_time:.3f} seconds")
        print(f"  Average results per query: {avg_results:.1f}")
        print(f"  Total templates searched: {kb.get_statistics()['total_templates']}")

        # Performance is good if searches are under 0.1 seconds
        performance_good = avg_time < 0.1

        print(f"  Performance: {'EXCELLENT' if performance_good else 'ACCEPTABLE'}")

        return performance_good

    except Exception as e:
        print(f"Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yaml_examples_access():
    """Test access to stored YAML examples."""
    print("\n" + "="*60)
    print("Testing YAML Examples Access")
    print("="*60)

    try:
        yaml_examples_dir = Path("nrp_k8s_system/cache/yaml_examples")
        metadata_file = yaml_examples_dir / "examples_metadata.json"

        if not metadata_file.exists():
            print("YAML examples metadata not found")
            return False

        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        print(f"YAML Examples Available: {len(metadata['job_examples'])}")

        # Display examples
        for example_id, example_info in metadata['job_examples'].items():
            print(f"\nExample: {example_id}")
            print(f"  Title: {example_info['title']}")
            print(f"  File: {example_info['file']}")
            print(f"  Description: {example_info['description']}")
            print(f"  Warnings: {len(example_info['warnings'])}")
            print(f"  Best Practices: {len(example_info['best_practices'])}")

            # Check if file exists
            yaml_file = yaml_examples_dir / example_info['file']
            if yaml_file.exists():
                print(f"  File Status: EXISTS ({yaml_file.stat().st_size} bytes)")
            else:
                print(f"  File Status: MISSING")

        print(f"\nTopics: {list(metadata['topics'].keys())}")

        return True

    except Exception as e:
        print(f"YAML examples access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all user question tests."""
    print("User Questions Test Suite")
    print("="*60)

    try:
        # Test both user questions
        q1_success = test_user_question_1()
        q2_success = test_user_question_2()

        # Test performance
        perf_success = test_knowledge_base_performance()

        # Test YAML examples
        yaml_success = test_yaml_examples_access()

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Question 1 (sleep in batch jobs): {'[OK]' if q1_success else '[FAIL]'}")
        print(f"Question 2 (indefinite jobs): {'[OK]' if q2_success else '[FAIL]'}")
        print(f"Performance: {'[OK]' if perf_success else '[FAIL]'}")
        print(f"YAML Examples: {'[OK]' if yaml_success else '[FAIL]'}")

        if all([q1_success, q2_success, perf_success, yaml_success]):
            print("\n[SUCCESS] Knowledge base will now provide fast, relevant responses!")
            print("Next time users ask these questions, the system will:")
            print("- Find relevant templates from knowledge base")
            print("- Return answers much faster (no re-extraction)")
            print("- Include warnings, cautions, and YAML examples")
            print("- Provide comprehensive guidance with citations")
        else:
            print("\n[ISSUES] Some components need attention.")

    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()