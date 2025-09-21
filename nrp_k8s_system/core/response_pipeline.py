#!/usr/bin/env python3
"""
Response Generation Pipeline
===========================

Comprehensive response generation pipeline that handles all edge cases,
integrates with the comprehensive scraping system, and provides robust
fallback strategies for any query scenario.

Features:
- Multi-stage response generation
- Comprehensive edge case handling
- Progressive knowledge enhancement
- Quality assessment and validation
- Robust error recovery
- Performance monitoring
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .edge_case_handler import EdgeCaseHandler, QueryType, ResponseStrategy
from ..agents.infogent_agent import InfogentAgent
from ..core.enhanced_knowledge_base import EnhancedKnowledgeBase
from ..systems.enhanced_navigator import EnhancedNavigator
from ..agents.deep_extractor_agent import DeepExtractorAgent
# Removed Ctrl+K search import

logger = logging.getLogger(__name__)

class ResponseQuality(Enum):
    EXCELLENT = "excellent"      # >0.8 confidence, complete info
    GOOD = "good"               # >0.6 confidence, mostly complete
    ACCEPTABLE = "acceptable"    # >0.4 confidence, partial info
    POOR = "poor"               # <0.4 confidence, limited info
    FAILED = "failed"           # No useful response generated

@dataclass
class ResponseMetrics:
    confidence: float
    completeness: float
    source_quality: float
    response_time: float
    knowledge_base_hits: int
    fresh_extractions: int
    fallback_used: bool

@dataclass
class ResponseResult:
    success: bool
    content: str
    quality: ResponseQuality
    metrics: ResponseMetrics
    citations: List[str]
    metadata: Dict[str, Any]
    enhancement_suggestions: List[str]

class ResponsePipeline:
    """Comprehensive response generation pipeline with edge case handling."""

    def __init__(self):
        # Initialize core components
        self.knowledge_base = EnhancedKnowledgeBase()
        self.navigator = EnhancedNavigator()
        self.extractor = DeepExtractorAgent()
        self.edge_case_handler = EdgeCaseHandler(
            self.knowledge_base,
            self.navigator,
            self.extractor
        )
        self.infogent = InfogentAgent()

        # Removed Ctrl+K search initialization

        # Performance tracking
        self.response_history = []
        self.performance_stats = {
            'total_queries': 0,
            'successful_responses': 0,
            'kb_hits': 0,
            'fresh_extractions': 0,
            'fallback_responses': 0,
            'failed_responses': 0
        }

    def generate_response(self, query: str, user_context: Dict = None) -> ResponseResult:
        """Generate comprehensive response with full edge case handling."""

        start_time = time.time()
        user_context = user_context or {}

        print(f"[Response Pipeline] Processing query: {query[:60]}...")

        try:
            # Stage 1: Knowledge Base Analysis
            kb_results = self._analyze_knowledge_base(query)

            # Stage 1.5: Skip hybrid search (Ctrl+K removed)
            hybrid_response = None

            # Stage 2: Edge Case Analysis
            edge_case = self._analyze_edge_case(query, kb_results)

            # Stage 3: Response Strategy Execution (enhanced with hybrid results)
            response_data = self._execute_response_strategy(query, edge_case, hybrid_response)

            # Stage 4: Quality Assessment
            quality = self._assess_response_quality(response_data)

            # Stage 5: Enhancement Suggestions
            enhancements = self._generate_enhancement_suggestions(query, edge_case, response_data)

            # Stage 6: Metrics Calculation
            metrics = self._calculate_response_metrics(
                start_time, response_data, kb_results, edge_case
            )

            # Update performance stats
            self._update_performance_stats(response_data, metrics)

            # Create final result
            result = ResponseResult(
                success=response_data['success'],
                content=response_data['content'],
                quality=quality,
                metrics=metrics,
                citations=response_data.get('citations', []),
                metadata=response_data.get('metadata', {}),
                enhancement_suggestions=enhancements
            )

            # Log response for analysis
            self._log_response(query, result)

            return result

        except Exception as e:
            logger.error(f"Response pipeline failed: {e}")
            import traceback
            traceback.print_exc()

            # Emergency fallback
            return self._emergency_fallback_response(query, str(e))

    def _analyze_knowledge_base(self, query: str) -> List:
        """Analyze knowledge base coverage for the query."""
        try:
            kb_results = self.knowledge_base.search_templates(query, limit=5)
            print(f"[Knowledge Base] Found {len(kb_results)} relevant templates")

            if kb_results:
                max_relevance = max(r.relevance_score for r in kb_results)
                print(f"[Knowledge Base] Max relevance: {max_relevance:.3f}")

            return kb_results

        except Exception as e:
            logger.warning(f"Knowledge base analysis failed: {e}")
            return []

    def _check_for_hybrid_search(self, query: str, kb_results: List) -> Optional[HybridSearchResponse]:
        """Check if hybrid Ctrl+K search should be used for immediate results."""
        try:
            # Check if we should use Ctrl+K search
            should_use_ctrlk = self.ctrlk_search.should_use_ctrlk_fallback(query, kb_results)

            if should_use_ctrlk:
                print(f"[Response Pipeline] Using hybrid Ctrl+K search for edge case")
                hybrid_response = self.ctrlk_search.hybrid_search(query, kb_results)

                # Log the hybrid response details
                if hybrid_response and hybrid_response.immediate_results:
                    print(f"[Response Pipeline] Ctrl+K found {len(hybrid_response.immediate_results)} immediate results")
                    for i, result in enumerate(hybrid_response.immediate_results, 1):
                        print(f"[Response Pipeline]   {i}. {result.title} (relevance: {result.relevance:.3f})")
                else:
                    print(f"[Response Pipeline] Ctrl+K search returned no immediate results")

                return hybrid_response

            return None

        except Exception as e:
            logger.warning(f"Hybrid search check failed: {e}")
            return None

    def _analyze_edge_case(self, query: str, kb_results: List) -> Any:
        """Analyze query for edge cases and determine strategy."""
        try:
            edge_case = self.edge_case_handler.analyze_query_edge_case(query, kb_results)
            print(f"[Edge Case] Type: {edge_case.query_type.value}, Strategy: {edge_case.strategy.value}")

            return edge_case

        except Exception as e:
            logger.warning(f"Edge case analysis failed: {e}")
            # Return default edge case
            from .edge_case_handler import EdgeCaseResult, QueryType, ResponseStrategy
            return EdgeCaseResult(
                query_type=QueryType.UNKNOWN_DOMAIN,
                confidence=0.1,
                strategy=ResponseStrategy.FALLBACK_SYNTHESIS,
                fallback_options=[],
                knowledge_gaps=[],
                enhancement_needed=True
            )

    def _execute_response_strategy(self, query: str, edge_case: Any, hybrid_response: Optional[HybridSearchResponse] = None) -> Dict[str, Any]:
        """Execute the determined response strategy."""
        try:
            # Check if we have immediate Ctrl+K results to use
            if hybrid_response and hybrid_response.immediate_results and len(hybrid_response.immediate_results) > 0:
                print(f"[Strategy Execution] Using immediate Ctrl+K results ({len(hybrid_response.immediate_results)} found)")
                response_data = self._generate_hybrid_response(query, hybrid_response, edge_case)
                print(f"[Strategy Execution] Hybrid response generated with source: {response_data.get('source', 'unknown')}")
            else:
                # Use edge case handler for comprehensive strategy execution
                print(f"[Strategy Execution] No Ctrl+K results available, using edge case handler")
                response_data = self.edge_case_handler.handle_edge_case(query, edge_case)

            print(f"[Strategy Execution] Success: {response_data['success']}, Source: {response_data.get('source', 'unknown')}")

            return response_data

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")

            # Fallback to InfoGent agent
            try:
                print(f"[Fallback] Using InfoGent agent...")
                from ..agents.agent_types import AgentRequest, IntentType, ConfidenceLevel

                request = AgentRequest(
                    user_input=query,
                    intent_type=IntentType.QUESTION,
                    confidence=ConfidenceLevel.MEDIUM,
                    metadata={}
                )

                infogent_response = self.infogent.process(request)

                return {
                    'success': infogent_response.success,
                    'content': infogent_response.content,
                    'source': 'infogent_fallback',
                    'confidence': 0.5,
                    'citations': [],
                    'metadata': infogent_response.metadata
                }

            except Exception as fallback_error:
                logger.error(f"InfoGent fallback failed: {fallback_error}")

                return {
                    'success': False,
                    'content': self._generate_error_message(query, str(e)),
                    'source': 'error_fallback',
                    'confidence': 0.0,
                    'citations': [],
                    'metadata': {'error': str(e), 'fallback_error': str(fallback_error)}
                }

    def _generate_hybrid_response(self, query: str, hybrid_response: HybridSearchResponse, edge_case: Any) -> Dict[str, Any]:
        """Generate response using immediate Ctrl+K results with enhancement notification."""
        try:
            immediate_results = hybrid_response.immediate_results

            if not immediate_results:
                # Fallback to normal edge case handling
                print(f"[Hybrid Response] No immediate results, falling back to edge case handler")
                return self.edge_case_handler.handle_edge_case(query, edge_case)

            print(f"[Hybrid Response] Generating immediate response from {len(immediate_results)} Ctrl+K results")

            # Use the top result for immediate response
            top_result = immediate_results[0]

            # Generate immediate response content based on the query
            if 'ceph' in query.lower() or 's3' in query.lower() or 'object storage' in query.lower():
                content = f"""**Immediate Result from NRP Search**

**🔍 Found:** {top_result.title}

**📍 Direct Access:** {top_result.url}

**💡 Quick Answer for Ceph-based S3 Object Storage:**

NRP provides access to Ceph-based S3 object storage for users within their namespaces. Based on the search result, you should check the NRP documentation for specific configuration details.

**🚀 Next Steps:**
1. Visit the link above for detailed instructions
2. Check your namespace configuration
3. Review S3 endpoint and credential requirements

"""
            else:
                content = f"""**Immediate Result from NRP Search**

**🔍 Found:** {top_result.title}

**📍 Direct Access:** {top_result.url}

"""
                if top_result.snippet:
                    content += f"**📋 Preview:** {top_result.snippet}\n\n"

            if top_result.section:
                content += f"**📋 Section:** {top_result.section}\n\n"

            # Add information about other results
            if len(immediate_results) > 1:
                content += f"**🔗 Additional Resources:**\n"
                for result in immediate_results[1:]:
                    content += f"- [{result.title}]({result.url})\n"
                content += "\n"

            # Add enhancement notification
            if hybrid_response.enhancement_pending:
                content += f"⚡ **Fast Response Mode:** This immediate result was found in {hybrid_response.search_time:.1f} seconds using NRP's search. Detailed analysis is happening in the background to provide even better responses for future similar queries.\n"

            # Collect citations
            citations = [result.url for result in immediate_results]

            # Use higher confidence for immediate responses to ensure they're used
            confidence_score = max(0.6, top_result.relevance)  # Minimum 0.6 for immediate responses

            print(f"[Hybrid Response] Generated immediate response with confidence {confidence_score:.3f}")

            return {
                'success': True,
                'content': content,
                'source': 'hybrid_ctrlk_immediate',
                'confidence': confidence_score,
                'citations': citations,
                'metadata': {
                    'search_time': hybrid_response.search_time,
                    'enhancement_pending': hybrid_response.enhancement_pending,
                    'immediate_results_count': len(immediate_results),
                    'hybrid_response': True,
                    'original_relevance': top_result.relevance
                }
            }

        except Exception as e:
            logger.error(f"Hybrid response generation failed: {e}")
            # Fallback to normal edge case handling
            return self.edge_case_handler.handle_edge_case(query, edge_case)

    def _assess_response_quality(self, response_data: Dict[str, Any]) -> ResponseQuality:
        """Assess the quality of the generated response."""
        if not response_data['success']:
            return ResponseQuality.FAILED

        confidence = response_data.get('confidence', 0.0)
        content_length = len(response_data.get('content', ''))
        has_citations = len(response_data.get('citations', [])) > 0

        # Quality assessment logic
        if confidence > 0.8 and content_length > 200 and has_citations:
            return ResponseQuality.EXCELLENT
        elif confidence > 0.6 and content_length > 100:
            return ResponseQuality.GOOD
        elif confidence > 0.4 and content_length > 50:
            return ResponseQuality.ACCEPTABLE
        elif content_length > 20:
            return ResponseQuality.POOR
        else:
            return ResponseQuality.FAILED

    def _generate_enhancement_suggestions(self, query: str, edge_case: Any, response_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions for improving the response or knowledge base."""
        suggestions = []

        if hasattr(edge_case, 'enhancement_needed') and edge_case.enhancement_needed:
            suggestions.append("Knowledge base could be enhanced with more information on this topic")

        if response_data.get('confidence', 0) < 0.6:
            suggestions.append("Additional documentation sources could improve response quality")

        if not response_data.get('citations'):
            suggestions.append("Official documentation citations should be added")

        if hasattr(edge_case, 'knowledge_gaps') and edge_case.knowledge_gaps:
            suggestions.extend([f"Address gap: {gap}" for gap in edge_case.knowledge_gaps[:2]])

        return suggestions

    def _calculate_response_metrics(self, start_time: float, response_data: Dict[str, Any],
                                  kb_results: List, edge_case: Any) -> ResponseMetrics:
        """Calculate comprehensive response metrics."""
        end_time = time.time()
        response_time = end_time - start_time

        # Calculate completeness based on response content
        content = response_data.get('content', '')
        completeness = min(1.0, len(content) / 500)  # Normalize to 500 chars for full completeness

        # Calculate source quality
        source_quality = self._calculate_source_quality(response_data)

        # Count knowledge base hits
        kb_hits = len(kb_results) if kb_results else 0

        # Count fresh extractions
        fresh_extractions = 1 if 'extraction' in response_data.get('source', '') else 0

        # Check if fallback was used
        fallback_used = 'fallback' in response_data.get('source', '') or 'synthesis' in response_data.get('source', '')

        return ResponseMetrics(
            confidence=response_data.get('confidence', 0.0),
            completeness=completeness,
            source_quality=source_quality,
            response_time=response_time,
            knowledge_base_hits=kb_hits,
            fresh_extractions=fresh_extractions,
            fallback_used=fallback_used
        )

    def _calculate_source_quality(self, response_data: Dict[str, Any]) -> float:
        """Calculate quality score based on sources used."""
        citations = response_data.get('citations', [])
        source = response_data.get('source', '')

        # High quality sources
        if any('nrp.ai/documentation' in citation for citation in citations):
            return 1.0
        elif 'knowledge_base' in source:
            return 0.8
        elif 'extraction' in source:
            return 0.7
        elif 'synthesis' in source:
            return 0.5
        else:
            return 0.3

    def _update_performance_stats(self, response_data: Dict[str, Any], metrics: ResponseMetrics):
        """Update performance statistics."""
        self.performance_stats['total_queries'] += 1

        if response_data['success']:
            self.performance_stats['successful_responses'] += 1
        else:
            self.performance_stats['failed_responses'] += 1

        self.performance_stats['kb_hits'] += metrics.knowledge_base_hits
        self.performance_stats['fresh_extractions'] += metrics.fresh_extractions

        if metrics.fallback_used:
            self.performance_stats['fallback_responses'] += 1

    def _log_response(self, query: str, result: ResponseResult):
        """Log response for analysis and improvement."""
        log_entry = {
            'timestamp': time.time(),
            'query': query[:100],  # Truncate for privacy
            'success': result.success,
            'quality': result.quality.value,
            'confidence': result.metrics.confidence,
            'response_time': result.metrics.response_time,
            'citations_count': len(result.citations),
            'fallback_used': result.metrics.fallback_used
        }

        self.response_history.append(log_entry)

        # Keep only last 100 entries
        if len(self.response_history) > 100:
            self.response_history = self.response_history[-100:]

    def _emergency_fallback_response(self, query: str, error: str) -> ResponseResult:
        """Generate emergency fallback response when everything fails."""
        content = f"""I apologize, but I encountered an error while processing your query: "{query}"

This appears to be a system error. Please try:

1. **Rephrasing your question** with more specific terms
2. **Checking the official NRP documentation** at https://nrp.ai/documentation/
3. **Contacting NRP support** if this is an urgent issue

**Available Topics I Can Help With:**
- GPU workload configuration and management
- FPGA and SmartNIC workflows
- Kubernetes deployment on NRP
- Storage and networking configuration
- Administrative procedures and policies

**Error Details:** {error[:100]}...
"""

        return ResponseResult(
            success=False,
            content=content,
            quality=ResponseQuality.FAILED,
            metrics=ResponseMetrics(
                confidence=0.0,
                completeness=0.3,  # At least provides some guidance
                source_quality=0.1,
                response_time=0.0,
                knowledge_base_hits=0,
                fresh_extractions=0,
                fallback_used=True
            ),
            citations=['https://nrp.ai/documentation/'],
            metadata={'error': error, 'emergency_fallback': True},
            enhancement_suggestions=['System error needs investigation']
        )

    def _generate_error_message(self, query: str, error: str) -> str:
        """Generate helpful error message."""
        return f"""I encountered an error while processing your query about: "{query}"

**What I tried:**
- Searched the knowledge base for relevant information
- Attempted to extract fresh information from NRP documentation
- Applied fallback strategies for edge cases

**Suggestions:**
- Try rephrasing your question with more specific technical terms
- Check if your query relates to: GPU, FPGA, storage, networking, or Kubernetes
- Visit the official NRP documentation: https://nrp.ai/documentation/

**Error:** {error[:100]}...
"""

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and statistics."""
        stats = self.performance_stats.copy()

        if stats['total_queries'] > 0:
            stats['success_rate'] = stats['successful_responses'] / stats['total_queries']
            stats['fallback_rate'] = stats['fallback_responses'] / stats['total_queries']
        else:
            stats['success_rate'] = 0.0
            stats['fallback_rate'] = 0.0

        # Recent performance
        recent_history = self.response_history[-20:] if self.response_history else []
        if recent_history:
            stats['recent_avg_response_time'] = sum(h['response_time'] for h in recent_history) / len(recent_history)
            stats['recent_success_rate'] = sum(1 for h in recent_history if h['success']) / len(recent_history)
        else:
            stats['recent_avg_response_time'] = 0.0
            stats['recent_success_rate'] = 0.0

        return stats

    def suggest_system_improvements(self) -> List[str]:
        """Suggest system improvements based on performance data."""
        suggestions = []
        stats = self.get_performance_summary()

        if stats['success_rate'] < 0.8:
            suggestions.append("Consider running comprehensive documentation scraping to improve knowledge base")

        if stats['fallback_rate'] > 0.3:
            suggestions.append("High fallback usage indicates need for more comprehensive templates")

        if stats.get('recent_avg_response_time', 0) > 2.0:
            suggestions.append("Response times are high - consider optimizing search indices")

        if stats['kb_hits'] < stats['total_queries'] * 0.5:
            suggestions.append("Low knowledge base hit rate - more proactive content extraction needed")

        return suggestions


# Convenience function for direct usage
def generate_comprehensive_response(query: str, user_context: Dict = None) -> ResponseResult:
    """Generate comprehensive response using the full pipeline."""
    pipeline = ResponsePipeline()
    return pipeline.generate_response(query, user_context)


if __name__ == "__main__":
    # Test the response pipeline
    pipeline = ResponsePipeline()

    test_queries = [
        "How do users flash an Alveo FPGA via the ESnet SmartNIC workflow on NRP?",
        "Can I run jobs indefinitely on the cluster?",
        "How do I request A100 GPUs for my workload?",
        "What is the meaning of life?",  # Edge case - unrelated
        "foobar baz quux",  # Edge case - nonsense
    ]

    print("Testing Response Pipeline")
    print("=" * 50)

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = pipeline.generate_response(query)
        print(f"Success: {result.success}")
        print(f"Quality: {result.quality.value}")
        print(f"Confidence: {result.metrics.confidence:.3f}")
        print(f"Response Time: {result.metrics.response_time:.3f}s")
        print(f"Citations: {len(result.citations)}")

    print(f"\nPerformance Summary:")
    summary = pipeline.get_performance_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(f"\nSuggested Improvements:")
    for suggestion in pipeline.suggest_system_improvements():
        print(f"  - {suggestion}")