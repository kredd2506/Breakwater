#!/usr/bin/env python3
"""
Fast Knowledge Base Builder
==========================

Lightweight system for building the knowledge base quickly on first run,
then providing fast responses using pre-built knowledge.

Key principles:
1. Build once, use many times
2. Lightweight extraction focused on key information
3. Fast lookup and retrieval
4. Continuous updates in background
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import requests
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..systems.nrp_search_navigator import NRPSearchNavigator

logger = logging.getLogger(__name__)

@dataclass
class QuickTemplate:
    """Lightweight template for fast knowledge base."""
    id: str
    title: str
    resource_type: str
    yaml_snippet: str
    description: str
    gpu_specific: bool
    warnings: List[str]
    source_url: str
    relevance_keywords: List[str]
    created_at: str

@dataclass
class KnowledgeEntry:
    """Fast lookup knowledge entry."""
    id: str
    content: str
    topic: str
    keywords: Set[str]
    importance: float  # 0.0 to 1.0
    source_url: str
    last_updated: str

class FastKnowledgeBuilder:
    """
    Fast knowledge base builder that creates a comprehensive knowledge base
    on first run, then provides lightning-fast responses.
    """

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "fast_knowledge"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Storage files
        self.templates_file = self.cache_dir / "quick_templates.json"
        self.knowledge_file = self.cache_dir / "knowledge_entries.json"
        self.keywords_index_file = self.cache_dir / "keywords_index.json"
        self.build_status_file = self.cache_dir / "build_status.json"

        # In-memory storage for fast access
        self.templates: Dict[str, QuickTemplate] = {}
        self.knowledge: Dict[str, KnowledgeEntry] = {}
        self.keywords_index: Dict[str, Set[str]] = {}  # keyword -> template_ids

        # Search navigator for finding sources
        self.search_navigator = NRPSearchNavigator()

        # Critical NRP topics to focus on
        self.critical_topics = [
            "A100 GPU", "V100 GPU", "GPU request", "NVIDIA GPU",
            "GPU limits", "GPU quota", "Kubernetes GPU",
            "machine learning", "PyTorch", "TensorFlow",
            "batch jobs", "persistent storage", "PVC",
            "ingress", "networking", "resource limits"
        ]

        # Load existing knowledge if available
        self._load_knowledge_base()

    def is_knowledge_base_built(self) -> bool:
        """Check if knowledge base has been built."""
        if not self.build_status_file.exists():
            return False

        try:
            with open(self.build_status_file, 'r') as f:
                status = json.load(f)
                return status.get('built', False) and status.get('templates_count', 0) > 0
        except:
            return False

    def build_knowledge_base(self, force_rebuild: bool = False) -> bool:
        """
        Build the knowledge base quickly using targeted extraction.

        Returns:
            True if successful, False otherwise
        """
        if not force_rebuild and self.is_knowledge_base_built():
            logger.info("Knowledge base already built, skipping...")
            return True

        logger.info("Building fast knowledge base...")
        start_time = time.time()

        try:
            # Step 1: Get high-priority documentation URLs
            priority_urls = self._get_priority_urls()

            # Step 2: Extract knowledge in parallel (but lightweight)
            templates, knowledge = self._extract_knowledge_parallel(priority_urls)

            # Step 3: Build keyword indices for fast lookup
            self._build_keyword_indices(templates, knowledge)

            # Step 4: Save everything
            self._save_knowledge_base(templates, knowledge)

            # Step 5: Update build status
            build_time = time.time() - start_time
            self._update_build_status(len(templates), len(knowledge), build_time)

            logger.info(f"Knowledge base built: {len(templates)} templates, {len(knowledge)} entries in {build_time:.1f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}")
            return False

    def _get_priority_urls(self) -> List[str]:
        """Get priority URLs to extract from using targeted search."""
        priority_urls = set()

        # Use search to find the most relevant pages
        for topic in self.critical_topics:
            try:
                results = self.search_navigator.search_nrp_documentation(topic, limit=3)
                for result in results:
                    if 'nrp.ai/documentation' in result['url']:
                        priority_urls.add(result['url'])
            except Exception as e:
                logger.warning(f"Search failed for topic '{topic}': {e}")

        # Add known important URLs
        known_important = [
            "https://nrp.ai/documentation/userdocs/gpu/",
            "https://nrp.ai/documentation/userdocs/kubernetes/",
            "https://nrp.ai/documentation/userdocs/storage/",
            "https://nrp.ai/documentation/userdocs/",
            "https://nrp.ai/documentation/"
        ]

        priority_urls.update(known_important)
        return list(priority_urls)

    def _extract_knowledge_parallel(self, urls: List[str]) -> tuple:
        """Extract knowledge from URLs in parallel but lightweight."""
        templates = {}
        knowledge = {}

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit extraction tasks
            future_to_url = {
                executor.submit(self._extract_from_single_url, url): url
                for url in urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    url_templates, url_knowledge = future.result(timeout=30)
                    templates.update(url_templates)
                    knowledge.update(url_knowledge)
                    logger.info(f"Extracted from {url}: {len(url_templates)} templates, {len(url_knowledge)} entries")
                except Exception as e:
                    logger.warning(f"Failed to extract from {url}: {e}")

        return templates, knowledge

    def _extract_from_single_url(self, url: str) -> tuple:
        """Lightweight extraction from a single URL."""
        templates = {}
        knowledge = {}

        try:
            # Fetch content
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Quick extraction of YAML examples
            yaml_examples = self._extract_yaml_examples(soup, url)
            for yaml_ex in yaml_examples:
                template_id = f"tmpl_{len(templates)}_{int(time.time())}"
                templates[template_id] = yaml_ex

            # Quick extraction of important text sections
            text_knowledge = self._extract_text_knowledge(soup, url)
            for knowledge_entry in text_knowledge:
                entry_id = f"know_{len(knowledge)}_{int(time.time())}"
                knowledge[entry_id] = knowledge_entry

        except Exception as e:
            logger.warning(f"Extraction failed for {url}: {e}")

        return templates, knowledge

    def _extract_yaml_examples(self, soup, url: str) -> List[QuickTemplate]:
        """Extract YAML examples quickly."""
        templates = []

        # Find code blocks
        code_blocks = soup.find_all(['pre', 'code'])

        for block in code_blocks:
            try:
                code_content = block.get_text()

                # Check if it's Kubernetes YAML
                if self._is_kubernetes_yaml(code_content):
                    # Get surrounding context for title and description
                    title = self._get_context_title(block, soup)
                    description = self._get_context_description(block)

                    # Determine if GPU-specific
                    gpu_specific = self._is_gpu_related(code_content, title, description)

                    # Extract warnings from surrounding context
                    warnings = self._extract_nearby_warnings(block)

                    # Generate keywords for fast lookup
                    keywords = self._generate_keywords(title, description, code_content)

                    # Determine resource type
                    resource_type = self._determine_resource_type(code_content)

                    template = QuickTemplate(
                        id="",  # Will be set by caller
                        title=title,
                        resource_type=resource_type,
                        yaml_snippet=code_content[:500],  # Limit size
                        description=description[:200],
                        gpu_specific=gpu_specific,
                        warnings=warnings,
                        source_url=url,
                        relevance_keywords=keywords,
                        created_at=str(int(time.time()))
                    )

                    templates.append(template)

            except Exception as e:
                logger.warning(f"Failed to process code block: {e}")
                continue

        return templates

    def _extract_text_knowledge(self, soup, url: str) -> List[KnowledgeEntry]:
        """Extract important text knowledge quickly."""
        knowledge_entries = []

        # Find important sections
        important_selectors = [
            'h1', 'h2', 'h3',  # Headings
            '.warning', '.caution', '.note',  # Warnings
            'blockquote',  # Important quotes
            '.important', '.highlight'  # Highlighted content
        ]

        for selector in important_selectors:
            elements = soup.select(selector)

            for element in elements:
                try:
                    text = element.get_text(strip=True)

                    if len(text) < 20 or len(text) > 500:  # Skip too short/long
                        continue

                    # Classify topic
                    topic = self._classify_text_topic(text)

                    # Extract keywords
                    keywords = set(self._generate_keywords_from_text(text))

                    # Calculate importance
                    importance = self._calculate_text_importance(text, element.name)

                    # Only keep important content
                    if importance > 0.3:
                        entry = KnowledgeEntry(
                            id="",  # Will be set by caller
                            content=text,
                            topic=topic,
                            keywords=keywords,
                            importance=importance,
                            source_url=url,
                            last_updated=str(int(time.time()))
                        )

                        knowledge_entries.append(entry)

                except Exception as e:
                    logger.warning(f"Failed to process text element: {e}")
                    continue

        return knowledge_entries

    def _is_kubernetes_yaml(self, content: str) -> bool:
        """Quick check if content is Kubernetes YAML."""
        content_lower = content.lower()
        return ('apiversion:' in content_lower and 'kind:' in content_lower)

    def _is_gpu_related(self, yaml_content: str, title: str, description: str) -> bool:
        """Check if content is GPU-related."""
        all_text = f"{yaml_content} {title} {description}".lower()
        gpu_indicators = ['gpu', 'nvidia', 'cuda', 'a100', 'v100', 'tesla']
        return any(indicator in all_text for indicator in gpu_indicators)

    def _get_context_title(self, element, soup) -> str:
        """Get title from context."""
        # Look for nearby heading
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            try:
                if abs(heading.sourceline - element.sourceline) < 10:
                    return heading.get_text(strip=True)
            except:
                pass

        return "Kubernetes Configuration"

    def _get_context_description(self, element) -> str:
        """Get description from surrounding context."""
        # Look for preceding paragraph
        prev_elem = element.find_previous(['p', 'div'])
        if prev_elem:
            return prev_elem.get_text(strip=True)[:150]
        return ""

    def _extract_nearby_warnings(self, element) -> List[str]:
        """Extract warnings near the element."""
        warnings = []

        # Look for warning elements nearby
        nearby_elements = []

        # Get siblings and nearby elements
        current = element
        for _ in range(5):  # Check 5 elements before and after
            current = current.find_previous()
            if current:
                nearby_elements.append(current)
            else:
                break

        current = element
        for _ in range(5):
            current = current.find_next()
            if current:
                nearby_elements.append(current)
            else:
                break

        # Check for warning patterns
        for elem in nearby_elements:
            try:
                text = elem.get_text().lower()
                if any(warning in text for warning in ['warning', 'caution', 'danger', 'important']):
                    warning_text = elem.get_text(strip=True)
                    if len(warning_text) < 200:  # Keep warnings concise
                        warnings.append(warning_text)
            except:
                pass

        return warnings[:3]  # Limit to 3 warnings

    def _generate_keywords(self, title: str, description: str, yaml_content: str) -> List[str]:
        """Generate keywords for fast lookup."""
        all_text = f"{title} {description} {yaml_content}".lower()

        # Important keywords to extract
        important_keywords = [
            'a100', 'v100', 'gpu', 'nvidia', 'cuda',
            'pod', 'deployment', 'job', 'service',
            'storage', 'pvc', 'volume',
            'limit', 'request', 'resource',
            'kubernetes', 'k8s'
        ]

        found_keywords = []
        for keyword in important_keywords:
            if keyword in all_text:
                found_keywords.append(keyword)

        return found_keywords

    def _determine_resource_type(self, yaml_content: str) -> str:
        """Determine Kubernetes resource type."""
        content_lower = yaml_content.lower()

        if 'kind: pod' in content_lower:
            return 'pod'
        elif 'kind: deployment' in content_lower:
            return 'deployment'
        elif 'kind: job' in content_lower:
            return 'job'
        elif 'kind: service' in content_lower:
            return 'service'
        elif 'persistentvolumeclaim' in content_lower:
            return 'pvc'
        else:
            return 'unknown'

    def _classify_text_topic(self, text: str) -> str:
        """Classify text topic."""
        text_lower = text.lower()

        if any(gpu_term in text_lower for gpu_term in ['gpu', 'nvidia', 'cuda', 'a100', 'v100']):
            return 'gpu'
        elif any(storage_term in text_lower for storage_term in ['storage', 'volume', 'pvc']):
            return 'storage'
        elif any(job_term in text_lower for job_term in ['job', 'batch', 'workload']):
            return 'jobs'
        elif any(net_term in text_lower for net_term in ['network', 'ingress', 'service']):
            return 'networking'
        else:
            return 'general'

    def _generate_keywords_from_text(self, text: str) -> List[str]:
        """Generate keywords from text."""
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter for important words
        important_words = []
        for word in words:
            if (len(word) >= 3 and
                word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all'] and
                any(important in word for important in ['gpu', 'kubernetes', 'pod', 'job', 'storage'])):
                important_words.append(word)

        return list(set(important_words))

    def _calculate_text_importance(self, text: str, element_type: str) -> float:
        """Calculate importance of text."""
        importance = 0.0

        # Base importance by element type
        if element_type in ['h1', 'h2']:
            importance += 0.8
        elif element_type == 'h3':
            importance += 0.6
        elif element_type in ['.warning', '.caution']:
            importance += 0.9
        else:
            importance += 0.4

        # Boost for GPU content
        if any(gpu_term in text.lower() for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
            importance += 0.3

        # Boost for warning content
        if any(warning in text.lower() for warning in ['warning', 'caution', 'important']):
            importance += 0.2

        return min(1.0, importance)

    def _build_keyword_indices(self, templates: Dict[str, QuickTemplate], knowledge: Dict[str, KnowledgeEntry]):
        """Build keyword indices for fast lookup."""
        self.keywords_index.clear()

        # Index templates
        for template_id, template in templates.items():
            for keyword in template.relevance_keywords:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = set()
                self.keywords_index[keyword].add(template_id)

        # Index knowledge
        for entry_id, entry in knowledge.items():
            for keyword in entry.keywords:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = set()
                self.keywords_index[keyword].add(entry_id)

    def _save_knowledge_base(self, templates: Dict[str, QuickTemplate], knowledge: Dict[str, KnowledgeEntry]):
        """Save knowledge base to disk."""
        try:
            # Save templates
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                serializable_templates = {k: asdict(v) for k, v in templates.items()}
                json.dump(serializable_templates, f, indent=2)

            # Save knowledge (convert sets to lists for JSON)
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                serializable_knowledge = {}
                for k, v in knowledge.items():
                    data = asdict(v)
                    data['keywords'] = list(data['keywords'])  # Convert set to list
                    serializable_knowledge[k] = data
                json.dump(serializable_knowledge, f, indent=2)

            # Save keyword index
            with open(self.keywords_index_file, 'w', encoding='utf-8') as f:
                serializable_index = {k: list(v) for k, v in self.keywords_index.items()}
                json.dump(serializable_index, f, indent=2)

            # Update in-memory storage
            self.templates = templates
            self.knowledge = knowledge

        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    def _load_knowledge_base(self):
        """Load knowledge base from disk."""
        try:
            # Load templates
            if self.templates_file.exists():
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = {k: QuickTemplate(**v) for k, v in data.items()}

            # Load knowledge
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge = {}
                    for k, v in data.items():
                        v['keywords'] = set(v['keywords'])  # Convert list back to set
                        self.knowledge[k] = KnowledgeEntry(**v)

            # Load keyword index
            if self.keywords_index_file.exists():
                with open(self.keywords_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.keywords_index = {k: set(v) for k, v in data.items()}

        except Exception as e:
            logger.warning(f"Failed to load knowledge base: {e}")

    def _update_build_status(self, templates_count: int, knowledge_count: int, build_time: float):
        """Update build status."""
        status = {
            'built': True,
            'templates_count': templates_count,
            'knowledge_count': knowledge_count,
            'build_time': build_time,
            'last_built': str(int(time.time()))
        }

        with open(self.build_status_file, 'w') as f:
            json.dump(status, f, indent=2)

    # Fast lookup methods

    def quick_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fast search using pre-built indices."""
        query_lower = query.lower()
        query_words = query_lower.split()

        # Find matching template/knowledge IDs
        matching_ids = set()

        for word in query_words:
            if word in self.keywords_index:
                matching_ids.update(self.keywords_index[word])

        # Score and return results
        results = []

        # Check templates
        for template_id in matching_ids:
            if template_id in self.templates:
                template = self.templates[template_id]
                score = self._calculate_quick_relevance(query_lower, template)

                results.append({
                    'type': 'template',
                    'id': template_id,
                    'title': template.title,
                    'content': template.yaml_snippet,
                    'description': template.description,
                    'gpu_specific': template.gpu_specific,
                    'warnings': template.warnings,
                    'source_url': template.source_url,
                    'relevance': score
                })

        # Check knowledge entries
        for entry_id in matching_ids:
            if entry_id in self.knowledge:
                entry = self.knowledge[entry_id]
                score = entry.importance * 0.8  # Base on importance

                results.append({
                    'type': 'knowledge',
                    'id': entry_id,
                    'title': entry.topic.title(),
                    'content': entry.content,
                    'topic': entry.topic,
                    'source_url': entry.source_url,
                    'relevance': score
                })

        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:limit]

    def _calculate_quick_relevance(self, query: str, template: QuickTemplate) -> float:
        """Quick relevance calculation."""
        score = 0.0

        # GPU boost for GPU queries
        if any(gpu_term in query for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
            if template.gpu_specific:
                score += 0.5

        # Keyword matching
        query_words = set(query.split())
        template_keywords = set(template.relevance_keywords)
        overlap = len(query_words & template_keywords)

        if overlap > 0:
            score += overlap * 0.2

        # Title matching
        if any(word in template.title.lower() for word in query.split()):
            score += 0.3

        return min(1.0, score)

    def get_gpu_templates(self) -> List[Dict[str, Any]]:
        """Get all GPU-specific templates quickly."""
        gpu_templates = []

        for template_id, template in self.templates.items():
            if template.gpu_specific:
                gpu_templates.append({
                    'id': template_id,
                    'title': template.title,
                    'resource_type': template.resource_type,
                    'yaml_snippet': template.yaml_snippet,
                    'description': template.description,
                    'warnings': template.warnings,
                    'source_url': template.source_url
                })

        return gpu_templates

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        gpu_count = sum(1 for t in self.templates.values() if t.gpu_specific)

        return {
            'total_templates': len(self.templates),
            'total_knowledge': len(self.knowledge),
            'gpu_templates': gpu_count,
            'keywords_indexed': len(self.keywords_index),
            'is_built': self.is_knowledge_base_built()
        }


# Convenience functions
def ensure_knowledge_base_built() -> FastKnowledgeBuilder:
    """Ensure knowledge base is built and return the builder."""
    builder = FastKnowledgeBuilder()

    if not builder.is_knowledge_base_built():
        print("Building knowledge base for first time...")
        success = builder.build_knowledge_base()
        if success:
            print("Knowledge base built successfully!")
        else:
            print("Failed to build knowledge base")

    return builder

def quick_search_knowledge(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Quick search of the knowledge base."""
    builder = ensure_knowledge_base_built()
    return builder.quick_search(query, limit)

def get_a100_templates() -> List[Dict[str, Any]]:
    """Get A100-specific templates quickly."""
    builder = ensure_knowledge_base_built()
    results = builder.quick_search("A100 GPU", limit=10)
    return [r for r in results if r['type'] == 'template' and 'a100' in r['content'].lower()]