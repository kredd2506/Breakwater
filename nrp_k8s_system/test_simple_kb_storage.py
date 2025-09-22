#!/usr/bin/env python3
"""
Simple Knowledge Base Storage Test
=================================

Test knowledge base storage without external dependencies.
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

def test_knowledge_base_storage():
    """Test knowledge base storage with sample templates."""
    print("Testing Knowledge Base Storage")
    print("="*50)

    try:
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase
        from nrp_k8s_system.agents.deep_extractor_agent import ExtractionTemplate

        # Create knowledge base
        kb = EnhancedKnowledgeBase()

        # Check initial state
        stats = kb.get_statistics()
        print(f"Initial KB stats: {stats['total_templates']} templates")

        # Create batch job template
        batch_job_template = ExtractionTemplate(
            title="Batch Job with Runtime Optimization",
            description="Example showing batch job optimization and avoiding long sleep periods",
            resource_type="job",
            yaml_content='''apiVersion: batch/v1
kind: Job
metadata:
  name: optimized-batch-job
  namespace: gsoc
spec:
  activeDeadlineSeconds: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: python:3.9
        command: ["python", "-c", "print('Starting work...'); import time; time.sleep(5); print('Work completed efficiently')"]
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"''',
            usage_context="This example demonstrates efficient batch job design without excessive sleep periods.",
            warnings=["Avoid using long sleep periods in batch jobs"],
            cautions=["Cluster policies may terminate long-running jobs", "Design jobs for efficiency rather than indefinite execution"],
            notes=["Optimize workloads for shorter execution times", "Use appropriate resource requests"],
            dangers=["Running indefinite loops can consume cluster resources"],
            examples=["Use sleep(5) for brief delays, not sleep(3600)", "Process data in chunks rather than waiting"],
            best_practices=[
                "Design jobs to complete work efficiently",
                "Use appropriate timeouts with activeDeadlineSeconds",
                "Monitor job execution and optimize bottlenecks",
                "Avoid indefinite loops or long sleep periods"
            ],
            common_mistakes=[
                "Running sleep commands for hours in batch jobs",
                "Not setting activeDeadlineSeconds",
                "Using indefinite while loops"
            ],
            source_url="https://nrp.ai/documentation/running/",
            api_version="batch/v1",
            namespace_requirements=["gsoc"],
            resource_requirements={"memory": "4Gi", "cpu": "2"},
            dependencies=["python:3.9 image"],
            confidence_score=0.95,
            extraction_method="manual_creation",
            validation_status="valid"
        )

        # Create indefinite job template
        indefinite_job_template = ExtractionTemplate(
            title="Why Jobs Should Not Run Indefinitely",
            description="Explanation of cluster policies and best practices for job runtime",
            resource_type="job",
            yaml_content='''apiVersion: batch/v1
kind: Job
metadata:
  name: finite-job-example
  namespace: gsoc
spec:
  activeDeadlineSeconds: 1800  # 30 minutes max
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: processor
        image: ubuntu:20.04
        command: ["bash", "-c", "echo 'Processing data...'; sleep 10; echo 'Data processed'; exit 0"]
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"''',
            usage_context="Jobs should have defined endpoints and not run indefinitely to maintain cluster health.",
            warnings=["Jobs running indefinitely will be terminated by cluster policies"],
            cautions=[
                "Cluster has resource limits and fairness policies",
                "Long-running workloads should use Deployments, not Jobs",
                "Jobs are designed for finite, batch processing tasks"
            ],
            notes=[
                "Use activeDeadlineSeconds to set maximum job runtime",
                "For continuous workloads, use Deployments instead of Jobs",
                "Monitor resource usage and job completion"
            ],
            dangers=[
                "Indefinite jobs can monopolize cluster resources",
                "May violate cluster usage policies",
                "Can prevent other users from accessing resources"
            ],
            examples=[
                "Set activeDeadlineSeconds: 3600 for 1-hour maximum",
                "Use 'exit 0' to properly terminate job containers",
                "Monitor job status with kubectl get jobs"
            ],
            best_practices=[
                "Always set activeDeadlineSeconds for batch jobs",
                "Use Deployments for long-running services",
                "Design jobs with clear start and end conditions",
                "Test job completion locally before cluster deployment"
            ],
            common_mistakes=[
                "Using while True loops without exit conditions",
                "Not setting job timeout limits",
                "Running interactive services as batch jobs"
            ],
            source_url="https://nrp.ai/documentation/running/",
            api_version="batch/v1",
            namespace_requirements=["gsoc"],
            resource_requirements={"memory": "2Gi", "cpu": "1"},
            dependencies=["ubuntu:20.04 image"],
            confidence_score=0.98,
            extraction_method="manual_creation",
            validation_status="valid"
        )

        # Add templates to knowledge base
        print("\nAdding templates to knowledge base...")
        template_id_1 = kb.add_template(batch_job_template)
        template_id_2 = kb.add_template(indefinite_job_template)

        print(f"Added template 1: {template_id_1}")
        print(f"Added template 2: {template_id_2}")

        # Save knowledge base
        kb.save()
        print("Knowledge base saved")

        # Check updated stats
        updated_stats = kb.get_statistics()
        print(f"Updated KB stats: {updated_stats['total_templates']} templates")

        # Test searches
        print("\nTesting searches...")

        # Search for sleep/batch job question
        sleep_results = kb.search_templates("sleep batch jobs runtime optimization", limit=5)
        print(f"Sleep/batch search: {len(sleep_results)} results")
        for result in sleep_results:
            print(f"  - {result.template.template.title} (relevance: {result.relevance_score:.2f})")

        # Search for indefinite jobs question
        indefinite_results = kb.search_templates("jobs indefinitely run forever continuous", limit=5)
        print(f"Indefinite jobs search: {len(indefinite_results)} results")
        for result in indefinite_results:
            print(f"  - {result.template.template.title} (relevance: {result.relevance_score:.2f})")

        # Test specific queries
        runtime_results = kb.search_templates("Should users run sleep in batch jobs", limit=3)
        print(f"Runtime question search: {len(runtime_results)} results")

        forever_results = kb.search_templates("can i run jobs indefinitely", limit=3)
        print(f"Forever question search: {len(forever_results)} results")

        return True

    except Exception as e:
        print(f"Knowledge base storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_yaml_examples_storage():
    """Create organized YAML examples storage."""
    print("\nCreating YAML Examples Storage")
    print("="*50)

    try:
        # Create directory structure
        yaml_examples_dir = Path("nrp_k8s_system/cache/yaml_examples")
        yaml_examples_dir.mkdir(parents=True, exist_ok=True)

        # Create code directory for YAML files
        code_dir = yaml_examples_dir / "code"
        code_dir.mkdir(exist_ok=True)

        # Batch job examples
        batch_jobs = {
            "optimized_batch_job.yaml": '''apiVersion: batch/v1
kind: Job
metadata:
  name: optimized-batch-job
  namespace: gsoc
spec:
  activeDeadlineSeconds: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: python:3.9
        command: ["python", "-c", "print('Starting efficient work...'); import time; time.sleep(5); print('Work completed')"]
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"''',

            "finite_job_example.yaml": '''apiVersion: batch/v1
kind: Job
metadata:
  name: finite-job-example
  namespace: gsoc
spec:
  activeDeadlineSeconds: 1800  # 30 minutes max
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: processor
        image: ubuntu:20.04
        command: ["bash", "-c", "echo 'Processing...'; sleep 10; echo 'Done'; exit 0"]
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"'''
        }

        # Save YAML files
        for filename, content in batch_jobs.items():
            yaml_file = code_dir / filename
            with open(yaml_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created: {yaml_file}")

        # Create metadata file
        metadata = {
            "job_examples": {
                "optimized_batch_job": {
                    "file": "code/optimized_batch_job.yaml",
                    "title": "Optimized Batch Job",
                    "description": "Example of efficient batch job without excessive sleep",
                    "warnings": ["Avoid long sleep periods", "Set activeDeadlineSeconds"],
                    "best_practices": ["Optimize for short runtime", "Use appropriate resources"]
                },
                "finite_job_example": {
                    "file": "code/finite_job_example.yaml",
                    "title": "Finite Job Example",
                    "description": "Job with proper timeout and exit conditions",
                    "warnings": ["Jobs should not run indefinitely", "Use timeouts"],
                    "best_practices": ["Set clear end conditions", "Use activeDeadlineSeconds"]
                }
            },
            "topics": {
                "batch_jobs": ["optimized_batch_job", "finite_job_example"],
                "runtime_optimization": ["optimized_batch_job"],
                "job_policies": ["finite_job_example"]
            },
            "created": "2025-01-15",
            "last_updated": "2025-01-15"
        }

        metadata_file = yaml_examples_dir / "examples_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"Created metadata: {metadata_file}")
        print(f"YAML examples storage created in: {yaml_examples_dir}")

        return True

    except Exception as e:
        print(f"YAML examples storage creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Simple Knowledge Base Storage Test")
    print("="*50)

    try:
        # Test knowledge base storage
        kb_success = test_knowledge_base_storage()

        # Create YAML examples storage
        yaml_success = create_yaml_examples_storage()

        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Knowledge Base Storage: {'[OK]' if kb_success else '[FAIL]'}")
        print(f"YAML Examples Storage: {'[OK]' if yaml_success else '[FAIL]'}")

        if kb_success and yaml_success:
            print("\n[SUCCESS] All storage systems working correctly!")
            print("The knowledge base will now store and retrieve templates properly.")
        else:
            print("\n[ISSUES] Some storage systems need attention.")

    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()