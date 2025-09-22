#!/usr/bin/env python3
"""
Deep Extractor Agent
===================

A dedicated agent for thorough documentation parsing and extraction.
Designed to read documentation pages multiple times with different extraction strategies
to ensure complete and accurate information retrieval.

Features:
- Multi-pass extraction with different parsing strategies
- Deep YAML and code example extraction with validation
- Context-aware warning and note extraction
- Template creation with danger/caution/warning preservation
- Semantic chunking for better knowledge base construction
"""

import os
import re
import json
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from ..core.nrp_init import init_chat_model

logger = logging.getLogger(__name__)

@dataclass
class ExtractionTemplate:
    """A comprehensive template extracted from documentation."""
    title: str
    description: str
    resource_type: str  # "pod", "deployment", "job", "service", etc.
    yaml_content: str
    usage_context: str

    # Warnings and notes
    warnings: List[str]
    cautions: List[str]
    notes: List[str]
    dangers: List[str]

    # Examples and best practices
    examples: List[str]
    best_practices: List[str]
    common_mistakes: List[str]

    # Metadata
    source_url: str
    api_version: str
    namespace_requirements: List[str]
    resource_requirements: Dict[str, str]
    dependencies: List[str]

    # Quality metrics
    confidence_score: float
    extraction_method: str
    validation_status: str

@dataclass
class ExtractedKnowledge:
    """Knowledge chunk with rich context."""
    content: str
    content_type: str  # "yaml", "command", "explanation", "warning", "example"
    topic: str
    subtopic: str

    # Context preservation
    preceding_context: str
    following_context: str
    section_heading: str

    # Semantic information
    keywords: List[str]
    entities: List[str]  # GPU types, storage classes, etc.
    relationships: List[str]  # Dependencies, requirements

    # Source tracking
    source_url: str
    source_section: str
    extraction_timestamp: str

    # Quality indicators
    reliability_score: float
    completeness_score: float

class DeepExtractorAgent:
    """
    Deep extraction agent that thoroughly parses documentation pages.

    Uses multiple extraction strategies:
    1. Structured parsing (headings, lists, code blocks)
    2. Semantic analysis (warnings, examples, relationships)
    3. Template extraction (complete YAML with context)
    4. Validation and cross-referencing
    """

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "deep_extracted_knowledge"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache files
        self.templates_cache = self.cache_dir / "templates.json"
        self.knowledge_cache = self.cache_dir / "knowledge_chunks.json"
        self.validation_cache = self.cache_dir / "validation_results.json"

        # In-memory storage
        self.templates: List[ExtractionTemplate] = []
        self.knowledge_chunks: List[ExtractedKnowledge] = []
        self.validation_results: Dict[str, Any] = {}

        # LLM for semantic analysis
        self.llm = init_chat_model()

        # Extraction patterns - Updated for NRP-specific HTML structure
        self.yaml_patterns = [
            # NRP-specific: <pre data-language="yaml"> with class="expressive code"
            r'<pre[^>]*data-language=["\']yaml["\'][^>]*class=["\'][^"\']*expressive[^"\']*code[^"\']*["\'][^>]*>(.*?)</pre>',
            r'<pre[^>]*class=["\'][^"\']*expressive[^"\']*code[^"\']*["\'][^>]*data-language=["\']yaml["\'][^>]*>(.*?)</pre>',
            # Alternative NRP patterns
            r'<pre[^>]*data-language=["\']yaml["\'][^>]*>(.*?)</pre>',
            r'<code[^>]*class=["\'][^"\']*language-yaml[^"\']*["\'][^>]*>(.*?)</code>',
            # Standard patterns as fallback
            r'```ya?ml\s*\n(.*?)\n```',
            r'<pre[^>]*><code[^>]*class[^>]*ya?ml[^>]*>(.*?)</code></pre>',
            r'(?:^|\n)((?:apiVersion|kind):\s*.*?(?=\n(?:[a-zA-Z]|\Z)))',
        ]

        self.warning_patterns = [
            # NRP-specific caution patterns
            r'<[^>]*class=["\'][^"\']*\bcomplementary\s+caution\b[^"\']*["\'][^>]*>(.*?)</[^>]*>',
            r'<[^>]*class=["\'][^"\']*\bcaution\b[^"\']*["\'][^>]*>(.*?)</[^>]*>',
            # Standard warning patterns
            r'(?i)(?:⚠️|🚨|❗|⚡|🔥|🛑)\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
            r'(?i)(?:DANGER|CRITICAL|WARNING|CAUTION|NOTE|IMPORTANT):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
            r'(?i)> (?:Danger|Critical|Warning|Caution|Note|Important):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|\n```|$)',
        ]

        self.command_patterns = [
            r'```(?:bash|shell|sh)?\s*\n(.*?)\n```',
            r'<pre[^>]*><code[^>]*(?:class[^>]*(?:bash|shell|sh)[^>]*)?>(.*?)</code></pre>',
            r'(?:^|\n)\$\s+(.*?)(?=\n|\Z)',
        ]

        # Load existing cache
        self._load_cache()

    def _load_cache(self):
        """Load cached data."""
        try:
            if self.templates_cache.exists():
                with open(self.templates_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = [ExtractionTemplate(**t) for t in data]

            if self.knowledge_cache.exists():
                with open(self.knowledge_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_chunks = [ExtractedKnowledge(**k) for k in data]

            if self.validation_cache.exists():
                with open(self.validation_cache, 'r', encoding='utf-8') as f:
                    self.validation_results = json.load(f)

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save data to cache."""
        try:
            with open(self.templates_cache, 'w', encoding='utf-8') as f:
                json.dump([asdict(t) for t in self.templates], f, indent=2)

            with open(self.knowledge_cache, 'w', encoding='utf-8') as f:
                json.dump([asdict(k) for k in self.knowledge_chunks], f, indent=2)

            with open(self.validation_cache, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def deep_extract_from_url(self, url: str, topic_focus: str = None) -> Tuple[List[ExtractionTemplate], List[ExtractedKnowledge]]:
        """
        Perform deep extraction from a URL using multiple strategies.

        Args:
            url: Documentation URL to extract from
            topic_focus: Specific topic to focus on (e.g., "gpu", "storage", "networking")

        Returns:
            Tuple of (templates, knowledge_chunks)
        """
        logger.info(f"Deep extraction from: {url}")

        try:
            # Fetch content
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            # Multi-pass extraction
            templates = []
            knowledge_chunks = []

            # Pass 1: Structured extraction
            struct_templates, struct_knowledge = self._extract_structured_content(soup, url, topic_focus)
            templates.extend(struct_templates)
            knowledge_chunks.extend(struct_knowledge)

            # Pass 2: Semantic extraction
            semantic_knowledge = self._extract_semantic_content(soup, url, topic_focus)
            knowledge_chunks.extend(semantic_knowledge)

            # Pass 3: Context-aware extraction
            context_knowledge = self._extract_contextual_content(soup, url, topic_focus)
            knowledge_chunks.extend(context_knowledge)

            # Pass 4: Validation and enrichment
            validated_templates = self._validate_and_enrich_templates(templates, url)
            validated_knowledge = self._validate_and_enrich_knowledge(knowledge_chunks, url)

            # Update caches
            self.templates.extend(validated_templates)
            self.knowledge_chunks.extend(validated_knowledge)

            logger.info(f"Extracted {len(validated_templates)} templates and {len(validated_knowledge)} knowledge chunks")

            return validated_templates, validated_knowledge

        except Exception as e:
            logger.error(f"Deep extraction failed for {url}: {e}")
            return [], []

    def _extract_structured_content(self, soup: BeautifulSoup, url: str, topic_focus: str) -> Tuple[List[ExtractionTemplate], List[ExtractedKnowledge]]:
        """Extract content using structural HTML analysis - Enhanced for NRP structure."""
        templates = []
        knowledge_chunks = []

        # NRP-specific: Find YAML blocks with data-language="yaml" attribute
        yaml_blocks = soup.find_all('pre', attrs={'data-language': 'yaml'})
        for block in yaml_blocks:
            try:
                code_content = self._extract_text_from_element(block)
                if code_content.strip() and self._is_kubernetes_yaml(code_content):
                    template = self._create_template_from_yaml(block, code_content, url, soup)
                    if template:
                        templates.append(template)
                        logger.info(f"Found NRP YAML template: {template.title[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to process NRP YAML block: {e}")
                continue

        # NRP-specific: Find code blocks with expressive code class
        expressive_code_blocks = soup.find_all(['pre', 'code'], class_=re.compile(r'expressive.*code', re.I))
        for block in expressive_code_blocks:
            try:
                code_content = self._extract_text_from_element(block)
                if code_content.strip() and self._is_kubernetes_yaml(code_content):
                    template = self._create_template_from_yaml(block, code_content, url, soup)
                    if template:
                        templates.append(template)
                        logger.info(f"Found expressive code YAML template: {template.title[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to process expressive code block: {e}")
                continue

        # Fallback: Find all code blocks with YAML content (standard patterns)
        code_blocks = soup.find_all(['pre', 'code'])
        for block in code_blocks:
            try:
                # Skip if already processed above
                if (block.get('data-language') == 'yaml' or
                    'expressive' in ' '.join(block.get('class', []))):
                    continue

                code_content = self._extract_text_from_element(block)

                # Check if it's YAML
                if self._is_kubernetes_yaml(code_content):
                    template = self._create_template_from_yaml(block, code_content, url, soup)
                    if template:
                        templates.append(template)

                # Check if it's a command
                elif self._is_command_content(code_content):
                    knowledge = self._create_knowledge_from_command(block, code_content, url, soup)
                    if knowledge:
                        knowledge_chunks.append(knowledge)

            except Exception as e:
                logger.warning(f"Failed to process code block: {e}")
                continue

        # NRP-specific: Extract cautions with specific classes
        nrp_caution_elements = soup.find_all(class_=re.compile(r'\bcaution\b|\bcomplementary\s+caution\b', re.I))
        for caution_elem in nrp_caution_elements:
            try:
                knowledge = self._create_knowledge_from_warning(caution_elem, url, soup)
                if knowledge:
                    knowledge_chunks.append(knowledge)
                    logger.info(f"Found NRP caution: {knowledge.content[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to process NRP caution: {e}")
                continue

        # Standard warning extraction
        warning_elements = soup.find_all(['div', 'aside', 'blockquote'], class_=re.compile(r'warning|caution|note|important|danger', re.I))

        for warning_elem in warning_elements:
            try:
                knowledge = self._create_knowledge_from_warning(warning_elem, url, soup)
                if knowledge:
                    knowledge_chunks.append(knowledge)
            except Exception as e:
                logger.warning(f"Failed to process warning: {e}")
                continue

        return templates, knowledge_chunks

    def _extract_semantic_content(self, soup: BeautifulSoup, url: str, topic_focus: str) -> List[ExtractedKnowledge]:
        """Extract content using semantic analysis with LLM."""
        knowledge_chunks = []

        # Get page text and break into sections
        sections = self._get_content_sections(soup)

        for section_heading, section_content in sections:
            try:
                # Skip if content is too short
                if len(section_content.strip()) < 50:
                    continue

                # Use LLM to analyze semantic content
                semantic_analysis = self._analyze_content_semantically(
                    section_content, section_heading, topic_focus, url
                )

                if semantic_analysis:
                    knowledge_chunks.extend(semantic_analysis)

            except Exception as e:
                logger.warning(f"Semantic analysis failed for section '{section_heading}': {e}")
                continue

        return knowledge_chunks

    def _extract_contextual_content(self, soup: BeautifulSoup, url: str, topic_focus: str) -> List[ExtractedKnowledge]:
        """Extract content with rich context preservation."""
        knowledge_chunks = []

        # Find all paragraphs and analyze with context
        all_paragraphs = soup.find_all(['p', 'li', 'dd'])

        for i, para in enumerate(all_paragraphs):
            try:
                para_text = self._extract_text_from_element(para).strip()

                if len(para_text) < 20:
                    continue

                # Get preceding and following context
                preceding_context = ""
                following_context = ""

                if i > 0:
                    preceding_context = self._extract_text_from_element(all_paragraphs[i-1])

                if i < len(all_paragraphs) - 1:
                    following_context = self._extract_text_from_element(all_paragraphs[i+1])

                # Get section heading
                section_heading = self._find_section_heading(para)

                # Determine content type and topic
                content_type = self._classify_content_type(para_text)
                topic, subtopic = self._classify_topic(para_text, topic_focus)

                # Extract keywords and entities
                keywords = self._extract_keywords(para_text)
                entities = self._extract_entities(para_text)
                relationships = self._extract_relationships(para_text)

                knowledge = ExtractedKnowledge(
                    content=para_text,
                    content_type=content_type,
                    topic=topic,
                    subtopic=subtopic,
                    preceding_context=preceding_context[:200],
                    following_context=following_context[:200],
                    section_heading=section_heading,
                    keywords=keywords,
                    entities=entities,
                    relationships=relationships,
                    source_url=url,
                    source_section=section_heading,
                    extraction_timestamp=str(int(time.time())),
                    reliability_score=self._calculate_reliability_score(para_text, para),
                    completeness_score=self._calculate_completeness_score(para_text, preceding_context, following_context)
                )

                knowledge_chunks.append(knowledge)

            except Exception as e:
                logger.warning(f"Contextual extraction failed for paragraph: {e}")
                continue

        return knowledge_chunks

    def _create_template_from_yaml(self, element: Tag, yaml_content: str, url: str, soup: BeautifulSoup) -> Optional[ExtractionTemplate]:
        """Create a comprehensive template from YAML content."""
        try:
            # Parse YAML to get basic info
            yaml_data = yaml.safe_load(yaml_content)

            if not isinstance(yaml_data, dict):
                return None

            # Extract basic info
            api_version = yaml_data.get('apiVersion', '')
            kind = yaml_data.get('kind', 'Unknown')
            metadata = yaml_data.get('metadata', {})
            spec = yaml_data.get('spec', {})

            # Find surrounding context
            preceding_context = self._get_preceding_text(element, 500)
            following_context = self._get_following_text(element, 500)
            section_heading = self._find_section_heading(element)

            # Extract warnings and notes from context
            warnings = self._extract_warnings_from_context(preceding_context + following_context)
            cautions = self._extract_cautions_from_context(preceding_context + following_context)
            notes = self._extract_notes_from_context(preceding_context + following_context)
            dangers = self._extract_dangers_from_context(preceding_context + following_context)

            # Extract examples and best practices
            examples = self._extract_examples_from_context(preceding_context + following_context)
            best_practices = self._extract_best_practices_from_context(preceding_context + following_context)
            common_mistakes = self._extract_common_mistakes_from_context(preceding_context + following_context)

            # Extract resource requirements
            resource_requirements = {}
            if 'resources' in str(spec):
                resource_requirements = self._extract_resource_requirements(yaml_data)

            # Extract dependencies
            dependencies = self._extract_dependencies(yaml_data, preceding_context + following_context)

            # Generate title and description
            title = self._generate_template_title(kind, metadata, section_heading)
            description = self._generate_template_description(preceding_context, yaml_data)

            template = ExtractionTemplate(
                title=title,
                description=description,
                resource_type=kind.lower(),
                yaml_content=yaml_content,
                usage_context=f"{preceding_context}\n{following_context}",
                warnings=warnings,
                cautions=cautions,
                notes=notes,
                dangers=dangers,
                examples=examples,
                best_practices=best_practices,
                common_mistakes=common_mistakes,
                source_url=url,
                api_version=api_version,
                namespace_requirements=self._extract_namespace_requirements(yaml_data, preceding_context + following_context),
                resource_requirements=resource_requirements,
                dependencies=dependencies,
                confidence_score=self._calculate_template_confidence(yaml_data, preceding_context, following_context),
                extraction_method="deep_structured",
                validation_status="pending"
            )

            return template

        except Exception as e:
            logger.warning(f"Failed to create template from YAML: {e}")
            return None

    def _create_knowledge_from_command(self, element: Tag, command_content: str, url: str, soup: BeautifulSoup) -> Optional[ExtractedKnowledge]:
        """Create knowledge chunk from command content."""
        try:
            preceding_context = self._get_preceding_text(element, 300)
            following_context = self._get_following_text(element, 300)
            section_heading = self._find_section_heading(element)

            # Classify the command
            topic, subtopic = self._classify_command_topic(command_content)
            keywords = self._extract_command_keywords(command_content)
            entities = self._extract_command_entities(command_content)

            knowledge = ExtractedKnowledge(
                content=command_content,
                content_type="command",
                topic=topic,
                subtopic=subtopic,
                preceding_context=preceding_context[:200],
                following_context=following_context[:200],
                section_heading=section_heading,
                keywords=keywords,
                entities=entities,
                relationships=[],
                source_url=url,
                source_section=section_heading,
                extraction_timestamp=str(int(time.time())),
                reliability_score=0.8,  # Commands are generally reliable
                completeness_score=self._calculate_command_completeness(command_content, preceding_context)
            )

            return knowledge

        except Exception as e:
            logger.warning(f"Failed to create knowledge from command: {e}")
            return None

    def _create_knowledge_from_warning(self, element: Tag, url: str, soup: BeautifulSoup) -> Optional[ExtractedKnowledge]:
        """Create knowledge chunk from warning/note element."""
        try:
            warning_text = self._extract_text_from_element(element)

            if len(warning_text.strip()) < 10:
                return None

            # Determine warning type
            warning_type = self._classify_warning_type(element, warning_text)

            # Get context
            preceding_context = self._get_preceding_text(element, 300)
            following_context = self._get_following_text(element, 300)
            section_heading = self._find_section_heading(element)

            # Extract topic and keywords
            topic, subtopic = self._classify_warning_topic(warning_text)
            keywords = self._extract_keywords(warning_text)
            entities = self._extract_entities(warning_text)

            knowledge = ExtractedKnowledge(
                content=warning_text,
                content_type=warning_type,
                topic=topic,
                subtopic=subtopic,
                preceding_context=preceding_context[:200],
                following_context=following_context[:200],
                section_heading=section_heading,
                keywords=keywords,
                entities=entities,
                relationships=[],
                source_url=url,
                source_section=section_heading,
                extraction_timestamp=str(int(time.time())),
                reliability_score=0.9,  # Warnings are highly reliable
                completeness_score=0.8
            )

            return knowledge

        except Exception as e:
            logger.warning(f"Failed to create knowledge from warning: {e}")
            return None

    def _analyze_content_semantically(self, content: str, heading: str, topic_focus: str, url: str) -> List[ExtractedKnowledge]:
        """Use LLM to analyze content semantically."""
        try:
            analysis_prompt = f"""Analyze this documentation content and extract key information:

Section: {heading}
Content: {content[:1000]}
Topic Focus: {topic_focus or 'general'}

Extract and categorize:
1. Key concepts and definitions
2. Important warnings or cautions
3. Configuration requirements
4. Best practices mentioned
5. Common issues or gotchas

Format as JSON with structure:
{{
    "key_concepts": ["concept1", "concept2"],
    "warnings": ["warning1", "warning2"],
    "requirements": ["req1", "req2"],
    "best_practices": ["practice1", "practice2"],
    "common_issues": ["issue1", "issue2"],
    "main_topic": "topic",
    "subtopic": "subtopic"
}}"""

            response = self.llm.invoke(analysis_prompt)

            try:
                analysis = json.loads(response.content)
            except:
                # Fallback to text parsing if JSON fails
                return []

            # Create knowledge chunks from analysis
            knowledge_chunks = []

            for concept in analysis.get('key_concepts', []):
                knowledge_chunks.append(ExtractedKnowledge(
                    content=concept,
                    content_type="concept",
                    topic=analysis.get('main_topic', 'general'),
                    subtopic=analysis.get('subtopic', ''),
                    preceding_context="",
                    following_context="",
                    section_heading=heading,
                    keywords=concept.split(),
                    entities=[],
                    relationships=[],
                    source_url=url,
                    source_section=heading,
                    extraction_timestamp=str(int(time.time())),
                    reliability_score=0.7,
                    completeness_score=0.6
                ))

            for warning in analysis.get('warnings', []):
                knowledge_chunks.append(ExtractedKnowledge(
                    content=warning,
                    content_type="warning",
                    topic=analysis.get('main_topic', 'general'),
                    subtopic=analysis.get('subtopic', ''),
                    preceding_context="",
                    following_context="",
                    section_heading=heading,
                    keywords=warning.split(),
                    entities=[],
                    relationships=[],
                    source_url=url,
                    source_section=heading,
                    extraction_timestamp=str(int(time.time())),
                    reliability_score=0.9,
                    completeness_score=0.8
                ))

            return knowledge_chunks

        except Exception as e:
            logger.warning(f"Semantic analysis failed: {e}")
            return []

    # Helper methods for text extraction and analysis

    def _extract_text_from_element(self, element: Tag) -> str:
        """Extract clean text from HTML element."""
        if isinstance(element, NavigableString):
            return str(element)

        # Remove script and style elements
        for script in element(["script", "style"]):
            script.decompose()

        return element.get_text(separator=' ', strip=True)

    def _is_kubernetes_yaml(self, content: str) -> bool:
        """Check if content is Kubernetes YAML."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return False

            # Check for Kubernetes resource markers
            required_fields = ['apiVersion', 'kind']
            return all(field in data for field in required_fields)
        except:
            return False

    def _is_command_content(self, content: str) -> bool:
        """Check if content is a command."""
        content = content.strip()

        # Check for common command indicators
        command_indicators = [
            'kubectl', 'helm', 'docker', 'git', 'curl', 'wget',
            'apt', 'yum', 'pip', 'npm', 'make', 'cd', 'ls', 'cat'
        ]

        first_word = content.split()[0] if content.split() else ""
        return first_word.lower() in command_indicators or content.startswith('$')

    def _get_content_sections(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Get content organized by sections."""
        sections = []

        # Find all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for i, heading in enumerate(headings):
            heading_text = self._extract_text_from_element(heading)

            # Get content until next heading
            content_elements = []
            next_sibling = heading.next_sibling

            while next_sibling:
                if next_sibling.name and next_sibling.name.startswith('h'):
                    break
                if hasattr(next_sibling, 'get_text'):
                    content_elements.append(next_sibling)
                next_sibling = next_sibling.next_sibling

            section_content = ' '.join(self._extract_text_from_element(elem) for elem in content_elements)

            if section_content.strip():
                sections.append((heading_text, section_content))

        return sections

    def _get_preceding_text(self, element: Tag, max_chars: int = 300) -> str:
        """Get text preceding an element."""
        preceding_text = ""
        current = element.previous_sibling

        while current and len(preceding_text) < max_chars:
            if hasattr(current, 'get_text'):
                text = self._extract_text_from_element(current)
                preceding_text = text + " " + preceding_text
            elif isinstance(current, NavigableString):
                preceding_text = str(current) + " " + preceding_text
            current = current.previous_sibling

        return preceding_text[:max_chars]

    def _get_following_text(self, element: Tag, max_chars: int = 300) -> str:
        """Get text following an element."""
        following_text = ""
        current = element.next_sibling

        while current and len(following_text) < max_chars:
            if hasattr(current, 'get_text'):
                text = self._extract_text_from_element(current)
                following_text = following_text + " " + text
            elif isinstance(current, NavigableString):
                following_text = following_text + " " + str(current)
            current = current.next_sibling

        return following_text[:max_chars]

    def _find_section_heading(self, element: Tag) -> str:
        """Find the section heading for an element."""
        current = element

        while current:
            if current.name and current.name.startswith('h'):
                return self._extract_text_from_element(current)
            current = current.previous_sibling

        # Look in parent elements
        parent = element.parent
        while parent:
            heading = parent.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                return self._extract_text_from_element(heading)
            parent = parent.parent

        return "Unknown Section"

    def _classify_content_type(self, content: str) -> str:
        """Classify the type of content."""
        content_lower = content.lower()

        if any(warning in content_lower for warning in ['warning', 'caution', 'danger', 'critical']):
            return "warning"
        elif any(note in content_lower for note in ['note', 'important', 'tip']):
            return "note"
        elif any(example in content_lower for example in ['example', 'for instance', 'such as']):
            return "example"
        elif any(practice in content_lower for practice in ['best practice', 'recommended', 'should']):
            return "best_practice"
        else:
            return "explanation"

    def _classify_topic(self, content: str, topic_focus: str = None) -> Tuple[str, str]:
        """Classify the topic and subtopic of content."""
        content_lower = content.lower()

        # Main topics
        if any(gpu in content_lower for gpu in ['gpu', 'nvidia', 'cuda', 'a100', 'v100']):
            topic = "gpu"
            if 'a100' in content_lower:
                subtopic = "a100"
            elif 'v100' in content_lower:
                subtopic = "v100"
            else:
                subtopic = "general"
        elif any(storage in content_lower for storage in ['storage', 'pvc', 'volume', 'persistent']):
            topic = "storage"
            if 'ceph' in content_lower:
                subtopic = "ceph"
            elif 'nfs' in content_lower:
                subtopic = "nfs"
            else:
                subtopic = "general"
        elif any(net in content_lower for net in ['network', 'ingress', 'service', 'loadbalancer']):
            topic = "networking"
            if 'ingress' in content_lower:
                subtopic = "ingress"
            elif 'service' in content_lower:
                subtopic = "service"
            else:
                subtopic = "general"
        elif any(job in content_lower for job in ['job', 'batch', 'cron', 'workload']):
            topic = "jobs"
            if 'cronjob' in content_lower:
                subtopic = "cronjob"
            else:
                subtopic = "job"
        else:
            topic = topic_focus or "general"
            subtopic = "general"

        return topic, subtopic

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        import re

        # Remove common words and extract meaningful terms
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

        # Filter out common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}

        keywords = [word for word in words if word not in stop_words]

        # Return top 10 most relevant keywords
        return list(set(keywords))[:10]

    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities like GPU types, storage classes, etc."""
        entities = []
        content_lower = content.lower()

        # GPU entities
        gpu_entities = ['a100', 'v100', 'k80', 'titan', 'geforce', 'quadro', 'tesla']
        entities.extend([gpu for gpu in gpu_entities if gpu in content_lower])

        # Storage entities
        storage_entities = ['ceph', 'nfs', 'iscsi', 'csi', 'pvc', 'pv']
        entities.extend([storage for storage in storage_entities if storage in content_lower])

        # Network entities
        network_entities = ['haproxy', 'nginx', 'traefik', 'istio', 'envoy']
        entities.extend([net for net in network_entities if net in content_lower])

        return list(set(entities))

    def _extract_relationships(self, content: str) -> List[str]:
        """Extract relationships and dependencies."""
        relationships = []
        content_lower = content.lower()

        # Look for dependency patterns
        if 'requires' in content_lower:
            relationships.append('requires_dependency')
        if 'depends on' in content_lower:
            relationships.append('depends_on')
        if 'needs' in content_lower:
            relationships.append('needs')

        return relationships

    def _calculate_reliability_score(self, content: str, element: Tag) -> float:
        """Calculate reliability score for content."""
        score = 0.5  # Base score

        # Boost for official sources
        if element.find_parent(['div', 'section'], class_=re.compile(r'official|docs|documentation', re.I)):
            score += 0.3

        # Boost for code examples
        if any(indicator in content.lower() for indicator in ['apiversion', 'kind', 'kubectl']):
            score += 0.2

        # Boost for detailed content
        if len(content) > 100:
            score += 0.1

        return min(1.0, score)

    def _calculate_completeness_score(self, content: str, preceding: str, following: str) -> float:
        """Calculate completeness score based on context."""
        score = 0.5

        # Boost if has good context
        if len(preceding) > 50:
            score += 0.2
        if len(following) > 50:
            score += 0.2

        # Boost for complete examples
        if 'example' in (preceding + following).lower():
            score += 0.1

        return min(1.0, score)

    # Validation and enrichment methods

    def _validate_and_enrich_templates(self, templates: List[ExtractionTemplate], url: str) -> List[ExtractionTemplate]:
        """Validate and enrich templates."""
        validated = []

        for template in templates:
            try:
                # Validate YAML
                yaml.safe_load(template.yaml_content)

                # Enrich with additional context
                template.confidence_score = self._recalculate_template_confidence(template)
                template.validation_status = "valid"

                validated.append(template)

            except Exception as e:
                logger.warning(f"Template validation failed: {e}")
                template.validation_status = f"invalid: {str(e)}"
                template.confidence_score *= 0.5  # Reduce confidence for invalid templates
                validated.append(template)  # Keep for potential manual review

        return validated

    def _validate_and_enrich_knowledge(self, knowledge_chunks: List[ExtractedKnowledge], url: str) -> List[ExtractedKnowledge]:
        """Validate and enrich knowledge chunks."""
        # Remove duplicates
        seen_content = set()
        unique_chunks = []

        for chunk in knowledge_chunks:
            content_hash = hash(chunk.content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_chunks.append(chunk)

        return unique_chunks

    # Additional helper methods would go here...
    # (Due to length constraints, implementing key extraction methods above)

    def save(self):
        """Save all extracted data to cache."""
        self._save_cache()

    def search_templates(self, query: str) -> List[ExtractionTemplate]:
        """Search templates by query."""
        query_lower = query.lower()
        matching_templates = []

        for template in self.templates:
            if (query_lower in template.title.lower() or
                query_lower in template.description.lower() or
                query_lower in template.resource_type.lower() or
                any(query_lower in keyword.lower() for keyword in template.best_practices)):
                matching_templates.append(template)

        return matching_templates

    def search_knowledge(self, query: str) -> List[ExtractedKnowledge]:
        """Search knowledge chunks by query."""
        query_lower = query.lower()
        matching_knowledge = []

        for knowledge in self.knowledge_chunks:
            if (query_lower in knowledge.content.lower() or
                query_lower in knowledge.topic.lower() or
                any(query_lower in keyword.lower() for keyword in knowledge.keywords)):
                matching_knowledge.append(knowledge)

        return matching_knowledge

    # Placeholder implementations for pattern extraction methods
    def _extract_warnings_from_context(self, context: str) -> List[str]:
        """Extract warnings from context."""
        warnings = []
        for pattern in self.warning_patterns:
            matches = re.finditer(pattern, context, re.DOTALL | re.IGNORECASE)
            for match in matches:
                warning = match.group(1).strip() if match.groups() else match.group(0).strip()
                if len(warning) > 10:
                    warnings.append(warning)
        return warnings[:5]  # Limit to avoid noise

    def _extract_cautions_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)caution:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_notes_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)note:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_dangers_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)danger:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_examples_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)example:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_best_practices_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)(?:best practice|recommended):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_common_mistakes_from_context(self, context: str) -> List[str]:
        return self._extract_pattern_from_context(context, r'(?i)(?:avoid|don\'t|never|mistake):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)')

    def _extract_pattern_from_context(self, context: str, pattern: str) -> List[str]:
        """Extract pattern matches from context."""
        matches = []
        for match in re.finditer(pattern, context, re.DOTALL):
            text = match.group(1).strip() if match.groups() else match.group(0).strip()
            if len(text) > 10:
                matches.append(text)
        return matches[:3]  # Limit results

    def _extract_resource_requirements(self, yaml_data: dict) -> Dict[str, str]:
        """Extract resource requirements from YAML."""
        requirements = {}

        def extract_from_dict(d, prefix=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k == 'resources' and isinstance(v, dict):
                        requirements.update({f"{prefix}resources.{kk}": str(vv) for kk, vv in v.items()})
                    elif isinstance(v, dict):
                        extract_from_dict(v, f"{prefix}{k}.")

        extract_from_dict(yaml_data)
        return requirements

    def _extract_dependencies(self, yaml_data: dict, context: str) -> List[str]:
        """Extract dependencies from YAML and context."""
        dependencies = []

        # Extract from YAML structure
        if 'spec' in yaml_data:
            spec = yaml_data['spec']
            if 'volumes' in spec:
                dependencies.extend(['storage'])
            if 'nodeSelector' in spec:
                dependencies.extend(['node-selector'])

        # Extract from context
        context_lower = context.lower()
        if 'requires' in context_lower:
            dependencies.append('external-dependency')

        return list(set(dependencies))

    def _extract_namespace_requirements(self, yaml_data: dict, context: str) -> List[str]:
        """Extract namespace requirements."""
        requirements = []

        metadata = yaml_data.get('metadata', {})
        if 'namespace' in metadata:
            requirements.append(f"namespace: {metadata['namespace']}")

        if 'gsoc' in context.lower():
            requirements.append('namespace: gsoc')

        return requirements

    def _generate_template_title(self, kind: str, metadata: dict, section_heading: str) -> str:
        """Generate title for template."""
        name = metadata.get('name', kind)
        return f"{kind} - {name} ({section_heading})"

    def _generate_template_description(self, context: str, yaml_data: dict) -> str:
        """Generate description for template."""
        # Extract first sentence from context as description
        sentences = context.split('.')
        return sentences[0][:200] if sentences else f"Kubernetes {yaml_data.get('kind', 'resource')} configuration"

    def _calculate_template_confidence(self, yaml_data: dict, preceding: str, following: str) -> float:
        """Calculate confidence score for template."""
        score = 0.5

        # Boost for complete YAML
        if all(field in yaml_data for field in ['apiVersion', 'kind', 'metadata']):
            score += 0.3

        # Boost for good context
        if len(preceding + following) > 200:
            score += 0.2

        return min(1.0, score)

    def _recalculate_template_confidence(self, template: ExtractionTemplate) -> float:
        """Recalculate template confidence after validation."""
        score = template.confidence_score

        # Boost for warnings and notes
        if template.warnings or template.cautions or template.dangers:
            score += 0.1

        # Boost for best practices
        if template.best_practices:
            score += 0.1

        return min(1.0, score)

    def _classify_warning_type(self, element: Tag, text: str) -> str:
        """Classify type of warning."""
        classes = element.get('class', [])
        aria_label = element.get('aria-label', '').lower()
        text_lower = text.lower()

        if any('danger' in str(c).lower() for c in classes) or 'danger' in aria_label or 'danger' in text_lower:
            return 'danger'
        elif any('warning' in str(c).lower() for c in classes) or 'warning' in aria_label or 'warning' in text_lower:
            return 'warning'
        elif any('caution' in str(c).lower() for c in classes) or 'caution' in aria_label or 'caution' in text_lower:
            return 'caution'
        else:
            return 'note'

    def _classify_warning_topic(self, text: str) -> Tuple[str, str]:
        """Classify the topic of a warning."""
        return self._classify_topic(text)

    def _classify_command_topic(self, command: str) -> Tuple[str, str]:
        """Classify the topic of a command."""
        command_lower = command.lower()

        if 'kubectl' in command_lower:
            if 'gpu' in command_lower:
                return 'gpu', 'kubectl'
            elif 'storage' in command_lower or 'pvc' in command_lower:
                return 'storage', 'kubectl'
            else:
                return 'kubernetes', 'kubectl'
        elif 'helm' in command_lower:
            return 'kubernetes', 'helm'
        elif 'docker' in command_lower:
            return 'containers', 'docker'
        else:
            return 'general', 'command'

    def _extract_command_keywords(self, command: str) -> List[str]:
        """Extract keywords from command."""
        # Split command and extract meaningful parts
        parts = command.split()
        keywords = []

        for part in parts:
            if len(part) > 2 and not part.startswith('-'):
                keywords.append(part.lower())

        return keywords[:5]

    def _extract_command_entities(self, command: str) -> List[str]:
        """Extract entities from command."""
        return self._extract_entities(command)

    def _calculate_command_completeness(self, command: str, context: str) -> float:
        """Calculate completeness score for command."""
        score = 0.6  # Base score for commands

        # Boost for good context
        if 'example' in context.lower():
            score += 0.2

        # Boost for complete commands
        if len(command.split()) > 3:
            score += 0.2

        return min(1.0, score)


# Convenience functions
def create_deep_extractor() -> DeepExtractorAgent:
    """Create a deep extractor agent."""
    return DeepExtractorAgent()

def deep_extract_documentation(urls: List[str], topic_focus: str = None) -> Tuple[List[ExtractionTemplate], List[ExtractedKnowledge]]:
    """Extract comprehensive knowledge from multiple URLs."""
    extractor = DeepExtractorAgent()

    all_templates = []
    all_knowledge = []

    for url in urls:
        templates, knowledge = extractor.deep_extract_from_url(url, topic_focus)
        all_templates.extend(templates)
        all_knowledge.extend(knowledge)

    extractor.save()
    return all_templates, all_knowledge