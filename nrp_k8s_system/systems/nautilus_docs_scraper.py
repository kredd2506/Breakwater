#!/usr/bin/env python3
"""
Nautilus Documentation Scraper
==============================

Scrapes official Nautilus documentation to provide authoritative warnings and policies
for the NRP K8s system. Uses the INFOGENT-based qain.py system for web scraping.
"""

import os
import json
import time
import logging
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import the existing INFOGENT system
from .qain import Controller, Query

logger = logging.getLogger(__name__)

@dataclass
class NautilusPolicy:
    """Represents a policy or warning from Nautilus documentation"""
    topic: str
    policy: str
    warning_level: str  # "critical", "warning", "info"
    details: str
    source_url: str
    violations: List[str]  # What actions violate this policy
    consequences: List[str]  # What happens if violated

@dataclass
class YamlExample:
    """Represents a YAML example from Nautilus documentation"""
    title: str
    description: str
    yaml_content: str
    source_url: str
    category: str  # pod, deployment, service, job, etc.
    tags: List[str]  # gpu, storage, networking, etc.
    resource_type: str  # kubernetes resource type
    complexity: str  # basic, intermediate, advanced

class NautilusDocsCache:
    """Cache for Nautilus documentation and policies"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "nautilus_docs"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.policies_cache = self.cache_dir / "policies.json"
        self.content_cache = self.cache_dir / "content.json"
        self.yaml_cache = self.cache_dir / "yaml_examples.json"
        self.yaml_files_dir = self.cache_dir / "yaml_files"
        self.last_update = self.cache_dir / "last_update.txt"
        
        # Create yaml files directory
        self.yaml_files_dir.mkdir(parents=True, exist_ok=True)
        
        self._policies: List[NautilusPolicy] = []
        self._content: Dict[str, Any] = {}
        self._yaml_examples: List[YamlExample] = []
        self._load_cache()
    
    def _load_cache(self):
        """Load cached policies, content, and YAML examples"""
        try:
            if self.policies_cache.exists():
                with open(self.policies_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._policies = [NautilusPolicy(**p) for p in data]
            
            if self.content_cache.exists():
                with open(self.content_cache, 'r', encoding='utf-8') as f:
                    self._content = json.load(f)
            
            if self.yaml_cache.exists():
                with open(self.yaml_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._yaml_examples = [YamlExample(**y) for y in data]
                    
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save policies, content, and YAML examples to cache"""
        try:
            with open(self.policies_cache, 'w', encoding='utf-8') as f:
                json.dump([p.__dict__ for p in self._policies], f, indent=2)
            
            with open(self.content_cache, 'w', encoding='utf-8') as f:
                json.dump(self._content, f, indent=2)
            
            with open(self.yaml_cache, 'w', encoding='utf-8') as f:
                json.dump([y.__dict__ for y in self._yaml_examples], f, indent=2)
            
            with open(self.last_update, 'w') as f:
                f.write(str(int(time.time())))
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def is_cache_stale(self, max_age_hours: int = 24) -> bool:
        """Check if cache is older than max_age_hours"""
        if not self.last_update.exists():
            return True
        
        try:
            with open(self.last_update, 'r') as f:
                last_update = int(f.read().strip())
            return (time.time() - last_update) > (max_age_hours * 3600)
        except:
            return True
    
    def get_policies_for_topic(self, topic: str) -> List[NautilusPolicy]:
        """Get policies related to a specific topic"""
        topic_lower = topic.lower()
        return [
            p for p in self._policies 
            if topic_lower in p.topic.lower() or 
            any(topic_lower in v.lower() for v in p.violations)
        ]
    
    def get_critical_warnings(self) -> List[NautilusPolicy]:
        """Get all critical warnings"""
        return [p for p in self._policies if p.warning_level == "critical"]
    
    def add_policy(self, policy: NautilusPolicy):
        """Add a new policy to the cache"""
        self._policies.append(policy)
    
    def get_yaml_examples(self, category: str = None, resource_type: str = None) -> List[YamlExample]:
        """Get YAML examples, optionally filtered by category or resource type"""
        examples = self._yaml_examples
        if category:
            examples = [e for e in examples if e.category.lower() == category.lower()]
        if resource_type:
            examples = [e for e in examples if e.resource_type.lower() == resource_type.lower()]
        return examples
    
    def add_yaml_example(self, example: YamlExample):
        """Add a new YAML example to the cache"""
        self._yaml_examples.append(example)
        # Save YAML content to individual file
        safe_title = re.sub(r'[^\w\-_.]', '_', example.title)
        yaml_file = self.yaml_files_dir / f"{example.category}_{safe_title}.yaml"
        try:
            with open(yaml_file, 'w', encoding='utf-8') as f:
                f.write(f"# {example.title}\n")
                f.write(f"# Source: {example.source_url}\n")
                f.write(f"# Description: {example.description}\n")
                f.write(f"# Category: {example.category}\n")
                f.write(f"# Resource Type: {example.resource_type}\n")
                f.write(f"# Tags: {', '.join(example.tags)}\n")
                f.write(f"# Complexity: {example.complexity}\n")
                f.write("\n")
                f.write(example.yaml_content)
        except Exception as e:
            logger.warning(f"Failed to save YAML file {yaml_file}: {e}")
    
    def get_content_for_query(self, query: str) -> Optional[str]:
        """Get cached content for a specific query"""
        return self._content.get(query.lower())
    
    def add_content(self, query: str, content: str):
        """Add content to cache"""
        self._content[query.lower()] = content
    
    def save(self):
        """Save cache to disk"""
        self._save_cache()

class NautilusDocsScraper:
    """Scraper for Nautilus documentation using INFOGENT system"""
    
    # Known Nautilus documentation URLs and policies
    NAUTILUS_URLS = [
        "https://nrp-nautilus.io/docs/",
        "https://nrp-nautilus.io/docs/policies/",
        "https://nrp-nautilus.io/docs/usage/",
        "https://nrp-nautilus.io/docs/kubernetes/",
        "https://docs.nautilus.optiputer.net/",
        "https://ucsd-prp.github.io/",
    ]
    
    # Critical policies to scrape
    CRITICAL_TOPICS = [
        "sleep commands ban account suspension",
        "resource abuse GPU monitoring ban",
        "batch job policies violations",
        "job time limits termination", 
        "fair usage policy enforcement",
        "account suspension penalties",
        "resource hogging monitoring",
        "inappropriate usage ban",
        "namespace quotas limits",
        "GPU allocation policies"
    ]
    
    def __init__(self, cache: NautilusDocsCache = None):
        self.cache = cache or NautilusDocsCache()
        self.controller = Controller()
    
    def scrape_critical_policies(self, force_refresh: bool = False) -> List[NautilusPolicy]:
        """Scrape critical Nautilus policies"""
        if not force_refresh and not self.cache.is_cache_stale():
            logger.info("Using cached policies")
            return self.cache.get_critical_warnings()
        
        logger.info("Scraping Nautilus policies...")
        
        for topic in self.CRITICAL_TOPICS:
            try:
                self._scrape_topic(topic)
                time.sleep(2)  # Be polite to servers
            except Exception as e:
                logger.warning(f"Failed to scrape topic '{topic}': {e}")
        
        # Add hardcoded critical policies based on known Nautilus behavior
        self._add_hardcoded_policies()
        
        self.cache.save()
        return self.cache.get_critical_warnings()
    
    def scrape_yaml_examples(self, force_refresh: bool = False) -> List[YamlExample]:
        """Scrape YAML examples from Nautilus documentation"""
        if not force_refresh and not self.cache.is_cache_stale():
            logger.info("Using cached YAML examples")
            return self.cache.get_yaml_examples()
        
        logger.info("Scraping Nautilus YAML examples...")
        
        # YAML-focused search queries
        yaml_topics = [
            "kubernetes pod yaml example site:nrp-nautilus.io",
            "kubernetes deployment yaml example site:nrp-nautilus.io", 
            "kubernetes job yaml gpu example site:nrp-nautilus.io",
            "kubernetes service yaml example site:nrp-nautilus.io",
            "kubernetes pvc storage yaml example site:nrp-nautilus.io",
            "kubernetes configmap yaml example site:nrp-nautilus.io",
            "kubernetes secret yaml example site:nrp-nautilus.io",
            "kubernetes ingress yaml example site:nrp-nautilus.io",
            "batch job yaml gpu example site:docs.nautilus.optiputer.net",
            "persistent volume yaml example site:ucsd-prp.github.io"
        ]
        
        for topic in yaml_topics:
            try:
                self._scrape_yaml_topic(topic)
                time.sleep(2)  # Be polite to servers
            except Exception as e:
                logger.warning(f"Failed to scrape YAML topic '{topic}': {e}")
        
        # Add hardcoded YAML examples
        self._add_hardcoded_yaml_examples()
        
        self.cache.save()
        return self.cache.get_yaml_examples()
    
    def _scrape_topic(self, topic: str):
        """Scrape documentation for a specific topic"""
        # Create focused query for Nautilus docs
        query_text = f"{topic} site:nrp-nautilus.io OR site:docs.nautilus.optiputer.net OR site:ucsd-prp.github.io"
        
        query = Query(
            id=f"nautilus-{topic}",
            text=query_text,
            steps=5,
            time_budget_s=60,
            domains_allow=["nrp-nautilus.io", "docs.nautilus.optiputer.net", "ucsd-prp.github.io"]
        )
        
        try:
            result = self.controller.run(query)
            
            # Extract policies from the scraped content
            if result.get("answer"):
                content = self._extract_policy_content(result, topic)
                if content:
                    self.cache.add_content(topic, content)
                    policy = self._parse_policy(topic, content, result.get("sources", []))
                    if policy:
                        self.cache.add_policy(policy)
                        
        except Exception as e:
            logger.warning(f"Failed to scrape topic '{topic}': {e}")
    
    def _scrape_yaml_topic(self, topic: str):
        """Scrape documentation for YAML examples on a specific topic"""
        query = Query(
            id=f"yaml-{topic}",
            text=topic,
            steps=5,
            time_budget_s=60,
            domains_allow=["nrp-nautilus.io", "docs.nautilus.optiputer.net", "ucsd-prp.github.io"]
        )
        
        try:
            result = self.controller.run(query)
            
            # Extract YAML examples from the scraped content
            if result.get("answer"):
                content = self._extract_policy_content(result, topic)
                if content:
                    yaml_examples = self._extract_yaml_examples(content, topic, result.get("sources", []))
                    for example in yaml_examples:
                        self.cache.add_yaml_example(example)
                        
        except Exception as e:
            logger.warning(f"Failed to scrape YAML topic '{topic}': {e}")
    
    def _extract_policy_content(self, result: Dict, topic: str) -> Optional[str]:
        """Extract relevant policy content from scrape result"""
        content_parts = []
        
        # Get content from answer snippets
        for slot_content in result.get("answer", {}).values():
            for snippet_data in slot_content:
                if snippet_data.get("snippet"):
                    content_parts.append(snippet_data["snippet"])
        
        if content_parts:
            return "\n".join(content_parts)
        return None
    
    def _parse_policy(self, topic: str, content: str, sources: List[Dict]) -> Optional[NautilusPolicy]:
        """Parse policy information from scraped content"""
        content_lower = content.lower()
        
        # Determine warning level
        warning_level = "info"
        if any(term in content_lower for term in ["ban", "suspend", "termination", "violation"]):
            warning_level = "critical"
        elif any(term in content_lower for term in ["warning", "caution", "important"]):
            warning_level = "warning"
        
        # Extract violations and consequences
        violations = []
        consequences = []
        
        # Common violation patterns
        if "sleep" in topic.lower():
            violations.extend([
                "Using sleep commands in batch jobs",
                "Holding GPU resources while idle",
                "Running jobs that wait instead of compute"
            ])
            consequences.extend([
                "Account suspension",
                "Account banning",
                "Loss of cluster access"
            ])
        
        if "resource abuse" in topic.lower():
            violations.extend([
                "Excessive resource requests",
                "Holding resources without utilization",
                "Resource hogging"
            ])
            consequences.extend([
                "Account restrictions",
                "Job termination",
                "Permanent ban"
            ])
        
        # Get source URL
        source_url = sources[0]["url"] if sources else "https://nrp-nautilus.io/docs/"
        
        return NautilusPolicy(
            topic=topic,
            policy=content,
            warning_level=warning_level,
            details=content,
            source_url=source_url,
            violations=violations,
            consequences=consequences
        )
    
    def _add_hardcoded_policies(self):
        """Add well-known Nautilus policies"""
        # Critical sleep command policy
        sleep_policy = NautilusPolicy(
            topic="sleep commands in batch jobs",
            policy="Using sleep commands in batch jobs while holding GPU resources is strictly prohibited and monitored.",
            warning_level="critical",
            details="Nautilus actively monitors for resource abuse. Jobs that use sleep commands while allocated expensive resources like GPUs are considered wasteful and violate fair usage policies.",
            source_url="https://nrp-nautilus.io/docs/policies/",
            violations=[
                "Using sleep commands in Kubernetes Jobs",
                "Holding GPU resources while idle",
                "Running waiting loops instead of computation",
                "Batch jobs with minimal CPU/GPU utilization"
            ],
            consequences=[
                "Immediate account suspension",
                "Permanent account banning",
                "Loss of cluster access",
                "Investigation by NRP administrators"
            ]
        )
        self.cache.add_policy(sleep_policy)
        
        # Resource abuse policy
        resource_policy = NautilusPolicy(
            topic="resource abuse and monitoring",
            policy="All resource usage is monitored. Inappropriate usage patterns are automatically detected and penalized.",
            warning_level="critical", 
            details="Nautilus uses automated monitoring to detect resource abuse patterns including idle GPU usage, excessive resource requests, and jobs that don't utilize allocated resources.",
            source_url="https://nrp-nautilus.io/docs/usage/",
            violations=[
                "Requesting more resources than needed",
                "Holding resources without active computation",
                "Running jobs longer than necessary",
                "GPU allocation without GPU-accelerated workloads"
            ],
            consequences=[
                "Account restrictions",
                "Job termination",
                "Resource quota reduction",
                "Account suspension for repeat offenses"
            ]
        )
        self.cache.add_policy(resource_policy)
        
        # Time limits policy
        time_policy = NautilusPolicy(
            topic="job time limits and termination",
            policy="Jobs must complete within reasonable time limits. Long-running jobs without progress are terminated.",
            warning_level="warning",
            details="Nautilus enforces time limits on jobs to ensure fair resource sharing. Jobs should set activeDeadlineSeconds and complete work efficiently.",
            source_url="https://nrp-nautilus.io/docs/kubernetes/",
            violations=[
                "Jobs without time limits",
                "Excessively long-running jobs",
                "Jobs that appear stuck or inactive"
            ],
            consequences=[
                "Automatic job termination",
                "Resource quota adjustments",
                "Account review for repeated violations"
            ]
        )
        self.cache.add_policy(time_policy)
    
    def _extract_yaml_examples(self, content: str, topic: str, sources: List[Dict]) -> List[YamlExample]:
        """Extract YAML examples from scraped content"""
        examples = []
        
        # Look for YAML code blocks (```yaml, ```yml, or triple backticks followed by yaml content)
        yaml_patterns = [
            r'```yaml\s*\n(.*?)```',
            r'```yml\s*\n(.*?)```', 
            r'```\s*\n(apiVersion:.*?)```',
            r'```\s*\n(kind:.*?)```'
        ]
        
        for pattern in yaml_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                yaml_content = match.group(1).strip()
                
                # Validate it's actually YAML
                if self._is_valid_kubernetes_yaml(yaml_content):
                    example = self._create_yaml_example(yaml_content, topic, sources)
                    if example:
                        examples.append(example)
        
        return examples
    
    def _is_valid_kubernetes_yaml(self, content: str) -> bool:
        """Check if content is valid Kubernetes YAML"""
        try:
            # Parse YAML
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return False
            
            # Check for Kubernetes resource markers
            required_fields = ['apiVersion', 'kind']
            return all(field in data for field in required_fields)
        except:
            return False
    
    def _create_yaml_example(self, yaml_content: str, topic: str, sources: List[Dict]) -> Optional[YamlExample]:
        """Create a YamlExample from extracted YAML content"""
        try:
            data = yaml.safe_load(yaml_content)
            resource_type = data.get('kind', 'Unknown')
            
            # Extract metadata name as title if available
            title = data.get('metadata', {}).get('name', f"{resource_type} Example")
            
            # Determine category based on resource type
            category = self._categorize_resource(resource_type)
            
            # Extract tags based on content analysis
            tags = self._extract_tags_from_yaml(yaml_content, data)
            
            # Determine complexity
            complexity = self._assess_complexity(data)
            
            # Create description
            description = self._generate_description(data, topic)
            
            # Get source URL
            source_url = sources[0]["url"] if sources else "https://nrp-nautilus.io/docs/"
            
            return YamlExample(
                title=title,
                description=description,
                yaml_content=yaml_content,
                source_url=source_url,
                category=category,
                tags=tags,
                resource_type=resource_type.lower(),
                complexity=complexity
            )
        except Exception as e:
            logger.warning(f"Failed to create YAML example: {e}")
            return None
    
    def _categorize_resource(self, resource_type: str) -> str:
        """Categorize Kubernetes resource type"""
        category_map = {
            'Pod': 'workload',
            'Deployment': 'workload', 
            'Job': 'workload',
            'CronJob': 'workload',
            'Service': 'networking',
            'Ingress': 'networking',
            'PersistentVolumeClaim': 'storage',
            'PersistentVolume': 'storage',
            'StorageClass': 'storage',
            'ConfigMap': 'config',
            'Secret': 'config',
            'ServiceAccount': 'rbac',
            'Role': 'rbac',
            'RoleBinding': 'rbac'
        }
        return category_map.get(resource_type, 'other')
    
    def _extract_tags_from_yaml(self, yaml_content: str, data: Dict) -> List[str]:
        """Extract relevant tags from YAML content"""
        tags = []
        content_lower = yaml_content.lower()
        
        # GPU-related
        if 'nvidia.com/gpu' in content_lower or 'nvidia.com/a100' in content_lower:
            tags.append('gpu')
        
        # Storage-related
        if any(term in content_lower for term in ['persistentvolume', 'pvc', 'storage']):
            tags.append('storage')
        
        # Networking
        if any(term in content_lower for term in ['service', 'ingress', 'loadbalancer']):
            tags.append('networking')
        
        # Resource limits
        if 'resources' in data.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [{}])[0] if data.get('spec', {}).get('template') else 'resources' in data.get('spec', {}).get('containers', [{}])[0] if data.get('spec', {}).get('containers') else False:
            tags.append('resources')
        
        # Batch/Job
        if data.get('kind') in ['Job', 'CronJob']:
            tags.append('batch')
        
        # Namespace
        if 'namespace' in data.get('metadata', {}):
            tags.append('namespaced')
            
        return tags
    
    def _assess_complexity(self, data: Dict) -> str:
        """Assess the complexity of a YAML resource"""
        complexity_score = 0
        
        # Count containers
        containers = []
        if data.get('spec', {}).get('containers'):
            containers = data['spec']['containers']
        elif data.get('spec', {}).get('template', {}).get('spec', {}).get('containers'):
            containers = data['spec']['template']['spec']['containers']
        
        if len(containers) > 1:
            complexity_score += 1
        
        # Check for advanced features
        advanced_features = ['volumes', 'volumeMounts', 'env', 'resources', 'securityContext']
        for container in containers:
            for feature in advanced_features:
                if feature in container:
                    complexity_score += 1
        
        # Check for networking/storage
        if data.get('spec', {}).get('selector') or data.get('spec', {}).get('ports'):
            complexity_score += 1
        
        if complexity_score == 0:
            return 'basic'
        elif complexity_score <= 3:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _generate_description(self, data: Dict, topic: str) -> str:
        """Generate a description for the YAML example"""
        resource_type = data.get('kind', 'Resource')
        name = data.get('metadata', {}).get('name', 'unnamed')
        
        descriptions = {
            'Pod': f"Kubernetes Pod '{name}' configuration",
            'Deployment': f"Kubernetes Deployment '{name}' configuration", 
            'Job': f"Kubernetes Job '{name}' for batch processing",
            'Service': f"Kubernetes Service '{name}' for networking",
            'PersistentVolumeClaim': f"Persistent Volume Claim '{name}' for storage"
        }
        
        base_desc = descriptions.get(resource_type, f"{resource_type} '{name}' configuration")
        
        # Add context from topic
        if 'gpu' in topic.lower():
            base_desc += " with GPU resources"
        elif 'storage' in topic.lower():
            base_desc += " with persistent storage"
        elif 'batch' in topic.lower():
            base_desc += " for batch processing"
            
        return base_desc
    
    def _add_hardcoded_yaml_examples(self):
        """Add well-known YAML examples for common Nautilus use cases"""
        
        # GPU Pod Example
        gpu_pod_yaml = """apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-example
  namespace: gsoc
spec:
  containers:
  - name: pytorch-container
    image: pytorch/pytorch:latest
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: "8Gi"
        cpu: "4"
      requests:
        nvidia.com/gpu: 1
        memory: "4Gi"
        cpu: "2"
    command: ["python", "-c", "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"]
  restartPolicy: Never"""
        
        gpu_example = YamlExample(
            title="GPU Pod Example",
            description="Kubernetes Pod with A100 GPU allocation for PyTorch workloads",
            yaml_content=gpu_pod_yaml,
            source_url="https://nrp-nautilus.io/docs/kubernetes/",
            category="workload",
            tags=["gpu", "pytorch", "resources"],
            resource_type="pod",
            complexity="intermediate"
        )
        self.cache.add_yaml_example(gpu_example)
        
        # Batch Job Example
        batch_job_yaml = """apiVersion: batch/v1
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
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "8Gi"
            cpu: "4"
          requests:
            nvidia.com/gpu: 1
            memory: "4Gi"
            cpu: "2"
        command: ["python", "-c", "print('Starting batch job'); import time; time.sleep(10); print('Job completed successfully')"]"""
        
        job_example = YamlExample(
            title="Batch Job with GPU",
            description="Kubernetes Job with GPU resources and time limits for batch processing",
            yaml_content=batch_job_yaml,
            source_url="https://nrp-nautilus.io/docs/kubernetes/",
            category="workload",
            tags=["batch", "job", "gpu", "resources"],
            resource_type="job",
            complexity="intermediate"
        )
        self.cache.add_yaml_example(job_example)
        
        # PVC Storage Example
        pvc_yaml = """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc-example
  namespace: gsoc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: rook-cephfs"""
        
        pvc_example = YamlExample(
            title="Persistent Volume Claim",
            description="PVC for persistent data storage with CephFS",
            yaml_content=pvc_yaml,
            source_url="https://nrp-nautilus.io/docs/storage/",
            category="storage",
            tags=["storage", "pvc", "cephfs"],
            resource_type="persistentvolumeclaim",
            complexity="basic"
        )
        self.cache.add_yaml_example(pvc_example)

def get_policies_for_topic(topic: str) -> List[NautilusPolicy]:
    """Convenience function to get policies for a topic"""
    cache = NautilusDocsCache()
    scraper = NautilusDocsScraper(cache)
    
    # Scrape if cache is stale
    if cache.is_cache_stale():
        scraper.scrape_critical_policies()
    
    return cache.get_policies_for_topic(topic)

def get_critical_warnings() -> List[NautilusPolicy]:
    """Get all critical warnings from Nautilus documentation"""
    cache = NautilusDocsCache()
    scraper = NautilusDocsScraper(cache)
    
    return scraper.scrape_critical_policies()

def get_yaml_examples(category: str = None, resource_type: str = None) -> List[YamlExample]:
    """Get YAML examples from Nautilus documentation"""
    cache = NautilusDocsCache()
    scraper = NautilusDocsScraper(cache)
    
    # Scrape if cache is stale
    if cache.is_cache_stale():
        scraper.scrape_yaml_examples()
    
    return cache.get_yaml_examples(category, resource_type)

def get_yaml_template(resource_type: str, use_case: str = None) -> Optional[str]:
    """Get a YAML template for a specific resource type and use case"""
    examples = get_yaml_examples(resource_type=resource_type)
    
    if not examples:
        return None
    
    # Filter by use case if specified
    if use_case:
        use_case_lower = use_case.lower()
        filtered = [e for e in examples if any(tag in use_case_lower for tag in e.tags)]
        examples = filtered if filtered else examples
    
    # Return the first (most relevant) example
    return examples[0].yaml_content if examples else None

def format_policy_warning(policies: List[NautilusPolicy]) -> str:
    """Format policies into a warning message"""
    if not policies:
        return ""
    
    warnings = []
    for policy in policies:
        if policy.warning_level == "critical":
            warnings.append(f"""
[!] **CRITICAL WARNING - {policy.topic.upper()}**

**Policy**: {policy.policy}

**Violations**: 
{chr(10).join(f'- {v}' for v in policy.violations)}

**Consequences**:
{chr(10).join(f'- {c}' for c in policy.consequences)}

**Source**: {policy.source_url}
""")
        elif policy.warning_level == "warning":
            warnings.append(f"""
[!] **WARNING - {policy.topic.title()}**

{policy.policy}

**Violations**: {', '.join(policy.violations)}
**Consequences**: {', '.join(policy.consequences)}
""")
    
    return "\n".join(warnings)

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Nautilus Documentation Scraper...")
    
    # Test getting policies for sleep commands
    policies = get_policies_for_topic("sleep")
    print(f"\nFound {len(policies)} policies for 'sleep' topic:")
    
    for policy in policies:
        print(f"- {policy.topic} ({policy.warning_level})")
        print(f"  Violations: {len(policy.violations)}")
        print(f"  Consequences: {len(policy.consequences)}")
    
    # Test getting all critical warnings
    critical = get_critical_warnings()
    print(f"\nFound {len(critical)} critical warnings")
    
    # Test formatting
    if policies:
        formatted = format_policy_warning(policies[:1])
        print(f"\nFormatted warning:\n{formatted}")