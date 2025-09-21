#!/usr/bin/env python3
"""
Fast INFOGENT Agent
==================

Optimized INFOGENT agent that uses pre-built knowledge base for fast responses.

Key improvements:
1. Uses pre-built knowledge base instead of real-time extraction
2. Fast lookup and response generation
3. Only does fresh extraction when needed
4. Continuous background updates
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .agent_types import BaseAgent, AgentRequest, AgentResponse, IntentType, ConfidenceLevel
from ..core.fast_knowledge_builder import FastKnowledgeBuilder, ensure_knowledge_base_built
from ..core.nrp_init import init_chat_model

@dataclass
class FastInfoPack:
    """Fast aggregated information pack."""
    templates: List[Dict[str, Any]]
    knowledge_entries: List[Dict[str, Any]]
    warnings: List[str]
    citations: List[str]
    gpu_specific: bool
    confidence: float

class FastInfogentAgent(BaseAgent):
    """
    Fast INFOGENT agent using pre-built knowledge base.

    Process:
    1. Quick search pre-built knowledge base
    2. Generate response from cached knowledge
    3. Only do fresh extraction if knowledge is insufficient
    4. Provide fast, accurate responses
    """

    def __init__(self):
        # Initialize fast knowledge builder
        self.knowledge_builder = ensure_knowledge_base_built()
        self.llm = init_chat_model()

        # NRP defaults for fast application
        self.nrp_defaults = {
            "ingress_class": "haproxy",
            "storage_class_rwo": "rook-ceph-block",
            "storage_class_rwx": "rook-cephfs",
            "default_namespace": "gsoc",
            "gpu_resource": "nvidia.com/gpu",
            "gpu_a100_resource": "nvidia.com/a100",
            "gpu_v100_resource": "nvidia.com/v100"
        }

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return request.intent_type == IntentType.QUESTION

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process request using fast knowledge base lookup.

        Steps:
        1. Quick search knowledge base
        2. Aggregate results
        3. Generate fast response
        4. Return with metadata
        """
        try:
            print(f"[Fast INFOGENT] Processing: {request.user_input}")

            # Step 1: Quick search knowledge base
            search_results = self._quick_search_knowledge(request.user_input)

            # Step 2: Check if we have sufficient knowledge
            knowledge_sufficient = self._is_knowledge_sufficient(search_results, request.user_input)

            if not knowledge_sufficient:
                print(f"[Fast INFOGENT] Insufficient knowledge, falling back to fresh extraction")
                return self._fallback_to_fresh_extraction(request)

            # Step 3: Fast aggregation
            info_pack = self._fast_aggregate_information(search_results, request.user_input)

            # Step 4: Generate response
            answer = self._generate_fast_response(info_pack, request)

            return AgentResponse(
                success=True,
                content=answer,
                agent_type="FAST_INFOGENT",
                confidence=ConfidenceLevel.HIGH if info_pack.confidence > 0.7 else ConfidenceLevel.MEDIUM,
                metadata={
                    "search_results": len(search_results),
                    "templates_used": len(info_pack.templates),
                    "knowledge_used": len(info_pack.knowledge_entries),
                    "gpu_specific": info_pack.gpu_specific,
                    "confidence": info_pack.confidence,
                    "response_time": "fast"
                },
                follow_up_suggestions=self._generate_fast_follow_ups(info_pack, request)
            )

        except Exception as e:
            print(f"[!] Fast INFOGENT processing failed: {e}")
            return AgentResponse(
                success=False,
                content=f"Fast information gathering failed: {str(e)}",
                agent_type="FAST_INFOGENT",
                confidence=ConfidenceLevel.LOW,
                metadata={"error": str(e)},
                follow_up_suggestions=["Try rephrasing your question", "Be more specific about the topic"]
            )

    def _quick_search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Quick search of the knowledge base."""
        try:
            results = self.knowledge_builder.quick_search(query, limit=10)
            print(f"[Fast INFOGENT] Found {len(results)} knowledge base results")
            return results
        except Exception as e:
            print(f"[!] Knowledge base search failed: {e}")
            return []

    def _is_knowledge_sufficient(self, results: List[Dict[str, Any]], query: str) -> bool:
        """Check if we have sufficient knowledge to answer the query."""
        if len(results) == 0:
            return False

        # Check for high-relevance results
        high_relevance_count = sum(1 for r in results if r.get('relevance', 0) > 0.6)
        if high_relevance_count < 2:
            return False

        # For GPU queries, ensure we have GPU-specific content
        query_lower = query.lower()
        if any(gpu_term in query_lower for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
            gpu_results = [r for r in results if r.get('gpu_specific', False) or 'gpu' in r.get('content', '').lower()]
            if len(gpu_results) == 0:
                return False

        return True

    def _fast_aggregate_information(self, results: List[Dict[str, Any]], query: str) -> FastInfoPack:
        """Fast aggregation of search results."""
        templates = []
        knowledge_entries = []
        warnings = []
        citations = set()
        gpu_specific = False

        # Process results
        for result in results:
            if result['type'] == 'template':
                templates.append(result)
                if result.get('warnings'):
                    warnings.extend(result['warnings'])
                if result.get('gpu_specific'):
                    gpu_specific = True
            else:  # knowledge entry
                knowledge_entries.append(result)

            citations.add(result['source_url'])

        # Calculate overall confidence
        avg_relevance = sum(r.get('relevance', 0) for r in results) / len(results) if results else 0
        confidence = min(1.0, avg_relevance + (0.2 if gpu_specific else 0))

        return FastInfoPack(
            templates=templates[:3],  # Limit to top 3
            knowledge_entries=knowledge_entries[:3],
            warnings=list(set(warnings))[:5],  # Deduplicate and limit
            citations=list(citations),
            gpu_specific=gpu_specific,
            confidence=confidence
        )

    def _generate_fast_response(self, pack: FastInfoPack, request: AgentRequest) -> str:
        """Generate fast response from aggregated information."""
        try:
            # Build context efficiently
            context_parts = []

            # Add templates
            if pack.templates:
                context_parts.append("Available Configuration Templates:")
                for i, template in enumerate(pack.templates, 1):
                    context_parts.append(f"{i}. {template['title']}")
                    context_parts.append(f"   Resource: {template.get('resource_type', 'unknown')}")
                    if template.get('yaml_snippet'):
                        yaml_preview = template['yaml_snippet'][:200] + "..." if len(template['yaml_snippet']) > 200 else template['yaml_snippet']
                        context_parts.append(f"   YAML: {yaml_preview}")

            # Add knowledge entries
            if pack.knowledge_entries:
                context_parts.append("\nRelevant Information:")
                for entry in pack.knowledge_entries:
                    context_parts.append(f"• {entry['content'][:150]}")

            # Add warnings prominently
            warnings_text = ""
            if pack.warnings:
                warnings_text = f"\nIMPORTANT WARNINGS:\n" + "\n".join(f"⚠️ {warning}" for warning in pack.warnings[:3])

            # Apply NRP defaults
            nrp_defaults_text = self._get_relevant_nrp_defaults(request.user_input)

            # Generate response using LLM
            prompt = f"""Answer this NRP Kubernetes question: "{request.user_input}"

Context:
{chr(10).join(context_parts)}

{warnings_text}

NRP Default Settings:
{nrp_defaults_text}

Requirements:
1. Provide a clear, direct answer
2. Include specific configuration examples
3. Highlight any warnings prominently
4. Mention NRP-specific settings
5. Be concise but complete

Format as markdown."""

            response = self.llm.invoke(prompt)
            answer = response.content

            # Add structured sections
            if pack.warnings:
                answer += f"\n\n## ⚠️ Important Warnings\n"
                for warning in pack.warnings[:3]:
                    answer += f"- {warning}\n"

            # Add citations
            if pack.citations:
                answer += f"\n\n## Sources\n"
                for i, citation in enumerate(pack.citations, 1):
                    answer += f"{i}. {citation}\n"

            return answer

        except Exception as e:
            print(f"[!] Fast response generation failed: {e}")
            return self._generate_fallback_response(pack, request)

    def _get_relevant_nrp_defaults(self, query: str) -> str:
        """Get relevant NRP defaults based on query."""
        query_lower = query.lower()
        relevant_defaults = []

        # Always include namespace
        relevant_defaults.append(f"- Default namespace: {self.nrp_defaults['default_namespace']}")

        # GPU defaults
        if any(gpu_term in query_lower for gpu_term in ['gpu', 'nvidia', 'cuda']):
            relevant_defaults.append(f"- GPU resource: {self.nrp_defaults['gpu_resource']}")

            if 'a100' in query_lower:
                relevant_defaults.append(f"- A100 resource: {self.nrp_defaults['gpu_a100_resource']}")
            elif 'v100' in query_lower:
                relevant_defaults.append(f"- V100 resource: {self.nrp_defaults['gpu_v100_resource']}")

        # Storage defaults
        if any(storage_term in query_lower for storage_term in ['storage', 'volume', 'pvc']):
            relevant_defaults.append(f"- Storage class (RWO): {self.nrp_defaults['storage_class_rwo']}")
            relevant_defaults.append(f"- Storage class (RWX): {self.nrp_defaults['storage_class_rwx']}")

        # Networking defaults
        if any(net_term in query_lower for net_term in ['ingress', 'load']):
            relevant_defaults.append(f"- Ingress class: {self.nrp_defaults['ingress_class']}")

        return "\n".join(relevant_defaults)

    def _generate_fast_follow_ups(self, pack: FastInfoPack, request: AgentRequest) -> List[str]:
        """Generate fast follow-up suggestions."""
        suggestions = []

        # GPU-specific follow-ups
        if pack.gpu_specific:
            suggestions.extend([
                "Need specific GPU resource configuration examples?",
                "Want to see GPU job scheduling best practices?",
                "Looking for GPU troubleshooting guidance?"
            ])

        # Template-based follow-ups
        if pack.templates:
            suggestions.append("Want to see the complete YAML configuration?")

        # Warning-based follow-ups
        if pack.warnings:
            suggestions.append("Need more details about these warnings?")

        # General follow-ups
        suggestions.extend([
            "Need help with deployment steps?",
            "Looking for more examples?"
        ])

        return suggestions[:4]

    def _generate_fallback_response(self, pack: FastInfoPack, request: AgentRequest) -> str:
        """Generate fallback response when LLM fails."""
        response = f"# {request.user_input}\n\n"

        if pack.templates:
            response += "## Available Templates\n\n"
            for template in pack.templates:
                response += f"### {template['title']}\n"
                response += f"**Resource Type:** {template.get('resource_type', 'unknown')}\n\n"
                if template.get('yaml_snippet'):
                    response += f"```yaml\n{template['yaml_snippet']}\n```\n\n"

        if pack.warnings:
            response += "## ⚠️ Important Warnings\n\n"
            for warning in pack.warnings:
                response += f"- {warning}\n"

        if pack.knowledge_entries:
            response += "\n## Additional Information\n\n"
            for entry in pack.knowledge_entries:
                response += f"- {entry['content']}\n"

        response += f"\n**Sources:** {', '.join(pack.citations)}"

        return response

    def _fallback_to_fresh_extraction(self, request: AgentRequest) -> AgentResponse:
        """Fallback to the original enhanced infogent agent when knowledge is insufficient."""
        try:
            # Import here to avoid circular dependency
            from .infogent_agent import InfogentAgent

            print(f"[Fast INFOGENT] Falling back to full extraction for: {request.user_input}")

            # Use the original enhanced agent
            enhanced_agent = InfogentAgent()
            response = enhanced_agent.process(request)

            # Update response metadata to indicate fallback
            response.metadata = response.metadata or {}
            response.metadata['fallback_used'] = True
            response.metadata['response_time'] = 'slow'

            return response

        except Exception as e:
            print(f"[!] Fallback to enhanced infogent failed: {e}")
            return AgentResponse(
                success=False,
                content="I encountered an issue processing your request. Please try rephrasing your question.",
                agent_type="FAST_INFOGENT_FALLBACK",
                confidence=ConfidenceLevel.LOW,
                metadata={"fallback_error": str(e)},
                follow_up_suggestions=["Try asking a more specific question", "Rephrase your query"]
            )

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "Fast answers using pre-built knowledge base",
            "GPU-specific guidance with A100/V100 examples",
            "Quick YAML template retrieval",
            "Instant warning and best practice lookup",
            "NRP-specific configuration defaults",
            "Fallback to deep extraction when needed"
        ]

    def force_knowledge_refresh(self) -> bool:
        """Force refresh of the knowledge base."""
        try:
            print("[Fast INFOGENT] Forcing knowledge base refresh...")
            success = self.knowledge_builder.build_knowledge_base(force_rebuild=True)
            if success:
                print("[Fast INFOGENT] Knowledge base refreshed successfully")
            return success
        except Exception as e:
            print(f"[!] Knowledge refresh failed: {e}")
            return False

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return self.knowledge_builder.get_stats()


def init_fast_infogent_agent() -> FastInfogentAgent:
    """Initialize the fast INFOGENT agent."""
    return FastInfogentAgent()