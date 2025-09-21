#!/usr/bin/env python3
"""
Test Knowledge Base Update Flow
==============================

Test the complete flow from question processing to knowledge base updates
to identify why templates aren't being stored.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging to see detailed output
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_navigation_sources():
    """Test the navigation to find sources."""
    print("="*60)
    print("Testing Navigation Sources")
    print("="*60)

    try:
        from nrp_k8s_system.agents.infogent_agent import InfogentAgent
        from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

        agent = InfogentAgent()

        # Test navigation with batch/sleep query
        query = "Should users run sleep in batch jobs on Nautilus"
        print(f"Testing navigation for query: {query}")

        sources = agent._navigate_sources(query)
        print(f"Found {len(sources)} sources:")
        for i, source in enumerate(sources):
            print(f"  {i+1}. {source.get('url', 'No URL')} - {source.get('title', 'No Title')}")

        return sources

    except Exception as e:
        print(f"Navigation test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_deep_extraction():
    """Test deep extraction from sources."""
    print("\n" + "="*60)
    print("Testing Deep Extraction")
    print("="*60)

    try:
        from nrp_k8s_system.agents.infogent_agent import InfogentAgent

        agent = InfogentAgent()

        # Test with mock sources (since navigation might not work without proper setup)
        mock_sources = [
            {"url": "https://nrp.ai/documentation/", "title": "NRP Documentation", "source_type": "nrp_docs"},
            {"url": "https://nrp.ai/documentation/running/", "title": "Running Jobs", "source_type": "nrp_docs"}
        ]

        query = "batch jobs sleep runtime optimization"
        print(f"Testing extraction for query: {query}")
        print(f"Using {len(mock_sources)} mock sources")

        templates, knowledge = agent._deep_extract_information(mock_sources, query)

        print(f"Extracted {len(templates)} templates and {len(knowledge)} knowledge chunks")

        for i, template in enumerate(templates):
            print(f"\nTemplate {i+1}:")
            print(f"  Title: {template.title}")
            print(f"  Resource Type: {template.resource_type}")
            print(f"  YAML Content Length: {len(template.yaml_content)}")
            print(f"  Warnings: {len(template.warnings)}")
            print(f"  Cautions: {len(template.cautions)}")

        return templates

    except Exception as e:
        print(f"Deep extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_knowledge_base_storage():
    """Test knowledge base storage directly."""
    print("\n" + "="*60)
    print("Testing Knowledge Base Storage")
    print("="*60)

    try:
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase
        from nrp_k8s_system.agents.deep_extractor_agent import ExtractionTemplate

        kb = EnhancedKnowledgeBase()

        # Check current state
        stats = kb.get_statistics()
        print(f"Current KB stats: {json.dumps(stats, indent=2)}")

        # Create a test template
        test_template = ExtractionTemplate(
            title="Batch Job Sleep Example",
            description="Example showing sleep usage in batch jobs with optimization notes",
            resource_type="job",
            yaml_content="""apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job-example
  namespace: gsoc
spec:
  activeDeadlineSeconds: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: python:3.9
        command: ["python", "-c", "print('Job started'); import time; time.sleep(10); print('Job completed')"]
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1" """,
            usage_context="This example shows a batch job that uses sleep. Consider optimizing for shorter runtime.",
            warnings=["Long-running jobs may be terminated by cluster policies"],
            cautions=["Avoid using sleep for extended periods in batch jobs"],
            notes=["Optimize workloads for shorter execution times"],
            dangers=[],
            examples=["Use sleep(10) instead of sleep(3600) for testing"],
            best_practices=["Design jobs to complete work efficiently rather than using long sleep periods"],
            common_mistakes=["Running indefinite sleep loops in batch jobs"],
            source_url="https://nrp.ai/documentation/jobs/",
            api_version="batch/v1",
            namespace_requirements=["gsoc"],
            resource_requirements={"memory": "4Gi", "cpu": "2"},
            dependencies=[],
            confidence_score=0.9,
            extraction_method="test_creation",
            validation_status="valid"
        )

        # Add template to KB
        template_id = kb.add_template(test_template)
        print(f"Added template with ID: {template_id}")

        # Save KB
        kb.save()
        print("Knowledge base saved")

        # Test search
        results = kb.search_templates("batch job sleep", limit=5)
        print(f"Search found {len(results)} results:")
        for result in results:
            print(f"  - {result.template.template.title} (relevance: {result.relevance_score:.2f})")

        # Test job-related search
        job_results = kb.search_templates("jobs indefinitely runtime", limit=5)
        print(f"Job search found {len(job_results)} results:")
        for result in job_results:
            print(f"  - {result.template.template.title} (relevance: {result.relevance_score:.2f})")

        return True

    except Exception as e:
        print(f"Knowledge base storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_infogent_flow():
    """Test the complete InfoGent flow."""
    print("\n" + "="*60)
    print("Testing Full InfoGent Flow")
    print("="*60)

    try:
        from nrp_k8s_system.agents.infogent_agent import InfogentAgent
        from nrp_k8s_system.agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

        # Set minimal environment for testing
        os.environ.setdefault('NRP_API_KEY', 'test-key')
        os.environ.setdefault('OPENAI_API_KEY', 'test-key')

        agent = InfogentAgent()

        # Create test request
        request = AgentRequest(
            user_input="Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?",
            intent_type=IntentType.QUESTION,
            confidence=ConfidenceLevel.HIGH,
            metadata={}
        )

        print(f"Processing request: {request.user_input}")

        # Test each step individually
        print("\n1. Testing knowledge base search...")
        kb_results = agent._search_knowledge_base(request.user_input)
        print(f"   Found {len(kb_results)} existing templates")

        print("\n2. Testing fresh extraction need...")
        needs_extraction = agent._needs_fresh_extraction(kb_results, request.user_input)
        print(f"   Needs fresh extraction: {needs_extraction}")

        if needs_extraction:
            print("\n3. Testing navigation...")
            sources = agent._navigate_sources(request.user_input)
            print(f"   Found {len(sources)} sources")

            if sources:
                print("\n4. Testing deep extraction...")
                templates, knowledge = agent._deep_extract_information(sources, request.user_input)
                print(f"   Extracted {len(templates)} templates, {len(knowledge)} knowledge chunks")

                print("\n5. Testing knowledge base update...")
                agent._update_knowledge_base(templates)

                print("\n6. Testing refreshed search...")
                kb_results_after = agent._search_knowledge_base(request.user_input)
                print(f"   Found {len(kb_results_after)} templates after update")

        return True

    except Exception as e:
        print(f"Full InfoGent flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Knowledge Base Update Test Suite")
    print("="*60)

    try:
        # Test each component
        print("Phase 1: Testing Navigation...")
        sources = test_navigation_sources()

        print("\nPhase 2: Testing Deep Extraction...")
        templates = test_deep_extraction()

        print("\nPhase 3: Testing Knowledge Base Storage...")
        storage_success = test_knowledge_base_storage()

        print("\nPhase 4: Testing Full InfoGent Flow...")
        flow_success = test_full_infogent_flow()

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Navigation: {'✓' if sources else '✗'} ({len(sources) if sources else 0} sources)")
        print(f"Extraction: {'✓' if templates else '✗'} ({len(templates) if templates else 0} templates)")
        print(f"Storage: {'✓' if storage_success else '✗'}")
        print(f"Full Flow: {'✓' if flow_success else '✗'}")

    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()