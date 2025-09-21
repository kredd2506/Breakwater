#!/usr/bin/env python3
"""
Edge Case Handler
================

Robust edge case handling for unknown queries, missing documentation,
and various failure scenarios in the NRP K8s system.

Features:
- Unknown query classification and handling
- Missing documentation fallback strategies
- Progressive enhancement of knowledge base
- Error recovery and graceful degradation
- Comprehensive response generation pipeline
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    KNOWN_EXACT = "known_exact"           # Perfect match in knowledge base
    KNOWN_PARTIAL = "known_partial"       # Partial match, needs enhancement
    UNKNOWN_DOMAIN = "unknown_domain"     # New domain/topic not seen before
    UNKNOWN_RESOURCE = "unknown_resource" # New resource type
    BROKEN_REFERENCE = "broken_reference" # References broken/missing docs
    AMBIGUOUS = "ambiguous"              # Multiple possible interpretations
    INCOMPLETE = "incomplete"            # Missing key information

class ResponseStrategy(Enum):
    KB_DIRECT = "kb_direct"              # Direct knowledge base response
    KB_ENHANCED = "kb_enhanced"          # KB + fresh extraction
    FRESH_EXTRACTION = "fresh_extraction" # Complete fresh extraction
    FALLBACK_SYNTHESIS = "fallback_synthesis" # Synthesize from related info
    ERROR_GUIDANCE = "error_guidance"    # Helpful error with guidance

@dataclass
class EdgeCaseResult:
    query_type: QueryType
    confidence: float
    strategy: ResponseStrategy
    fallback_options: List[str]
    knowledge_gaps: List[str]
    enhancement_needed: bool

class EdgeCaseHandler:
    """Handles edge cases and unknown queries with robust fallback strategies."""

    def __init__(self, knowledge_base, navigator, extractor):
        self.knowledge_base = knowledge_base
        self.navigator = navigator
        self.extractor = extractor

        # Load comprehensive scraping data if available
        self.cache_dir = Path(__file__).parent.parent / "cache" / "comprehensive_scraping"
        self.comprehensive_data = self._load_comprehensive_data()

        # Domain knowledge for classification
        self.known_domains = {
            'kubernetes': ['k8s', 'pod', 'deployment', 'service', 'job', 'cronjob'],
            'gpu': ['gpu', 'nvidia', 'cuda', 'a100', 'v100', 'graphics'],
            'fpga': ['fpga', 'alveo', 'smartnic', 'esnet', 'xilinx'],
            'storage': ['storage', 'pvc', 'volume', 'persistent', 'ceph'],
            'networking': ['network', 'ingress', 'service', 'loadbalancer'],
            'ai_ml': ['ai', 'ml', 'llm', 'model', 'training', 'inference'],
            'admin': ['admin', 'cluster', 'node', 'policy', 'operations'],
            'jupyter': ['jupyter', 'notebook', 'lab', 'hub'],
            'security': ['rbac', 'auth', 'security', 'permission', 'access']
        }

        # Response templates for different edge cases
        self.response_templates = self._initialize_response_templates()

    def analyze_query_edge_case(self, query: str, kb_results: List = None) -> EdgeCaseResult:
        """Analyze query to determine edge case type and appropriate strategy."""

        # Step 1: Check knowledge base coverage
        kb_results = kb_results or self.knowledge_base.search_templates(query, limit=5)

        # Step 2: Classify query type
        query_type, confidence = self._classify_query_type(query, kb_results)

        # Step 3: Determine response strategy
        strategy = self._determine_response_strategy(query_type, confidence, kb_results)

        # Step 4: Identify fallback options
        fallback_options = self._identify_fallback_options(query, query_type)

        # Step 5: Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(query, kb_results)

        # Step 6: Determine if enhancement needed
        enhancement_needed = self._needs_enhancement(query_type, confidence, kb_results)

        return EdgeCaseResult(
            query_type=query_type,
            confidence=confidence,
            strategy=strategy,
            fallback_options=fallback_options,
            knowledge_gaps=knowledge_gaps,
            enhancement_needed=enhancement_needed
        )

    def handle_edge_case(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle the edge case using the determined strategy."""

        print(f"[Edge Case Handler] Query type: {edge_case.query_type.value}")
        print(f"[Edge Case Handler] Strategy: {edge_case.strategy.value}")

        if edge_case.strategy == ResponseStrategy.KB_DIRECT:
            return self._handle_kb_direct(query)

        elif edge_case.strategy == ResponseStrategy.KB_ENHANCED:
            return self._handle_kb_enhanced(query, edge_case)

        elif edge_case.strategy == ResponseStrategy.FRESH_EXTRACTION:
            return self._handle_fresh_extraction(query, edge_case)

        elif edge_case.strategy == ResponseStrategy.FALLBACK_SYNTHESIS:
            return self._handle_fallback_synthesis(query, edge_case)

        elif edge_case.strategy == ResponseStrategy.ERROR_GUIDANCE:
            return self._handle_error_guidance(query, edge_case)

        else:
            return self._handle_unknown_strategy(query, edge_case)

    def _classify_query_type(self, query: str, kb_results: List) -> Tuple[QueryType, float]:
        """Classify the query type and confidence level."""

        query_lower = query.lower()

        # Check knowledge base coverage
        if kb_results:
            max_relevance = max(r.relevance_score for r in kb_results)
            avg_relevance = sum(r.relevance_score for r in kb_results) / len(kb_results)

            if max_relevance > 0.8:
                return QueryType.KNOWN_EXACT, max_relevance
            elif max_relevance > 0.5:
                return QueryType.KNOWN_PARTIAL, max_relevance

        # Check if query mentions known domains
        mentioned_domains = []
        for domain, keywords in self.known_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                mentioned_domains.append(domain)

        if not mentioned_domains:
            return QueryType.UNKNOWN_DOMAIN, 0.1

        # Check for new resource types
        if self._contains_unknown_resources(query_lower):
            return QueryType.UNKNOWN_RESOURCE, 0.3

        # Check for broken references
        if self._references_broken_links(query_lower):
            return QueryType.BROKEN_REFERENCE, 0.2

        # Check for ambiguity
        if len(mentioned_domains) > 2:
            return QueryType.AMBIGUOUS, 0.4

        # Check for incomplete information
        if self._is_incomplete_query(query_lower):
            return QueryType.INCOMPLETE, 0.3

        # Default to unknown domain with low confidence
        return QueryType.UNKNOWN_DOMAIN, 0.2

    def _determine_response_strategy(self, query_type: QueryType, confidence: float, kb_results: List) -> ResponseStrategy:
        """Determine the best response strategy for the query type."""

        if query_type == QueryType.KNOWN_EXACT and confidence > 0.8:
            return ResponseStrategy.KB_DIRECT

        elif query_type == QueryType.KNOWN_PARTIAL and confidence > 0.5:
            return ResponseStrategy.KB_ENHANCED

        elif query_type in [QueryType.UNKNOWN_DOMAIN, QueryType.UNKNOWN_RESOURCE]:
            # Check if we have comprehensive data that might help
            if self.comprehensive_data and self._has_comprehensive_coverage(query_type):
                return ResponseStrategy.FRESH_EXTRACTION
            else:
                return ResponseStrategy.FALLBACK_SYNTHESIS

        elif query_type == QueryType.BROKEN_REFERENCE:
            return ResponseStrategy.ERROR_GUIDANCE

        elif query_type == QueryType.AMBIGUOUS:
            return ResponseStrategy.FALLBACK_SYNTHESIS

        elif query_type == QueryType.INCOMPLETE:
            return ResponseStrategy.ERROR_GUIDANCE

        else:
            return ResponseStrategy.FALLBACK_SYNTHESIS

    def _handle_kb_direct(self, query: str) -> Dict[str, Any]:
        """Handle queries with direct knowledge base matches."""
        kb_results = self.knowledge_base.search_templates(query, limit=3)

        if kb_results:
            best_result = kb_results[0]
            template = best_result.template.template

            return {
                'success': True,
                'source': 'knowledge_base_direct',
                'confidence': best_result.relevance_score,
                'content': self._format_direct_response(template),
                'citations': [template.source_url],
                'metadata': {
                    'template_id': best_result.template_id,
                    'relevance_score': best_result.relevance_score,
                    'matched_fields': best_result.matched_fields
                }
            }

        return self._handle_fallback_synthesis(query, None)

    def _handle_kb_enhanced(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle queries that need knowledge base enhancement."""

        # Get existing knowledge
        kb_results = self.knowledge_base.search_templates(query, limit=5)

        # Attempt fresh extraction for enhancement
        try:
            navigation_results = self.navigator.discover_relevant_sources(query)
            if navigation_results['sources']:
                # Extract from top sources
                templates, knowledge = self.extractor.deep_extract_from_url(
                    navigation_results['sources'][0]['url'],
                    self._extract_topic_focus(query)
                )

                # Update knowledge base
                if templates:
                    for template in templates:
                        self.knowledge_base.add_template(template)
                    self.knowledge_base.save()

                # Get enhanced results
                enhanced_kb_results = self.knowledge_base.search_templates(query, limit=3)

                if enhanced_kb_results and enhanced_kb_results[0].relevance_score > 0.6:
                    best_result = enhanced_kb_results[0]
                    template = best_result.template.template

                    return {
                        'success': True,
                        'source': 'knowledge_base_enhanced',
                        'confidence': best_result.relevance_score,
                        'content': self._format_enhanced_response(template, kb_results),
                        'citations': [template.source_url],
                        'enhancement_info': f"Enhanced with {len(templates)} new templates",
                        'metadata': {
                            'template_id': best_result.template_id,
                            'relevance_score': best_result.relevance_score,
                            'enhancement_method': 'fresh_extraction'
                        }
                    }

        except Exception as e:
            logger.warning(f"Enhancement failed: {e}")

        # Fallback to synthesis if enhancement fails
        return self._handle_fallback_synthesis(query, edge_case)

    def _handle_fresh_extraction(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle queries requiring fresh extraction."""

        try:
            # Navigate to find sources
            navigation_results = self.navigator.discover_relevant_sources(query)

            if not navigation_results['sources']:
                return self._handle_error_guidance(query, edge_case)

            # Extract from multiple sources
            all_templates = []
            all_knowledge = []

            for source in navigation_results['sources'][:3]:  # Top 3 sources
                try:
                    templates, knowledge = self.extractor.deep_extract_from_url(
                        source['url'],
                        self._extract_topic_focus(query)
                    )
                    all_templates.extend(templates)
                    all_knowledge.extend(knowledge)
                except Exception as e:
                    logger.warning(f"Extraction failed for {source['url']}: {e}")
                    continue

            if all_templates:
                # Update knowledge base
                for template in all_templates:
                    self.knowledge_base.add_template(template)
                self.knowledge_base.save()

                # Generate response from best template
                best_template = max(all_templates, key=lambda t: t.confidence_score)

                return {
                    'success': True,
                    'source': 'fresh_extraction',
                    'confidence': best_template.confidence_score,
                    'content': self._format_fresh_response(best_template, all_templates),
                    'citations': list(set(t.source_url for t in all_templates)),
                    'extraction_info': f"Extracted {len(all_templates)} templates from {len(navigation_results['sources'])} sources",
                    'metadata': {
                        'templates_created': len(all_templates),
                        'sources_processed': len(navigation_results['sources']),
                        'extraction_method': 'comprehensive'
                    }
                }

        except Exception as e:
            logger.error(f"Fresh extraction failed: {e}")

        return self._handle_fallback_synthesis(query, edge_case)

    def _handle_fallback_synthesis(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle queries using fallback synthesis from related information."""

        # Try to find related information
        query_words = query.lower().split()
        related_templates = []

        # Search for related terms
        for word in query_words:
            if len(word) > 3:  # Skip short words
                word_results = self.knowledge_base.search_templates(word, limit=2)
                related_templates.extend(word_results)

        # Remove duplicates and sort by relevance
        seen_ids = set()
        unique_templates = []
        for result in related_templates:
            if result.template_id not in seen_ids:
                seen_ids.add(result.template_id)
                unique_templates.append(result)

        unique_templates.sort(key=lambda x: x.relevance_score, reverse=True)

        if unique_templates:
            return {
                'success': True,
                'source': 'fallback_synthesis',
                'confidence': 0.5,  # Moderate confidence for synthesis
                'content': self._format_synthesis_response(query, unique_templates[:3]),
                'citations': [t.template.template.source_url for t in unique_templates[:3]],
                'synthesis_info': f"Synthesized from {len(unique_templates)} related templates",
                'metadata': {
                    'synthesis_method': 'related_templates',
                    'related_count': len(unique_templates),
                    'confidence_note': 'Synthesized response - may not be complete'
                }
            }

        return self._handle_error_guidance(query, edge_case)

    def _handle_error_guidance(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle queries with helpful error messages and guidance."""

        # Determine what kind of guidance to provide
        guidance_type = self._determine_guidance_type(query, edge_case)

        return {
            'success': False,
            'source': 'error_guidance',
            'confidence': 0.0,
            'content': self._format_error_guidance(query, edge_case, guidance_type),
            'guidance': {
                'type': guidance_type,
                'suggestions': self._get_guidance_suggestions(query, edge_case),
                'similar_queries': self._find_similar_queries(query),
                'available_topics': self._get_available_topics()
            },
            'metadata': {
                'error_type': edge_case.query_type.value if edge_case else 'unknown',
                'knowledge_gaps': edge_case.knowledge_gaps if edge_case else [],
                'fallback_options': edge_case.fallback_options if edge_case else []
            }
        }

    def _handle_unknown_strategy(self, query: str, edge_case: EdgeCaseResult) -> Dict[str, Any]:
        """Handle queries with unknown strategy (should not happen)."""

        return {
            'success': False,
            'source': 'unknown_strategy',
            'confidence': 0.0,
            'content': f"Unable to determine how to handle this query: {query}",
            'error': f"Unknown strategy: {edge_case.strategy}",
            'metadata': {
                'query_type': edge_case.query_type.value,
                'strategy': edge_case.strategy.value
            }
        }

    # Helper methods for analysis and formatting
    def _load_comprehensive_data(self) -> Optional[Dict]:
        """Load comprehensive scraping data if available."""
        try:
            content_db_file = self.cache_dir / "content_database.json"
            if content_db_file.exists():
                with open(content_db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load comprehensive data: {e}")
        return None

    def _contains_unknown_resources(self, query: str) -> bool:
        """Check if query contains unknown resource types."""
        # This would be enhanced with comprehensive data
        return False

    def _references_broken_links(self, query: str) -> bool:
        """Check if query references broken or missing documentation."""
        # This would check against broken links database
        return False

    def _is_incomplete_query(self, query: str) -> bool:
        """Check if query is incomplete or too vague."""
        return len(query.split()) < 3 or query.endswith('?') and len(query.split()) < 5

    def _has_comprehensive_coverage(self, query_type: QueryType) -> bool:
        """Check if comprehensive data has coverage for this query type."""
        return self.comprehensive_data is not None

    def _extract_topic_focus(self, query: str) -> str:
        """Extract main topic focus from query."""
        query_lower = query.lower()
        for domain, keywords in self.known_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                return domain
        return 'general'

    def _needs_enhancement(self, query_type: QueryType, confidence: float, kb_results: List) -> bool:
        """Determine if knowledge base needs enhancement."""
        return (query_type in [QueryType.KNOWN_PARTIAL, QueryType.UNKNOWN_RESOURCE] or
                confidence < 0.6 or
                len(kb_results) < 2)

    def _identify_fallback_options(self, query: str, query_type: QueryType) -> List[str]:
        """Identify potential fallback options for the query."""
        options = []

        if query_type == QueryType.UNKNOWN_DOMAIN:
            options.append("Search broader NRP documentation")
            options.append("Check official Kubernetes documentation")

        elif query_type == QueryType.BROKEN_REFERENCE:
            options.append("Search for alternative documentation")
            options.append("Check archived or cached versions")

        elif query_type == QueryType.AMBIGUOUS:
            options.append("Clarify specific aspect of interest")
            options.append("Break down into specific sub-questions")

        return options

    def _identify_knowledge_gaps(self, query: str, kb_results: List) -> List[str]:
        """Identify gaps in current knowledge base."""
        gaps = []

        if not kb_results:
            gaps.append("No existing templates for this topic")

        elif max(r.relevance_score for r in kb_results) < 0.5:
            gaps.append("Low relevance of existing templates")

        # Add more sophisticated gap analysis here

        return gaps

    def _format_direct_response(self, template) -> str:
        """Format direct response from knowledge base template."""
        return f"""# {template.title}

{template.description}

## Configuration

```yaml
{template.yaml_content}
```

## Important Warnings
{chr(10).join('- ' + warning for warning in template.warnings[:3])}

## Best Practices
{chr(10).join('- ' + practice for practice in template.best_practices[:3])}

**Source:** {template.source_url}
"""

    def _format_enhanced_response(self, template, original_results) -> str:
        """Format enhanced response with additional context."""
        response = self._format_direct_response(template)

        if original_results:
            response += f"\n\n## Related Information\n"
            for result in original_results[:2]:
                response += f"- {result.template.template.title}\n"

        return response

    def _format_fresh_response(self, best_template, all_templates) -> str:
        """Format response from fresh extraction."""
        response = self._format_direct_response(best_template)

        if len(all_templates) > 1:
            response += f"\n\n## Additional Resources\n"
            for template in all_templates[1:3]:
                response += f"- {template.title}: {template.source_url}\n"

        return response

    def _format_synthesis_response(self, query: str, related_templates) -> str:
        """Format synthesized response from related templates."""
        response = f"# Information Related to: {query}\n\n"
        response += "Based on related NRP documentation:\n\n"

        for i, result in enumerate(related_templates, 1):
            template = result.template.template
            response += f"## {i}. {template.title}\n"
            response += f"{template.description}\n\n"
            if template.warnings:
                response += f"**Warning:** {template.warnings[0]}\n\n"

        response += "**Note:** This is a synthesized response from related topics. "
        response += "For specific guidance, please consult the official NRP documentation.\n"

        return response

    def _format_error_guidance(self, query: str, edge_case: EdgeCaseResult, guidance_type: str) -> str:
        """Format helpful error guidance."""
        return f"""# Unable to Find Specific Information

I couldn't find specific information about: **{query}**

## Possible Reasons
- This might be a new or specialized topic not yet covered in the knowledge base
- The query might need to be more specific
- Documentation might exist but not yet indexed

## Suggestions
- Try rephrasing your question with more specific terms
- Check the official NRP documentation at https://nrp.ai/documentation/
- Consider breaking down complex questions into smaller parts

## Available Topics
I have comprehensive information about: GPU workloads, FPGA management, storage configuration, Kubernetes deployments, and administrative procedures.
"""

    def _determine_guidance_type(self, query: str, edge_case: EdgeCaseResult) -> str:
        """Determine what type of guidance to provide."""
        if edge_case and edge_case.query_type == QueryType.AMBIGUOUS:
            return "clarification_needed"
        elif edge_case and edge_case.query_type == QueryType.INCOMPLETE:
            return "more_specific_needed"
        else:
            return "topic_not_found"

    def _get_guidance_suggestions(self, query: str, edge_case: EdgeCaseResult) -> List[str]:
        """Get specific suggestions for the query."""
        return [
            "Try using more specific technical terms",
            "Include the resource type (pod, job, service, etc.)",
            "Specify the NRP component you're working with",
            "Check the official NRP documentation"
        ]

    def _find_similar_queries(self, query: str) -> List[str]:
        """Find similar queries that might help."""
        # This would be enhanced with query similarity analysis
        return [
            "How to configure GPU workloads?",
            "How to request storage resources?",
            "How to deploy applications on NRP?"
        ]

    def _get_available_topics(self) -> List[str]:
        """Get list of available topics in knowledge base."""
        stats = self.knowledge_base.get_statistics()
        return list(stats['resource_type_distribution'].keys())

    def _initialize_response_templates(self) -> Dict[str, str]:
        """Initialize response templates for different scenarios."""
        return {
            'unknown_domain': "This appears to be about {domain} which is not well covered in our current knowledge base.",
            'partial_match': "I found some related information about {topic}, but it may not be complete.",
            'synthesis': "Based on related NRP documentation, here's what I can tell you about {query}:",
            'error': "I couldn't find specific information about {query}. Here are some suggestions:"
        }