#!/usr/bin/env python3
"""
Enhanced Knowledge Base
======================

Advanced knowledge base that stores templates, warnings, examples, and best practices
with proper organization, search capabilities, and quality scoring.

Features:
- Structured template storage with warnings and cautions
- Semantic search capabilities
- Quality scoring and validation
- Context-aware retrieval
- Automatic knowledge base updates
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

from ..agents.deep_extractor_agent import ExtractionTemplate, ExtractedKnowledge, DeepExtractorAgent

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeTemplate:
    """Enhanced template with quality metrics and relationships."""
    # Core template data
    template: ExtractionTemplate

    # Quality metrics
    accuracy_score: float
    completeness_score: float
    usefulness_score: float
    last_verified: str

    # Relationships
    related_templates: List[str]  # IDs of related templates
    superseded_by: Optional[str]  # ID of newer template that replaces this
    supersedes: List[str]  # IDs of older templates this replaces

    # Usage tracking
    access_count: int
    last_accessed: str
    success_feedback_count: int
    failure_feedback_count: int

@dataclass
class SearchResult:
    """Search result with relevance scoring."""
    template_id: str
    template: KnowledgeTemplate
    relevance_score: float
    match_type: str  # "exact", "semantic", "partial"
    matched_fields: List[str]

@dataclass
class KnowledgeIndex:
    """Index for fast knowledge retrieval."""
    keyword_index: Dict[str, Set[str]]  # keyword -> template_ids
    topic_index: Dict[str, Set[str]]    # topic -> template_ids
    resource_type_index: Dict[str, Set[str]]  # resource_type -> template_ids
    warning_index: Dict[str, Set[str]]  # warning_type -> template_ids

class EnhancedKnowledgeBase:
    """
    Enhanced knowledge base for storing and retrieving documentation templates.

    Organizes templates by:
    - Resource type (pod, deployment, job, etc.)
    - Topic (GPU, storage, networking, etc.)
    - Warning level (danger, caution, warning, note)
    - Quality metrics
    """

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "enhanced_knowledge_base"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Storage files
        self.templates_file = self.cache_dir / "knowledge_templates.json"
        self.index_file = self.cache_dir / "knowledge_index.json"
        self.metadata_file = self.cache_dir / "knowledge_metadata.json"

        # In-memory storage
        self.templates: Dict[str, KnowledgeTemplate] = {}  # template_id -> KnowledgeTemplate
        self.index: KnowledgeIndex = KnowledgeIndex(
            keyword_index=defaultdict(set),
            topic_index=defaultdict(set),
            resource_type_index=defaultdict(set),
            warning_index=defaultdict(set)
        )

        # Metadata
        self.metadata = {
            "last_updated": None,
            "total_templates": 0,
            "update_history": []
        }

        # Load existing data
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load knowledge base from disk."""
        try:
            # Load templates
            if self.templates_file.exists():
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for template_id, template_data in data.items():
                        # Reconstruct ExtractionTemplate
                        extraction_template = ExtractionTemplate(**template_data['template'])
                        # Remove template from template_data and create KnowledgeTemplate
                        template_data.pop('template')
                        knowledge_template = KnowledgeTemplate(
                            template=extraction_template,
                            **template_data
                        )
                        self.templates[template_id] = knowledge_template

            # Load index
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    # Convert lists back to sets and maintain defaultdict behavior
                    self.index.keyword_index = defaultdict(set)
                    self.index.topic_index = defaultdict(set)
                    self.index.resource_type_index = defaultdict(set)
                    self.index.warning_index = defaultdict(set)

                    # Populate with existing data
                    for k, v in index_data.get('keyword_index', {}).items():
                        self.index.keyword_index[k] = set(v)
                    for k, v in index_data.get('topic_index', {}).items():
                        self.index.topic_index[k] = set(v)
                    for k, v in index_data.get('resource_type_index', {}).items():
                        self.index.resource_type_index[k] = set(v)
                    for k, v in index_data.get('warning_index', {}).items():
                        self.index.warning_index[k] = set(v)

            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

            logger.info(f"Loaded {len(self.templates)} templates from knowledge base")

        except Exception as e:
            logger.warning(f"Failed to load knowledge base: {e}")

    def _save_knowledge_base(self):
        """Save knowledge base to disk."""
        try:
            # Save templates
            templates_data = {}
            for template_id, knowledge_template in self.templates.items():
                template_dict = asdict(knowledge_template)
                templates_data[template_id] = template_dict

            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2)

            # Save index (convert sets to lists for JSON serialization)
            index_data = {
                'keyword_index': {k: list(v) for k, v in self.index.keyword_index.items()},
                'topic_index': {k: list(v) for k, v in self.index.topic_index.items()},
                'resource_type_index': {k: list(v) for k, v in self.index.resource_type_index.items()},
                'warning_index': {k: list(v) for k, v in self.index.warning_index.items()}
            }

            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)

            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    def add_template(self, template: ExtractionTemplate, quality_metrics: Dict[str, float] = None) -> str:
        """
        Add a template to the knowledge base.

        Args:
            template: The extraction template to add
            quality_metrics: Optional quality metrics

        Returns:
            Template ID
        """
        # Generate unique ID
        template_id = self._generate_template_id(template)

        # Check if template already exists
        if template_id in self.templates:
            logger.info(f"Template {template_id} already exists, updating...")
            return self._update_existing_template(template_id, template, quality_metrics)

        # Create quality metrics
        if not quality_metrics:
            quality_metrics = self._calculate_quality_metrics(template)

        # Create knowledge template
        knowledge_template = KnowledgeTemplate(
            template=template,
            accuracy_score=quality_metrics.get('accuracy', 0.8),
            completeness_score=quality_metrics.get('completeness', 0.7),
            usefulness_score=quality_metrics.get('usefulness', 0.6),
            last_verified=str(int(time.time())),
            related_templates=[],
            superseded_by=None,
            supersedes=[],
            access_count=0,
            last_accessed=str(int(time.time())),
            success_feedback_count=0,
            failure_feedback_count=0
        )

        # Add to storage
        self.templates[template_id] = knowledge_template

        # Update indices
        self._update_indices(template_id, template)

        # Find related templates
        self._find_and_link_related_templates(template_id)

        # Update metadata
        self.metadata['total_templates'] = len(self.templates)
        self.metadata['last_updated'] = str(int(time.time()))
        self.metadata['update_history'].append({
            'action': 'add_template',
            'template_id': template_id,
            'timestamp': str(int(time.time()))
        })

        logger.info(f"Added template {template_id} to knowledge base")
        return template_id

    def search_templates(self, query: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[SearchResult]:
        """
        Search for templates using query and filters.

        Args:
            query: Search query
            filters: Additional filters (resource_type, topic, warning_level, etc.)
            limit: Maximum number of results

        Returns:
            List of search results sorted by relevance
        """
        filters = filters or {}
        results = []

        # Normalize query
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for template_id, knowledge_template in self.templates.items():
            template = knowledge_template.template

            # Apply filters first
            if not self._passes_filters(template, filters):
                continue

            # Calculate relevance score
            relevance_score = 0.0
            matched_fields = []

            # Title matching (highest weight)
            title_words = set(template.title.lower().split())
            title_overlap = len(query_words & title_words) / len(query_words) if query_words else 0
            if title_overlap > 0:
                relevance_score += title_overlap * 1.0
                matched_fields.append('title')

            # Description matching
            desc_words = set(template.description.lower().split())
            desc_overlap = len(query_words & desc_words) / len(query_words) if query_words else 0
            if desc_overlap > 0:
                relevance_score += desc_overlap * 0.8
                matched_fields.append('description')

            # Resource type matching
            if query_lower in template.resource_type.lower():
                relevance_score += 0.9
                matched_fields.append('resource_type')

            # YAML content matching
            yaml_words = set(template.yaml_content.lower().split())
            yaml_overlap = len(query_words & yaml_words) / len(query_words) if query_words else 0
            if yaml_overlap > 0:
                relevance_score += yaml_overlap * 0.6
                matched_fields.append('yaml_content')

            # Warning/note matching
            all_warnings = (template.warnings + template.cautions +
                          template.notes + template.dangers)
            for warning in all_warnings:
                warning_words = set(warning.lower().split())
                warning_overlap = len(query_words & warning_words) / len(query_words) if query_words else 0
                if warning_overlap > 0:
                    relevance_score += warning_overlap * 0.7
                    matched_fields.append('warnings')
                    break

            # Best practices matching
            for practice in template.best_practices:
                practice_words = set(practice.lower().split())
                practice_overlap = len(query_words & practice_words) / len(query_words) if query_words else 0
                if practice_overlap > 0:
                    relevance_score += practice_overlap * 0.5
                    matched_fields.append('best_practices')
                    break

            # Apply quality boost
            quality_boost = (knowledge_template.accuracy_score +
                           knowledge_template.completeness_score +
                           knowledge_template.usefulness_score) / 3
            relevance_score *= (0.5 + quality_boost * 0.5)

            # Apply usage boost
            usage_boost = min(1.0, knowledge_template.access_count / 100.0)
            relevance_score *= (0.8 + usage_boost * 0.2)

            # Only include if relevance is above threshold
            if relevance_score > 0.1:
                match_type = self._determine_match_type(relevance_score, matched_fields)

                results.append(SearchResult(
                    template_id=template_id,
                    template=knowledge_template,
                    relevance_score=relevance_score,
                    match_type=match_type,
                    matched_fields=matched_fields
                ))

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def get_template_by_id(self, template_id: str) -> Optional[KnowledgeTemplate]:
        """Get template by ID and update access statistics."""
        if template_id in self.templates:
            knowledge_template = self.templates[template_id]

            # Update access statistics
            knowledge_template.access_count += 1
            knowledge_template.last_accessed = str(int(time.time()))

            return knowledge_template
        return None

    def get_templates_by_topic(self, topic: str) -> List[KnowledgeTemplate]:
        """Get all templates for a specific topic."""
        template_ids = self.index.topic_index.get(topic.lower(), set())
        return [self.templates[tid] for tid in template_ids if tid in self.templates]

    def get_templates_by_resource_type(self, resource_type: str) -> List[KnowledgeTemplate]:
        """Get all templates for a specific resource type."""
        template_ids = self.index.resource_type_index.get(resource_type.lower(), set())
        return [self.templates[tid] for tid in template_ids if tid in self.templates]

    def get_critical_warnings(self) -> List[KnowledgeTemplate]:
        """Get templates with critical warnings (dangers)."""
        template_ids = self.index.warning_index.get('danger', set())
        templates_with_warnings = [self.templates[tid] for tid in template_ids if tid in self.templates]

        # Sort by severity (templates with more dangers first)
        templates_with_warnings.sort(
            key=lambda kt: len(kt.template.dangers),
            reverse=True
        )

        return templates_with_warnings

    def add_feedback(self, template_id: str, success: bool):
        """Add user feedback for a template."""
        if template_id in self.templates:
            knowledge_template = self.templates[template_id]
            if success:
                knowledge_template.success_feedback_count += 1
            else:
                knowledge_template.failure_feedback_count += 1

            # Recalculate usefulness score
            total_feedback = (knowledge_template.success_feedback_count +
                            knowledge_template.failure_feedback_count)
            if total_feedback > 0:
                success_rate = knowledge_template.success_feedback_count / total_feedback
                knowledge_template.usefulness_score = success_rate

    def update_from_extractor(self, extractor: DeepExtractorAgent):
        """Update knowledge base with templates from deep extractor."""
        logger.info("Updating knowledge base from deep extractor...")

        added_count = 0
        updated_count = 0

        for template in extractor.templates:
            template_id = self.add_template(template)
            if template_id:
                if template_id in self.templates:
                    updated_count += 1
                else:
                    added_count += 1

        logger.info(f"Knowledge base update complete: {added_count} added, {updated_count} updated")
        self._save_knowledge_base()

    def get_best_template_for_query(self, query: str, resource_type: str = None) -> Optional[KnowledgeTemplate]:
        """Get the best single template for a query."""
        filters = {}
        if resource_type:
            filters['resource_type'] = resource_type

        results = self.search_templates(query, filters, limit=1)

        if results:
            # Update access for the best result
            best_result = results[0]
            best_result.template.access_count += 1
            best_result.template.last_accessed = str(int(time.time()))
            return best_result.template

        return None

    def get_template_with_warnings(self, query: str) -> List[Tuple[KnowledgeTemplate, List[str]]]:
        """Get templates with their associated warnings for a query."""
        results = self.search_templates(query, limit=5)

        templates_with_warnings = []
        for result in results:
            template = result.template.template
            all_warnings = []

            if template.dangers:
                all_warnings.extend([f"🚨 DANGER: {w}" for w in template.dangers])
            if template.warnings:
                all_warnings.extend([f"⚠️ WARNING: {w}" for w in template.warnings])
            if template.cautions:
                all_warnings.extend([f"⚡ CAUTION: {w}" for w in template.cautions])
            if template.notes:
                all_warnings.extend([f"ℹ️ NOTE: {w}" for w in template.notes])

            templates_with_warnings.append((result.template, all_warnings))

        return templates_with_warnings

    def export_template_for_user(self, template_id: str) -> Dict[str, Any]:
        """Export template in user-friendly format."""
        knowledge_template = self.get_template_by_id(template_id)
        if not knowledge_template:
            return {}

        template = knowledge_template.template

        return {
            'title': template.title,
            'description': template.description,
            'resource_type': template.resource_type,
            'yaml_content': template.yaml_content,
            'warnings': {
                'dangers': template.dangers,
                'warnings': template.warnings,
                'cautions': template.cautions,
                'notes': template.notes
            },
            'guidance': {
                'best_practices': template.best_practices,
                'common_mistakes': template.common_mistakes,
                'examples': template.examples
            },
            'requirements': {
                'api_version': template.api_version,
                'namespace_requirements': template.namespace_requirements,
                'resource_requirements': template.resource_requirements,
                'dependencies': template.dependencies
            },
            'source': template.source_url,
            'quality_metrics': {
                'accuracy': knowledge_template.accuracy_score,
                'completeness': knowledge_template.completeness_score,
                'usefulness': knowledge_template.usefulness_score
            }
        }

    # Helper methods

    def _generate_template_id(self, template: ExtractionTemplate) -> str:
        """Generate unique ID for template."""
        content_hash = hashlib.md5(
            f"{template.title}{template.resource_type}{template.yaml_content}".encode()
        ).hexdigest()
        return f"{template.resource_type}_{content_hash[:8]}"

    def _calculate_quality_metrics(self, template: ExtractionTemplate) -> Dict[str, float]:
        """Calculate quality metrics for template."""
        accuracy = 0.8  # Base accuracy

        # Boost for valid YAML
        try:
            import yaml
            yaml.safe_load(template.yaml_content)
            accuracy += 0.1
        except:
            accuracy -= 0.2

        # Completeness based on available fields
        completeness = 0.5
        if template.warnings or template.cautions or template.dangers:
            completeness += 0.2
        if template.best_practices:
            completeness += 0.1
        if template.examples:
            completeness += 0.1
        if template.resource_requirements:
            completeness += 0.1

        # Usefulness based on content quality
        usefulness = 0.6
        if len(template.description) > 50:
            usefulness += 0.1
        if template.usage_context and len(template.usage_context) > 100:
            usefulness += 0.1
        if template.dependencies:
            usefulness += 0.1

        return {
            'accuracy': min(1.0, accuracy),
            'completeness': min(1.0, completeness),
            'usefulness': min(1.0, usefulness)
        }

    def _update_indices(self, template_id: str, template: ExtractionTemplate):
        """Update search indices for template."""
        # Update keyword index
        all_text = f"{template.title} {template.description} {template.yaml_content} {template.usage_context}"
        keywords = self._extract_keywords(all_text)
        for keyword in keywords:
            self.index.keyword_index[keyword.lower()].add(template_id)

        # Update topic index (extract from content)
        topics = self._extract_topics(template)
        for topic in topics:
            self.index.topic_index[topic.lower()].add(template_id)

        # Update resource type index
        self.index.resource_type_index[template.resource_type.lower()].add(template_id)

        # Update warning index
        if template.dangers:
            self.index.warning_index['danger'].add(template_id)
        if template.warnings:
            self.index.warning_index['warning'].add(template_id)
        if template.cautions:
            self.index.warning_index['caution'].add(template_id)
        if template.notes:
            self.index.warning_index['note'].add(template_id)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter out common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who'}

        return [word for word in set(words) if word not in stop_words]

    def _extract_topics(self, template: ExtractionTemplate) -> List[str]:
        """Extract topics from template content."""
        topics = []
        content = f"{template.title} {template.description} {template.yaml_content}".lower()

        # Predefined topic mappings
        topic_keywords = {
            'gpu': ['gpu', 'nvidia', 'cuda', 'a100', 'v100'],
            'storage': ['storage', 'pvc', 'volume', 'persistent', 'ceph'],
            'networking': ['network', 'ingress', 'service', 'loadbalancer'],
            'jobs': ['job', 'batch', 'cron', 'workload'],
            'security': ['rbac', 'security', 'auth', 'permission'],
            'monitoring': ['prometheus', 'grafana', 'metrics', 'monitoring']
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.append(topic)

        return topics or ['general']

    def _passes_filters(self, template: ExtractionTemplate, filters: Dict[str, Any]) -> bool:
        """Check if template passes filters."""
        for filter_key, filter_value in filters.items():
            if filter_key == 'resource_type':
                if template.resource_type.lower() != filter_value.lower():
                    return False
            elif filter_key == 'warning_level':
                has_warning_level = False
                if filter_value == 'danger' and template.dangers:
                    has_warning_level = True
                elif filter_value == 'warning' and template.warnings:
                    has_warning_level = True
                elif filter_value == 'caution' and template.cautions:
                    has_warning_level = True
                elif filter_value == 'note' and template.notes:
                    has_warning_level = True
                if not has_warning_level:
                    return False
            elif filter_key == 'min_quality':
                # Would need to calculate template quality
                pass

        return True

    def _determine_match_type(self, relevance_score: float, matched_fields: List[str]) -> str:
        """Determine the type of match based on score and fields."""
        if relevance_score > 0.8:
            return "exact"
        elif relevance_score > 0.5:
            return "semantic"
        else:
            return "partial"

    def _find_and_link_related_templates(self, template_id: str):
        """Find and link related templates."""
        current_template = self.templates[template_id].template

        for other_id, other_knowledge_template in self.templates.items():
            if other_id == template_id:
                continue

            other_template = other_knowledge_template.template

            # Calculate similarity
            similarity = self._calculate_template_similarity(current_template, other_template)

            if similarity > 0.6:  # Threshold for "related"
                # Add bidirectional relationship
                self.templates[template_id].related_templates.append(other_id)
                other_knowledge_template.related_templates.append(template_id)

    def _calculate_template_similarity(self, template1: ExtractionTemplate, template2: ExtractionTemplate) -> float:
        """Calculate similarity between two templates."""
        similarity = 0.0

        # Resource type similarity
        if template1.resource_type == template2.resource_type:
            similarity += 0.4

        # Topic similarity
        topics1 = set(self._extract_topics(template1))
        topics2 = set(self._extract_topics(template2))
        topic_similarity = len(topics1 & topics2) / len(topics1 | topics2) if topics1 | topics2 else 0
        similarity += topic_similarity * 0.3

        # Content similarity (basic keyword overlap)
        keywords1 = set(self._extract_keywords(template1.title + " " + template1.description))
        keywords2 = set(self._extract_keywords(template2.title + " " + template2.description))
        keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2) if keywords1 | keywords2 else 0
        similarity += keyword_similarity * 0.3

        return similarity

    def _update_existing_template(self, template_id: str, template: ExtractionTemplate, quality_metrics: Dict[str, float] = None) -> str:
        """Update existing template with new information."""
        existing = self.templates[template_id]

        # Update template with newer information
        existing.template = template

        # Update quality metrics if provided
        if quality_metrics:
            existing.accuracy_score = quality_metrics.get('accuracy', existing.accuracy_score)
            existing.completeness_score = quality_metrics.get('completeness', existing.completeness_score)
            existing.usefulness_score = quality_metrics.get('usefulness', existing.usefulness_score)

        existing.last_verified = str(int(time.time()))

        # Update indices
        self._update_indices(template_id, template)

        return template_id

    def save(self):
        """Save knowledge base to disk."""
        self._save_knowledge_base()

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        total_templates = len(self.templates)

        # Count by resource type
        resource_type_counts = defaultdict(int)
        for kt in self.templates.values():
            resource_type_counts[kt.template.resource_type] += 1

        # Count by warning level
        warning_counts = {
            'danger': len(self.index.warning_index.get('danger', set())),
            'warning': len(self.index.warning_index.get('warning', set())),
            'caution': len(self.index.warning_index.get('caution', set())),
            'note': len(self.index.warning_index.get('note', set()))
        }

        # Average quality scores
        if total_templates > 0:
            avg_accuracy = sum(kt.accuracy_score for kt in self.templates.values()) / total_templates
            avg_completeness = sum(kt.completeness_score for kt in self.templates.values()) / total_templates
            avg_usefulness = sum(kt.usefulness_score for kt in self.templates.values()) / total_templates
        else:
            avg_accuracy = avg_completeness = avg_usefulness = 0.0

        return {
            'total_templates': total_templates,
            'resource_type_distribution': dict(resource_type_counts),
            'warning_distribution': warning_counts,
            'average_quality': {
                'accuracy': avg_accuracy,
                'completeness': avg_completeness,
                'usefulness': avg_usefulness
            },
            'last_updated': self.metadata.get('last_updated'),
            'total_topics': len(self.index.topic_index),
            'total_keywords': len(self.index.keyword_index)
        }


# Convenience functions
def create_knowledge_base() -> EnhancedKnowledgeBase:
    """Create an enhanced knowledge base."""
    return EnhancedKnowledgeBase()

def search_knowledge_base(query: str, resource_type: str = None) -> List[SearchResult]:
    """Search the knowledge base."""
    kb = EnhancedKnowledgeBase()
    filters = {'resource_type': resource_type} if resource_type else {}
    return kb.search_templates(query, filters)

def get_template_with_warnings(query: str, resource_type: str = None) -> Optional[Dict[str, Any]]:
    """Get template with warnings for a query."""
    kb = EnhancedKnowledgeBase()
    filters = {'resource_type': resource_type} if resource_type else {}
    results = kb.search_templates(query, filters, limit=1)

    if results:
        template_id = results[0].template_id
        return kb.export_template_for_user(template_id)

    return None