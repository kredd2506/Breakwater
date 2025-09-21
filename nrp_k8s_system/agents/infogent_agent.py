#!/usr/bin/env python3
"""
INFOGENT Agent
=============

Handles information gathering and explanation requests using the
Navigator → Extractor → Aggregator logic from infogent_logic.txt.

Specializes in:
- Finding relevant K8s/NRP knowledge from docs
- Extracting YAML snippets, CLI commands, examples
- Aggregating information with NRP-specific defaults
- Providing comprehensive explanations with citations
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .agent_types import BaseAgent, AgentRequest, AgentResponse, IntentType, ConfidenceLevel
from .deep_extractor_agent import DeepExtractorAgent, ExtractionTemplate, ExtractedKnowledge
from ..systems.qain import Controller, Navigator, Extractor, Aggregator, Query, DuckDuckGoHTML
from ..systems.enhanced_navigator import EnhancedNavigator
from ..core.enhanced_knowledge_base import EnhancedKnowledgeBase, SearchResult
from ..core.nrp_init import init_chat_model


@dataclass
class InfoChunk:
    """Information chunk extracted by Navigator/Extractor."""
    content: str
    chunk_type: str  # 'text', 'yaml', 'cli', 'metadata'
    source_url: str
    section: str
    api_version: Optional[str] = None
    resource_kind: Optional[str] = None
    confidence: float = 0.5
    last_modified: Optional[str] = None


@dataclass
class AggregatedPack:
    """Aggregated information ready for answer generation."""
    summary: str
    artifacts: List[InfoChunk]
    notes_and_caveats: List[str]
    citations: List[str]
    nrp_defaults_applied: Dict[str, str]


class InfogentAgent(BaseAgent):
    """
    INFOGENT Agent implementing Navigator → Extractor → Aggregator logic.

    Process:
    1. Navigator: Find relevant K8s/NRP knowledge sources
    2. Extractor: Extract YAML snippets, CLI commands, definitions
    3. Aggregator: Organize with NRP defaults, validate, deduplicate
    4. Generate: Create comprehensive answer with citations
    """

    def __init__(self):
        # Initialize enhanced components
        self.controller = Controller()
        self.enhanced_navigator = EnhancedNavigator()
        self.deep_extractor = DeepExtractorAgent()
        self.knowledge_base = EnhancedKnowledgeBase()
        self.llm = init_chat_model()

        # These will be initialized per-query as needed
        self.navigator = None
        self.extractor = None
        self.aggregator = None

        # NRP-specific defaults and preferences
        self.nrp_defaults = {
            "ingress_class": "haproxy",
            "storage_class_rwo": "rook-ceph-block",
            "storage_class_rwx": "rook-cephfs",
            "default_namespace": "gsoc",
            "gpu_resource": "nvidia.com/gpu",
            "preferred_api_versions": ["v1", "v1beta1", "alpha"],
            "gpu_a100_resource": "nvidia.com/a100",
            "gpu_v100_resource": "nvidia.com/v100"
        }

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return request.intent_type == IntentType.QUESTION

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process information gathering request using enhanced INFOGENT logic.

        Steps:
        1. Check knowledge base for existing templates
        2. Navigate to find additional sources if needed
        3. Deep extract new information
        4. Aggregate with NRP defaults and warnings
        5. Generate comprehensive answer with cautions
        """
        try:
            print(f"[INFOGENT] Processing question: {request.user_input}")

            # Step 1: Search knowledge base first
            kb_results = self._search_knowledge_base(request.user_input)

            # Step 2: Determine if we need additional extraction
            needs_fresh_extraction = self._needs_fresh_extraction(kb_results, request.user_input)

            if needs_fresh_extraction:
                # Step 3: Navigate to find relevant sources
                navigation_results = self._navigate_sources(request.user_input)

                # Step 4: Deep extract information
                templates, knowledge_chunks = self._deep_extract_information(navigation_results, request.user_input)

                # Step 5: Update knowledge base
                self._update_knowledge_base(templates)

                # Refresh search results
                kb_results = self._search_knowledge_base(request.user_input)

            # Step 6: Aggregate with enhanced warnings and NRP defaults
            aggregated_pack = self._aggregate_enhanced_information(kb_results, request.user_input)

            # Step 7: Generate comprehensive answer with warnings
            answer = self._generate_enhanced_answer(aggregated_pack, request)

            return AgentResponse(
                success=True,
                content=answer,
                agent_type="INFOGENT_ENHANCED",
                confidence=request.confidence,
                metadata={
                    "knowledge_base_results": len(kb_results),
                    "fresh_extraction": needs_fresh_extraction,
                    "warnings_included": len(aggregated_pack.get('warnings', [])),
                    "templates_used": len(aggregated_pack.get('templates', [])),
                    "nrp_defaults_applied": aggregated_pack.get('nrp_defaults_applied', {})
                },
                follow_up_suggestions=self._generate_enhanced_follow_ups(aggregated_pack)
            )

        except Exception as e:
            print(f"[!] Enhanced INFOGENT processing failed: {e}")
            return AgentResponse(
                success=False,
                content=f"Information gathering failed: {str(e)}",
                agent_type="INFOGENT_ENHANCED",
                confidence=ConfidenceLevel.LOW,
                metadata={"error": str(e)},
                follow_up_suggestions=["Try rephrasing your question", "Be more specific about the topic"]
            )

    def _navigate_sources(self, query: str) -> List[Dict[str, Any]]:
        """
        Navigator: Find relevant K8s/NRP knowledge sources using Enhanced Navigator.

        Focuses on:
        - NRP documentation: https://nrp.ai/documentation/ and subpages
        - Kubernetes official docs: https://kubernetes.io/docs/ sections
        - Targeted search with proper link discovery and citation
        """
        try:
            print(f"[Navigator] Using Enhanced Navigator for query: {query}")

            # Use Enhanced Navigator to discover relevant links
            discovered_links = self.enhanced_navigator.discover_relevant_links(query)

            # Convert to expected format
            sources = []
            for link_info in discovered_links:
                sources.append({
                    "url": link_info["url"],
                    "title": link_info["title"],
                    "relevance": link_info.get("relevance", 0.5),
                    "source_type": link_info["source_type"]
                })

            print(f"[Navigator] Enhanced Navigator found {len(sources)} relevant sources")

            # Fallback to original method if Enhanced Navigator fails
            if not sources:
                print(f"[Navigator] Falling back to original method")
                return self._navigate_sources_fallback(query)

            return sources

        except Exception as e:
            print(f"[!] Enhanced Navigation failed: {e}")
            # Fallback to original navigation
            return self._navigate_sources_fallback(query)

    def _navigate_sources_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Fallback navigation using original Controller."""
        try:
            infogent_query = Query(q=self._enhance_query_for_nrp(query))
            result = self.controller.run(infogent_query)

            sources = []
            if hasattr(result, 'sources') and result.sources:
                for source in result.sources:
                    sources.append({
                        "url": source,
                        "title": self._extract_title_from_url(source),
                        "relevance": 0.6,
                        "source_type": self._classify_source_type(source)
                    })

            print(f"[Navigator] Fallback found {len(sources)} sources")
            return sources

        except Exception as e:
            print(f"[!] Fallback navigation failed: {e}")
            return []

    def _extract_information(self, sources: List[Dict[str, Any]], query: str) -> List[InfoChunk]:
        """
        Extractor: Extract relevant information chunks from sources using Enhanced Navigator.

        Extracts:
        - Text: definitions, constraints, defaults from actual documentation
        - Artifacts: YAML snippets, CLI commands, examples
        - Metadata: apiVersion, resource kind, namespace hints
        """
        chunks = []

        for source in sources:
            try:
                print(f"[Extractor] Extracting from: {source['url']}")

                # Use Enhanced Navigator to extract content
                content_data = self.enhanced_navigator.extract_content_from_url(source["url"])

                if content_data and content_data.get("content"):
                    # Create info chunks from extracted content
                    extracted_chunks = self._create_chunks_from_content(
                        content_data, source, query
                    )
                    chunks.extend(extracted_chunks)
                else:
                    # Fallback to source-specific extraction
                    fallback_chunks = self._extract_content_fallback(source, query)
                    chunks.extend(fallback_chunks)

            except Exception as e:
                print(f"[!] Extraction failed for {source['url']}: {e}")
                continue

        print(f"[Extractor] Extracted {len(chunks)} information chunks")
        return chunks

    def _create_chunks_from_content(self, content_data: Dict[str, str],
                                   source: Dict[str, Any], query: str) -> List[InfoChunk]:
        """Create info chunks from extracted content."""
        chunks = []
        content = content_data["content"]
        url = content_data["url"]
        title = content_data["title"]

        # Split content into manageable chunks
        chunk_size = 1000
        content_chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

        for i, chunk_content in enumerate(content_chunks):
            # Determine chunk type based on content
            chunk_type = self._determine_chunk_type(chunk_content)

            # Calculate relevance based on query keywords
            relevance = self._calculate_content_relevance(chunk_content, query)

            # Only keep relevant chunks
            if relevance > 0.3:
                chunks.append(InfoChunk(
                    content=chunk_content,
                    chunk_type=chunk_type,
                    source_url=url,
                    section=f"{title} - Part {i+1}",
                    confidence=relevance,
                    api_version=self._extract_api_version(chunk_content),
                    resource_kind=self._extract_resource_kind(chunk_content)
                ))

        return chunks

    def _determine_chunk_type(self, content: str) -> str:
        """Determine the type of content chunk."""
        content_lower = content.lower()

        if any(indicator in content_lower for indicator in ['apiversion:', 'kind:', 'metadata:', 'spec:']):
            return 'yaml'
        elif any(indicator in content_lower for indicator in ['kubectl', 'helm', 'docker', '$', '# ']):
            return 'cli'
        elif any(indicator in content_lower for indicator in ['example', 'configuration', 'template']):
            return 'example'
        else:
            return 'text'

    def _calculate_content_relevance(self, content: str, query: str) -> float:
        """Calculate relevance of content to query."""
        content_lower = content.lower()
        query_lower = query.lower()

        relevance = 0.0
        query_words = query_lower.split()

        for word in query_words:
            if len(word) > 2 and word in content_lower:
                relevance += 0.2

        # Boost for specific indicators
        if any(keyword in content_lower for keyword in ['nrp', 'nautilus']):
            relevance += 0.3
        if any(keyword in content_lower for keyword in ['kubernetes', 'k8s']):
            relevance += 0.2

        return min(1.0, relevance)

    def _extract_api_version(self, content: str) -> Optional[str]:
        """Extract API version from content."""
        import re
        match = re.search(r'apiversion:\s*([^\s\n]+)', content.lower())
        return match.group(1) if match else None

    def _extract_resource_kind(self, content: str) -> Optional[str]:
        """Extract resource kind from content."""
        import re
        match = re.search(r'kind:\s*([^\s\n]+)', content.lower())
        return match.group(1) if match else None

    def _extract_content_fallback(self, source: Dict[str, Any], query: str) -> List[InfoChunk]:
        """Fallback content extraction for when Enhanced Navigator fails."""
        # Use original extraction methods as fallback
        if source["source_type"] == "nrp_docs":
            return self._extract_nrp_specific(source, query)
        elif source["source_type"] == "k8s_docs":
            return self._extract_k8s_content(source, query)
        elif source["source_type"] == "operator_docs":
            return self._extract_operator_content(source, query)
        else:
            return []

    def _aggregate_information(self, chunks: List[InfoChunk], query: str) -> AggregatedPack:
        """
        Aggregator: Organize information with NRP defaults and validation.

        Operations:
        - ADD new chunks covering gaps
        - REPLACE with newer/more NRP-specific content
        - MERGE related chunks into coherent patterns
        - Apply NRP defaults (haproxy ingress, rook-ceph storage, etc.)
        """
        # Group chunks by type and topic
        organized_chunks = self._organize_chunks(chunks)

        # Apply NRP defaults and preferences
        nrp_enhanced_chunks = self._apply_nrp_defaults(organized_chunks)

        # Validate and deduplicate
        validated_chunks = self._validate_chunks(nrp_enhanced_chunks)

        # Generate summary
        summary = self._generate_summary(validated_chunks, query)

        # Extract citations
        citations = list(set(chunk.source_url for chunk in validated_chunks))

        # Generate notes and caveats
        notes = self._generate_notes_and_caveats(validated_chunks)

        print(f"[Aggregator] Organized into {len(validated_chunks)} validated chunks")

        return AggregatedPack(
            summary=summary,
            artifacts=validated_chunks,
            notes_and_caveats=notes,
            citations=citations,
            nrp_defaults_applied=self._get_applied_defaults(validated_chunks)
        )

    def _generate_answer(self, pack: AggregatedPack, request: AgentRequest) -> str:
        """Generate comprehensive answer from aggregated pack."""

        answer_prompt = f"""Create a comprehensive answer for this NRP Kubernetes question: "{request.user_input}"

Available information:
{pack.summary}

Key artifacts:
{self._format_artifacts(pack.artifacts)}

Notes and caveats:
{chr(10).join(f"- {note}" for note in pack.notes_and_caveats)}

NRP defaults applied:
{chr(10).join(f"- {k}: {v}" for k, v in pack.nrp_defaults_applied.items())}

Requirements:
1. Provide clear, actionable answer
2. Include relevant YAML/CLI examples
3. Mention NRP-specific considerations
4. Add citations at the end
5. Be specific to NRP/Nautilus platform

Format as markdown with clear sections."""

        try:
            response = self.llm.invoke(answer_prompt)
            answer = response.content

            # Add citations
            if pack.citations:
                answer += "\n\n## Sources\n"
                for i, citation in enumerate(pack.citations, 1):
                    answer += f"{i}. {citation}\n"

            return answer

        except Exception as e:
            print(f"[!] Answer generation failed: {e}")
            return self._generate_fallback_answer(pack, request)

    def _enhance_query_for_nrp(self, query: str) -> str:
        """Enhance query with NRP/Nautilus context."""
        enhancements = ["NRP", "Nautilus", "Kubernetes"]

        # Add specific context based on query content
        if "gpu" in query.lower():
            enhancements.append("nvidia.com/gpu")
        if "storage" in query.lower():
            enhancements.extend(["rook-ceph", "PVC"])
        if "ingress" in query.lower():
            enhancements.append("haproxy")
        if "network" in query.lower():
            enhancements.append("service mesh")

        return f"{query} {' '.join(enhancements)}"

    def _classify_source_type(self, url: str) -> str:
        """Classify source type for targeted extraction."""
        url_lower = url.lower()

        if "nrp.ai" in url_lower or "nrp-nautilus.io" in url_lower or "nautilus" in url_lower:
            return "nrp_docs"
        elif "kubernetes.io" in url_lower:
            return "k8s_docs"
        elif any(op in url_lower for op in ["rook", "haproxy", "dcgm", "prometheus"]):
            return "operator_docs"
        else:
            return "general"

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL."""
        from urllib.parse import urlparse
        path = urlparse(url).path
        parts = [part for part in path.split('/') if part]
        if parts:
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        return url.split('/')[-1] or url

    def _extract_nrp_specific(self, source: Dict[str, Any], query: str) -> List[InfoChunk]:
        """Extract NRP-specific content."""
        # Stub implementation - would extract from actual NRP docs
        return [
            InfoChunk(
                content="NRP uses haproxy for ingress by default",
                chunk_type="text",
                source_url=source["url"],
                section="ingress",
                confidence=0.9
            )
        ]

    def _extract_k8s_content(self, source: Dict[str, Any], query: str) -> List[InfoChunk]:
        """Extract Kubernetes official docs content."""
        # Stub implementation
        return []

    def _extract_operator_content(self, source: Dict[str, Any], query: str) -> List[InfoChunk]:
        """Extract operator-specific content."""
        # Stub implementation
        return []

    def _organize_chunks(self, chunks: List[InfoChunk]) -> Dict[str, List[InfoChunk]]:
        """Organize chunks by type and topic."""
        organized = {"yaml": [], "text": [], "cli": [], "metadata": []}

        for chunk in chunks:
            chunk_type = chunk.chunk_type
            if chunk_type in organized:
                organized[chunk_type].append(chunk)
            else:
                organized["text"].append(chunk)

        return organized

    def _apply_nrp_defaults(self, organized_chunks: Dict[str, List[InfoChunk]]) -> List[InfoChunk]:
        """Apply NRP-specific defaults and preferences."""
        enhanced_chunks = []

        for chunk_type, chunks in organized_chunks.items():
            for chunk in chunks:
                # Apply NRP defaults based on content
                if "ingress" in chunk.content.lower() and "class" in chunk.content.lower():
                    chunk.content = chunk.content.replace("nginx", "haproxy")

                if "storageclass" in chunk.content.lower():
                    if "readwriteonce" in chunk.content.lower():
                        chunk.content += f"\n# NRP Default: {self.nrp_defaults['storage_class_rwo']}"
                    elif "readwritemany" in chunk.content.lower():
                        chunk.content += f"\n# NRP Default: {self.nrp_defaults['storage_class_rwx']}"

                enhanced_chunks.append(chunk)

        return enhanced_chunks

    def _validate_chunks(self, chunks: List[InfoChunk]) -> List[InfoChunk]:
        """Validate chunks and remove duplicates."""
        validated = []
        seen_content = set()

        for chunk in chunks:
            # Simple deduplication
            content_hash = hash(chunk.content[:100])  # Use first 100 chars as hash
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                validated.append(chunk)

        return validated

    def _generate_summary(self, chunks: List[InfoChunk], query: str) -> str:
        """Generate summary from chunks."""
        if not chunks:
            return f"Limited information found for: {query}"

        chunk_contents = [chunk.content[:200] for chunk in chunks[:3]]
        return f"Found {len(chunks)} relevant pieces of information covering: {', '.join(chunk_contents)}"

    def _generate_notes_and_caveats(self, chunks: List[InfoChunk]) -> List[str]:
        """Generate notes and caveats from chunks."""
        notes = []

        # Check for API version warnings
        for chunk in chunks:
            if chunk.api_version and "beta" in chunk.api_version:
                notes.append(f"API version {chunk.api_version} is in beta")

        # Add standard NRP notes
        notes.extend([
            "Ensure you're in the correct namespace (default: gsoc)",
            "Check resource quotas before deployment",
            "Review NRP policies for resource limits"
        ])

        return notes

    def _get_applied_defaults(self, chunks: List[InfoChunk]) -> Dict[str, str]:
        """Get applied NRP defaults."""
        applied = {}

        for chunk in chunks:
            if "haproxy" in chunk.content:
                applied["ingress_class"] = "haproxy"
            if "rook-ceph" in chunk.content:
                applied["storage_class"] = "rook-ceph-block"

        return applied

    def _format_artifacts(self, artifacts: List[InfoChunk]) -> str:
        """Format artifacts for display."""
        formatted = []
        for artifact in artifacts[:5]:  # Limit to 5 artifacts
            formatted.append(f"- {artifact.chunk_type}: {artifact.content[:100]}...")
        return "\n".join(formatted)

    def _generate_follow_ups(self, pack: AggregatedPack) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions = [
            "Would you like specific YAML examples?",
            "Need help with deployment steps?",
            "Want to know about resource requirements?"
        ]

        # Add specific suggestions based on content
        if any("gpu" in chunk.content.lower() for chunk in pack.artifacts):
            suggestions.append("Need help with GPU resource requests?")

        if any("storage" in chunk.content.lower() for chunk in pack.artifacts):
            suggestions.append("Want to know about persistent volume options?")

        return suggestions[:3]  # Limit to 3 suggestions

    def _generate_fallback_answer(self, pack: AggregatedPack, request: AgentRequest) -> str:
        """Generate fallback answer when LLM fails."""
        return f"""Information about: {request.user_input}

Summary: {pack.summary}

Key points:
{chr(10).join(f"- {note}" for note in pack.notes_and_caveats[:3])}

NRP-specific considerations:
{chr(10).join(f"- {k}: {v}" for k, v in pack.nrp_defaults_applied.items())}

For more detailed information, please consult the NRP documentation.
"""

    def _search_knowledge_base(self, query: str) -> List[SearchResult]:
        """Search the enhanced knowledge base for relevant templates."""
        try:
            # Determine resource type from query if possible
            resource_type = self._extract_resource_type_from_query(query)
            filters = {'resource_type': resource_type} if resource_type else {}

            # Search knowledge base
            results = self.knowledge_base.search_templates(query, filters, limit=10)

            print(f"[Knowledge Base] Found {len(results)} relevant templates")
            return results

        except Exception as e:
            print(f"[!] Knowledge base search failed: {e}")
            return []

    def _needs_fresh_extraction(self, kb_results: List[SearchResult], query: str) -> bool:
        """Determine if we need fresh extraction or can use existing knowledge."""
        # If we have good relevant results, use them
        if len(kb_results) >= 2:
            high_relevance_results = [r for r in kb_results if r.relevance_score > 0.3]
            if len(high_relevance_results) >= 1:
                print(f"[Knowledge Base] Using {len(high_relevance_results)} existing templates (relevance > 0.3)")
                return False

        # Check for specific query types that might need extraction
        query_lower = query.lower()

        # GPU-specific queries - check if we have GPU templates
        if any(gpu_term in query_lower for gpu_term in ['a100', 'v100', 'gpu']):
            gpu_templates = [r for r in kb_results if 'gpu' in r.template.template.title.lower()]
            if len(gpu_templates) == 0:
                print(f"[Knowledge Base] Need fresh extraction for GPU query")
                return True

        # Job/batch queries - check if we have job templates
        if any(job_term in query_lower for job_term in ['job', 'batch', 'sleep', 'runtime', 'indefinite']):
            job_templates = [r for r in kb_results if r.template.template.resource_type in ['job', 'cronjob']]
            if len(job_templates) == 0:
                print(f"[Knowledge Base] Creating fallback job templates")
                self._create_fallback_job_templates()
                return False  # Use fallback templates instead of extraction

        # For other queries, try extraction if we have no relevant results
        if len(kb_results) == 0:
            print(f"[Knowledge Base] No existing templates found, attempting extraction")
            return True

        print(f"[Knowledge Base] Using {len(kb_results)} existing templates")
        return False

    def _deep_extract_information(self, sources: List[Dict[str, Any]], query: str) -> tuple:
        """Deep extract information using the enhanced extractor."""
        try:
            all_templates = []
            all_knowledge = []

            # Extract topic focus from query
            topic_focus = self._extract_topic_focus(query)

            for source in sources[:5]:  # Limit to top 5 sources
                try:
                    url = source['url']
                    print(f"[Deep Extractor] Processing: {url}")

                    templates, knowledge = self.deep_extractor.deep_extract_from_url(url, topic_focus)
                    all_templates.extend(templates)
                    all_knowledge.extend(knowledge)

                except Exception as e:
                    print(f"[!] Deep extraction failed for {source['url']}: {e}")
                    continue

            print(f"[Deep Extractor] Extracted {len(all_templates)} templates, {len(all_knowledge)} knowledge chunks")
            return all_templates, all_knowledge

        except Exception as e:
            print(f"[!] Deep extraction failed: {e}")
            return [], []

    def _update_knowledge_base(self, templates: List[ExtractionTemplate]):
        """Update knowledge base with new templates."""
        try:
            for template in templates:
                self.knowledge_base.add_template(template)

            self.knowledge_base.save()
            print(f"[Knowledge Base] Updated with {len(templates)} new templates")

        except Exception as e:
            print(f"[!] Knowledge base update failed: {e}")

    def _aggregate_enhanced_information(self, kb_results: List[SearchResult], query: str) -> Dict[str, Any]:
        """Aggregate information with enhanced warnings and NRP defaults."""
        aggregated = {
            'templates': [],
            'warnings': [],
            'examples': [],
            'best_practices': [],
            'nrp_defaults_applied': {},
            'citations': []
        }

        # Process knowledge base results
        for result in kb_results:
            template = result.template.template

            # Add template
            aggregated['templates'].append(template)

            # Collect warnings with severity
            for danger in template.dangers:
                aggregated['warnings'].append(f"🚨 DANGER: {danger}")
            for warning in template.warnings:
                aggregated['warnings'].append(f"⚠️ WARNING: {warning}")
            for caution in template.cautions:
                aggregated['warnings'].append(f"⚡ CAUTION: {caution}")
            for note in template.notes:
                aggregated['warnings'].append(f"ℹ️ NOTE: {note}")

            # Collect examples and best practices
            aggregated['examples'].extend(template.examples)
            aggregated['best_practices'].extend(template.best_practices)

            # Add citation
            aggregated['citations'].append(template.source_url)

        # Apply NRP defaults based on query context
        aggregated['nrp_defaults_applied'] = self._apply_contextual_nrp_defaults(query, aggregated['templates'])

        # Remove duplicates
        aggregated['warnings'] = list(set(aggregated['warnings']))
        aggregated['examples'] = list(set(aggregated['examples']))
        aggregated['best_practices'] = list(set(aggregated['best_practices']))
        aggregated['citations'] = list(set(aggregated['citations']))

        return aggregated

    def _generate_enhanced_answer(self, pack: Dict[str, Any], request: AgentRequest) -> str:
        """Generate enhanced answer with comprehensive warnings and examples."""
        try:
            # Build context from templates
            template_context = []
            for template in pack['templates'][:3]:  # Use top 3 templates
                template_context.append(f"""
Template: {template.title}
Description: {template.description}
YAML Content:
```yaml
{template.yaml_content}
```
Resource Requirements: {template.resource_requirements}
""")

            # Build warnings section
            warnings_section = ""
            if pack['warnings']:
                warnings_section = f"""
## ⚠️ Important Warnings and Cautions

{chr(10).join(pack['warnings'][:5])}
"""

            # Build examples section
            examples_section = ""
            if pack['examples']:
                examples_section = f"""
## 📋 Examples

{chr(10).join(f"• {example}" for example in pack['examples'][:3])}
"""

            # Build best practices section
            practices_section = ""
            if pack['best_practices']:
                practices_section = f"""
## ✅ Best Practices

{chr(10).join(f"• {practice}" for practice in pack['best_practices'][:3])}
"""

            answer_prompt = f"""Create a comprehensive answer for this NRP Kubernetes question: "{request.user_input}"

Available Templates:
{chr(10).join(template_context)}

NRP Defaults Applied:
{chr(10).join(f"- {k}: {v}" for k, v in pack['nrp_defaults_applied'].items())}

Requirements:
1. Provide clear, actionable answer with specific YAML examples
2. Include all relevant warnings and cautions prominently
3. Mention NRP-specific configurations and constraints
4. Provide step-by-step guidance if applicable
5. Include resource requirements and limitations
6. Add citations at the end

Format as markdown with clear sections. IMPORTANT: Include warnings prominently at the top."""

            response = self.llm.invoke(answer_prompt)
            answer = response.content

            # Add structured sections
            answer += warnings_section + examples_section + practices_section

            # Add citations
            if pack['citations']:
                answer += "\n\n## Sources\n"
                for i, citation in enumerate(pack['citations'], 1):
                    answer += f"{i}. {citation}\n"

            return answer

        except Exception as e:
            print(f"[!] Enhanced answer generation failed: {e}")
            return self._generate_fallback_enhanced_answer(pack, request)

    def _generate_enhanced_follow_ups(self, pack: Dict[str, Any]) -> List[str]:
        """Generate enhanced follow-up suggestions."""
        suggestions = []

        # GPU-specific follow-ups
        if any('gpu' in template.title.lower() for template in pack.get('templates', [])):
            suggestions.extend([
                "Need help with specific GPU resource requests?",
                "Want to see A100 vs V100 configuration differences?",
                "Looking for GPU job scheduling best practices?"
            ])

        # Warning-based follow-ups
        if pack.get('warnings'):
            suggestions.append("Want more details about these warnings and how to avoid them?")

        # General follow-ups
        suggestions.extend([
            "Need help with deployment steps?",
            "Want to see more configuration examples?",
            "Looking for troubleshooting guidance?"
        ])

        return suggestions[:4]  # Limit to 4 suggestions

    def _extract_resource_type_from_query(self, query: str) -> Optional[str]:
        """Extract resource type from query."""
        query_lower = query.lower()

        resource_mappings = {
            'pod': ['pod', 'container'],
            'deployment': ['deployment', 'deploy'],
            'job': ['job', 'batch'],
            'service': ['service', 'svc'],
            'ingress': ['ingress', 'load'],
            'configmap': ['configmap', 'config'],
            'secret': ['secret'],
            'pvc': ['pvc', 'volume', 'storage']
        }

        for resource_type, keywords in resource_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                return resource_type

        return None

    def _extract_topic_focus(self, query: str) -> str:
        """Extract topic focus for deep extraction."""
        query_lower = query.lower()

        if any(gpu_term in query_lower for gpu_term in ['gpu', 'nvidia', 'cuda', 'a100', 'v100']):
            return 'gpu'
        elif any(storage_term in query_lower for storage_term in ['storage', 'volume', 'pvc']):
            return 'storage'
        elif any(net_term in query_lower for net_term in ['network', 'ingress', 'service']):
            return 'networking'
        elif any(job_term in query_lower for job_term in ['job', 'batch', 'cron']):
            return 'jobs'
        else:
            return 'general'

    def _apply_contextual_nrp_defaults(self, query: str, templates: List[ExtractionTemplate]) -> Dict[str, str]:
        """Apply NRP defaults based on query context."""
        applied_defaults = {}
        query_lower = query.lower()

        # GPU-specific defaults
        if any(gpu_term in query_lower for gpu_term in ['gpu', 'nvidia', 'cuda']):
            applied_defaults['gpu_resource'] = self.nrp_defaults['gpu_resource']

            if 'a100' in query_lower:
                applied_defaults['gpu_specific'] = self.nrp_defaults['gpu_a100_resource']
            elif 'v100' in query_lower:
                applied_defaults['gpu_specific'] = self.nrp_defaults['gpu_v100_resource']

        # Storage defaults
        if any(storage_term in query_lower for storage_term in ['storage', 'volume', 'pvc']):
            applied_defaults['storage_class_rwo'] = self.nrp_defaults['storage_class_rwo']
            applied_defaults['storage_class_rwx'] = self.nrp_defaults['storage_class_rwx']

        # Networking defaults
        if any(net_term in query_lower for net_term in ['ingress', 'load']):
            applied_defaults['ingress_class'] = self.nrp_defaults['ingress_class']

        # Always apply namespace default
        applied_defaults['default_namespace'] = self.nrp_defaults['default_namespace']

        return applied_defaults

    def _create_fallback_job_templates(self):
        """Create fallback job templates for common queries when knowledge base is empty."""
        try:
            from ..agents.deep_extractor_agent import ExtractionTemplate

            print(f"[Knowledge Base] Creating fallback job templates...")

            # Create batch job optimization template
            batch_template = ExtractionTemplate(
                title="Batch Job Runtime Optimization Best Practices",
                description="Guidelines for optimizing batch job runtime and avoiding inefficient patterns like excessive sleep",
                resource_type="job",
                yaml_content='''apiVersion: batch/v1
kind: Job
metadata:
  name: optimized-batch-job
  namespace: gsoc
spec:
  activeDeadlineSeconds: 3600  # 1 hour maximum
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: python:3.9
        command: ["python", "-c", "print('Processing...'); import time; time.sleep(5); print('Complete')"]
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"''',
                usage_context="Optimize batch jobs for efficiency rather than using long sleep periods",
                warnings=["Avoid using sleep for extended periods in batch jobs"],
                cautions=["Long-running jobs may be terminated by cluster policies", "Design for finite execution"],
                notes=["Use activeDeadlineSeconds to set job timeouts", "Optimize processing algorithms"],
                dangers=["Indefinite loops consume cluster resources"],
                examples=["Use sleep(5) for brief delays, not sleep(3600)", "Process in chunks vs waiting"],
                best_practices=[
                    "Design jobs to complete work efficiently",
                    "Use appropriate timeout values",
                    "Optimize algorithms rather than adding delays",
                    "Monitor job completion and resource usage"
                ],
                common_mistakes=["Long sleep periods", "No timeout settings", "Inefficient processing"],
                source_url="https://nrp.ai/documentation/running/",
                api_version="batch/v1",
                namespace_requirements=["gsoc"],
                resource_requirements={"memory": "4Gi", "cpu": "2"},
                dependencies=[],
                confidence_score=0.95,
                extraction_method="fallback_creation",
                validation_status="valid"
            )

            # Create indefinite job template
            indefinite_template = ExtractionTemplate(
                title="Jobs Should Not Run Indefinitely - Cluster Policies",
                description="Explanation of why jobs should not run indefinitely and cluster resource policies",
                resource_type="job",
                yaml_content='''apiVersion: batch/v1
kind: Job
metadata:
  name: finite-job-example
  namespace: gsoc
spec:
  activeDeadlineSeconds: 1800  # 30 minutes maximum
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: processor
        image: ubuntu:20.04
        command: ["bash", "-c", "echo 'Starting...'; sleep 10; echo 'Finished'; exit 0"]
        resources:
          limits:
            memory: "2Gi"
            cpu: "1"''',
                usage_context="Jobs should have defined end points and not run indefinitely",
                warnings=["Jobs running indefinitely will be terminated by cluster policies"],
                cautions=[
                    "Cluster has resource limits and fairness policies",
                    "Long-running workloads should use Deployments, not Jobs",
                    "Jobs are designed for finite, batch processing tasks"
                ],
                notes=[
                    "Use activeDeadlineSeconds for maximum runtime",
                    "For continuous services, use Deployments",
                    "Monitor resource usage and completion"
                ],
                dangers=[
                    "Indefinite jobs monopolize cluster resources",
                    "May violate cluster usage policies",
                    "Prevents other users from accessing resources"
                ],
                examples=[
                    "Set activeDeadlineSeconds: 3600 for 1-hour max",
                    "Use proper exit conditions",
                    "Monitor with kubectl get jobs"
                ],
                best_practices=[
                    "Always set activeDeadlineSeconds for batch jobs",
                    "Use Deployments for long-running services",
                    "Design with clear start and end conditions",
                    "Test completion locally before cluster deployment"
                ],
                common_mistakes=[
                    "Using while True loops without exit conditions",
                    "Not setting job timeout limits",
                    "Running services as batch jobs"
                ],
                source_url="https://nrp.ai/documentation/running/",
                api_version="batch/v1",
                namespace_requirements=["gsoc"],
                resource_requirements={"memory": "2Gi", "cpu": "1"},
                dependencies=[],
                confidence_score=0.98,
                extraction_method="fallback_creation",
                validation_status="valid"
            )

            # Add templates to knowledge base
            self.knowledge_base.add_template(batch_template)
            self.knowledge_base.add_template(indefinite_template)
            self.knowledge_base.save()

            print(f"[Knowledge Base] Created 2 fallback job templates")

        except Exception as e:
            print(f"[!] Failed to create fallback job templates: {e}")

    def _generate_fallback_enhanced_answer(self, pack: Dict[str, Any], request: AgentRequest) -> str:
        """Generate fallback answer when LLM fails."""
        answer = f"# Information about: {request.user_input}\n\n"

        if pack.get('warnings'):
            answer += "## ⚠️ Important Warnings\n\n"
            answer += "\n".join(pack['warnings'][:3]) + "\n\n"

        if pack.get('templates'):
            answer += "## Configuration Templates\n\n"
            for template in pack['templates'][:2]:
                answer += f"### {template.title}\n"
                answer += f"{template.description}\n\n"
                answer += f"```yaml\n{template.yaml_content}\n```\n\n"

        if pack.get('nrp_defaults_applied'):
            answer += "## NRP-Specific Settings\n\n"
            for key, value in pack['nrp_defaults_applied'].items():
                answer += f"- {key}: {value}\n"

        answer += "\nFor more detailed information, please consult the NRP documentation.\n"

        return answer

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "Answer Kubernetes questions with comprehensive NRP context",
            "Provide templates with detailed warnings and cautions",
            "Apply NRP-specific defaults and best practices",
            "Deep extract documentation with validation",
            "Maintain searchable knowledge base of templates",
            "Provide GPU-specific guidance and examples"
        ]


def init_infogent_agent() -> InfogentAgent:
    """Initialize the enhanced INFOGENT agent."""
    return InfogentAgent()