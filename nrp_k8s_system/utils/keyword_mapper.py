#!/usr/bin/env python3
"""
Comprehensive Keyword Mapping System
====================================

Builds comprehensive keyword mapping from all NRP documentation pages
to improve navigation and search accuracy. Extracts keywords, topics,
and creates relationships between content areas.

This addresses the need for systematic keyword extraction mentioned
in the edge case handling discussion - building a comprehensive
mapping to avoid navigation failures and improve search relevance.
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class KeywordData:
    """Represents keyword data extracted from documentation."""
    keyword: str
    frequency: int
    pages: List[str]
    contexts: List[str]
    category: str
    importance_score: float

@dataclass
class TopicMapping:
    """Represents topic relationships and hierarchies."""
    topic: str
    related_topics: List[str]
    keywords: List[str]
    pages: List[str]
    parent_topic: Optional[str]
    child_topics: List[str]

@dataclass
class PageProfile:
    """Represents comprehensive profile of a documentation page."""
    url: str
    title: str
    keywords: List[str]
    topics: List[str]
    content_type: str
    importance_score: float
    related_pages: List[str]
    extract_quality: float

class KeywordMapper:
    """Comprehensive keyword mapping system for NRP documentation."""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or "cache/keyword_mapping")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Storage for mappings
        self.keyword_data: Dict[str, KeywordData] = {}
        self.topic_mappings: Dict[str, TopicMapping] = {}
        self.page_profiles: Dict[str, PageProfile] = {}

        # NRP-specific keyword categories
        self.keyword_categories = {
            'hardware': ['gpu', 'fpga', 'alveo', 'smartnic', 'cpu', 'memory', 'storage', 'node', 'cluster'],
            'software': ['kubernetes', 'docker', 'container', 'pod', 'deployment', 'service', 'yaml', 'helm'],
            'networking': ['ingress', 'egress', 'loadbalancer', 'service', 'network', 'dns', 'ip', 'port'],
            'storage': ['persistent', 'volume', 'pvc', 'storage', 'filesystem', 'mount', 'backup'],
            'compute': ['job', 'batch', 'workload', 'task', 'queue', 'schedule', 'resource', 'allocation'],
            'admin': ['admin', 'administrator', 'cluster', 'node', 'config', 'setup', 'install', 'manage'],
            'user': ['user', 'guide', 'tutorial', 'example', 'workflow', 'documentation', 'help'],
            'policy': ['policy', 'rule', 'guideline', 'limit', 'quota', 'permission', 'access', 'security'],
            'platform': ['nrp', 'nautilus', 'prp', 'sdsc', 'ucsd', 'esnet', 'platform', 'infrastructure']
        }

        # Load existing mappings
        self._load_existing_mappings()

    def _load_existing_mappings(self):
        """Load existing keyword mappings from cache."""
        try:
            keyword_file = self.cache_dir / "keyword_data.json"
            if keyword_file.exists():
                with open(keyword_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.keyword_data = {
                        k: KeywordData(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.keyword_data)} keywords from cache")

            topic_file = self.cache_dir / "topic_mappings.json"
            if topic_file.exists():
                with open(topic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.topic_mappings = {
                        k: TopicMapping(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.topic_mappings)} topic mappings from cache")

            page_file = self.cache_dir / "page_profiles.json"
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.page_profiles = {
                        k: PageProfile(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.page_profiles)} page profiles from cache")

        except Exception as e:
            logger.warning(f"Failed to load existing mappings: {e}")

    def extract_keywords_from_content(self, content: str, url: str, title: str = "") -> List[str]:
        """Extract relevant keywords from content."""
        if not content:
            return []

        # Clean and normalize content
        content = self._clean_content(content)

        # Extract different types of keywords
        keywords = set()

        # 1. Extract NRP-specific terms
        keywords.update(self._extract_nrp_terms(content))

        # 2. Extract technical terms
        keywords.update(self._extract_technical_terms(content))

        # 3. Extract command and configuration terms
        keywords.update(self._extract_command_terms(content))

        # 4. Extract from title and headers
        keywords.update(self._extract_title_keywords(title, content))

        # 5. Filter and score keywords
        scored_keywords = self._score_keywords(keywords, content, url)

        return [kw for kw, score in scored_keywords if score > 0.3]

    def _clean_content(self, content: str) -> str:
        """Clean content for keyword extraction."""
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)

        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)

        # Convert to lowercase for processing
        return content.lower().strip()

    def _extract_nrp_terms(self, content: str) -> Set[str]:
        """Extract NRP-specific terms."""
        nrp_terms = set()

        # Platform-specific terms
        platform_patterns = [
            r'\b(nrp|nautilus|prp)\b',
            r'\b(sdsc|ucsd|esnet)\b',
            r'\b(pacific research platform)\b',
            r'\b(national research platform)\b'
        ]

        for pattern in platform_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            nrp_terms.update(match.lower() if isinstance(match, str) else match[0].lower() for match in matches)

        return nrp_terms

    def _extract_technical_terms(self, content: str) -> Set[str]:
        """Extract technical terms and abbreviations."""
        technical_terms = set()

        # Technical patterns
        patterns = [
            # Kubernetes terms
            r'\b(kubernetes|k8s|kubectl|pod|deployment|service|ingress|configmap|secret)\b',
            # Hardware terms
            r'\b(gpu|fpga|alveo|u55c|smartnic|cpu|memory|storage|pci|lspci)\b',
            # Software terms
            r'\b(docker|container|yaml|helm|vivado|xrt|xilinx)\b',
            # Network terms
            r'\b(loadbalancer|dns|ip|port|network|subnet|vlan)\b',
            # Storage terms
            r'\b(persistent|volume|pvc|filesystem|mount|backup|snapshot)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            technical_terms.update(match.lower() for match in matches)

        return technical_terms

    def _extract_command_terms(self, content: str) -> Set[str]:
        """Extract command-line and configuration terms."""
        command_terms = set()

        # Look for command patterns
        command_patterns = [
            r'kubectl\s+(\w+)',
            r'docker\s+(\w+)',
            r'helm\s+(\w+)',
            r'(\w+)\s*:\s*["\']?[\w\-\.]+["\']?',  # YAML-like patterns
        ]

        for pattern in command_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            command_terms.update(match.lower() for match in matches if isinstance(match, str))

        return command_terms

    def _extract_title_keywords(self, title: str, content: str) -> Set[str]:
        """Extract keywords from title and headers."""
        title_keywords = set()

        if title:
            # Extract significant words from title
            title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            title_keywords.update(title_words)

        # Extract from headers in content
        header_patterns = [
            r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            r'#{1,6}\s*([^\n]+)',  # Markdown headers
        ]

        for pattern in header_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                header_words = re.findall(r'\b[a-zA-Z]{3,}\b', match.lower())
                title_keywords.update(header_words)

        return title_keywords

    def _score_keywords(self, keywords: Set[str], content: str, url: str) -> List[Tuple[str, float]]:
        """Score keywords based on relevance and importance."""
        scored = []
        content_lower = content.lower()

        for keyword in keywords:
            score = 0.0

            # Base frequency score
            frequency = content_lower.count(keyword.lower())
            score += min(frequency * 0.1, 1.0)

            # Category bonus
            for category, terms in self.keyword_categories.items():
                if keyword.lower() in [term.lower() for term in terms]:
                    score += 0.5
                    break

            # URL relevance bonus
            if keyword.lower() in url.lower():
                score += 0.3

            # Length penalty for very short terms
            if len(keyword) < 3:
                score *= 0.5

            # Length bonus for longer technical terms
            elif len(keyword) > 6:
                score += 0.2

            scored.append((keyword, score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def build_topic_relationships(self, pages_data: List[Dict[str, Any]]):
        """Build topic relationships from page data."""
        print("Building topic relationships from page data...")

        # Extract topics from all pages
        all_topics = defaultdict(set)
        topic_pages = defaultdict(set)
        topic_keywords = defaultdict(set)

        for page_data in pages_data:
            url = page_data.get('url', '')
            title = page_data.get('title', '')
            content = page_data.get('content', '')
            keywords = page_data.get('keywords', [])

            # Extract topics from URL structure
            topics = self._extract_topics_from_url(url)

            # Add topics from title
            topics.update(self._extract_topics_from_title(title))

            # Store relationships
            for topic in topics:
                topic_pages[topic].add(url)
                topic_keywords[topic].update(keywords)
                all_topics[topic].update(topics - {topic})  # Related topics

        # Create topic mappings
        for topic, related in all_topics.items():
            self.topic_mappings[topic] = TopicMapping(
                topic=topic,
                related_topics=list(related)[:10],  # Top 10 related
                keywords=list(topic_keywords[topic])[:20],  # Top 20 keywords
                pages=list(topic_pages[topic]),
                parent_topic=self._determine_parent_topic(topic),
                child_topics=self._determine_child_topics(topic, all_topics)
            )

        print(f"Built {len(self.topic_mappings)} topic mappings")

    def _extract_topics_from_url(self, url: str) -> Set[str]:
        """Extract topics from URL structure."""
        topics = set()

        # Remove base URL and extract path components
        path = url.replace('https://nrp.ai/', '').strip('/')
        components = path.split('/')

        for component in components:
            if component and len(component) > 2:
                # Clean component
                topic = re.sub(r'[^a-zA-Z0-9]', ' ', component).strip()
                if topic:
                    topics.add(topic.lower())

        return topics

    def _extract_topics_from_title(self, title: str) -> Set[str]:
        """Extract topics from page title."""
        if not title:
            return set()

        # Extract significant words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())

        # Filter out common words
        stop_words = {'the', 'and', 'for', 'with', 'how', 'what', 'when', 'where', 'why'}
        topics = {word for word in words if word not in stop_words}

        return topics

    def _determine_parent_topic(self, topic: str) -> Optional[str]:
        """Determine parent topic based on hierarchy."""
        # Define topic hierarchy
        hierarchy = {
            'gpu': 'hardware',
            'fpga': 'hardware',
            'alveo': 'fpga',
            'smartnic': 'networking',
            'kubernetes': 'software',
            'docker': 'software',
            'storage': 'infrastructure',
            'networking': 'infrastructure',
            'admin': 'administration',
            'user': 'documentation'
        }

        return hierarchy.get(topic.lower())

    def _determine_child_topics(self, topic: str, all_topics: Dict[str, Set[str]]) -> List[str]:
        """Determine child topics."""
        children = []

        for other_topic, related in all_topics.items():
            if topic in related and other_topic != topic:
                # Check if it's a more specific topic
                if topic in other_topic or other_topic.startswith(topic):
                    children.append(other_topic)

        return children[:5]  # Top 5 children

    def create_page_profiles(self, pages_data: List[Dict[str, Any]]):
        """Create comprehensive profiles for each page."""
        print("Creating comprehensive page profiles...")

        for page_data in pages_data:
            url = page_data.get('url', '')
            title = page_data.get('title', '')
            content = page_data.get('content', '')

            if not url:
                continue

            # Extract keywords
            keywords = self.extract_keywords_from_content(content, url, title)

            # Determine topics
            topics = list(self._extract_topics_from_url(url).union(
                self._extract_topics_from_title(title)
            ))

            # Determine content type
            content_type = self._classify_content_type(url, title, content)

            # Calculate importance score
            importance_score = self._calculate_page_importance(url, title, content, keywords)

            # Find related pages (simplified)
            related_pages = self._find_related_pages(keywords, topics, url)

            # Assess extract quality
            extract_quality = self._assess_extract_quality(content, keywords)

            # Create profile
            self.page_profiles[url] = PageProfile(
                url=url,
                title=title,
                keywords=keywords,
                topics=topics,
                content_type=content_type,
                importance_score=importance_score,
                related_pages=related_pages,
                extract_quality=extract_quality
            )

        print(f"Created {len(self.page_profiles)} page profiles")

    def _classify_content_type(self, url: str, title: str, content: str) -> str:
        """Classify the type of content."""
        url_lower = url.lower()
        title_lower = title.lower()

        if 'admindocs' in url_lower:
            return 'admin_documentation'
        elif 'userguide' in url_lower:
            return 'user_guide'
        elif 'tutorial' in title_lower or 'example' in title_lower:
            return 'tutorial'
        elif 'policy' in title_lower or 'guideline' in title_lower:
            return 'policy'
        elif 'api' in url_lower or 'reference' in title_lower:
            return 'reference'
        else:
            return 'general_documentation'

    def _calculate_page_importance(self, url: str, title: str, content: str, keywords: List[str]) -> float:
        """Calculate page importance score."""
        score = 0.0

        # URL depth penalty (deeper = less important)
        depth = url.count('/') - 3  # Adjust for base URL
        score += max(0, 1.0 - depth * 0.1)

        # Admin documentation bonus
        if 'admindocs' in url.lower():
            score += 0.3

        # FPGA/GPU content bonus
        if any(term in content.lower() for term in ['fpga', 'gpu', 'alveo', 'smartnic']):
            score += 0.2

        # Keyword richness
        score += min(len(keywords) * 0.05, 0.5)

        # Content length bonus
        if len(content) > 1000:
            score += 0.2

        return min(score, 1.0)

    def _find_related_pages(self, keywords: List[str], topics: List[str], current_url: str) -> List[str]:
        """Find related pages based on keywords and topics."""
        related = []

        # Simple implementation - would be enhanced with similarity scoring
        for url, profile in self.page_profiles.items():
            if url == current_url:
                continue

            # Check keyword overlap
            keyword_overlap = len(set(keywords) & set(profile.keywords))
            topic_overlap = len(set(topics) & set(profile.topics))

            if keyword_overlap >= 2 or topic_overlap >= 1:
                related.append(url)

        return related[:5]  # Top 5 related

    def _assess_extract_quality(self, content: str, keywords: List[str]) -> float:
        """Assess the quality of content extraction."""
        if not content:
            return 0.0

        score = 0.0

        # Content length indicator
        if len(content) > 500:
            score += 0.3
        elif len(content) > 100:
            score += 0.2

        # Keyword density
        if keywords and content:
            density = len(keywords) / (len(content.split()) + 1)
            score += min(density * 10, 0.3)

        # Structure indicators
        if '<' in content or '```' in content:  # HTML or code blocks
            score += 0.2

        # NRP-specific content
        if any(term in content.lower() for term in ['nrp', 'nautilus', 'kubernetes']):
            score += 0.2

        return min(score, 1.0)

    def save_mappings(self):
        """Save all mappings to cache files."""
        try:
            # Save keyword data
            keyword_file = self.cache_dir / "keyword_data.json"
            with open(keyword_file, 'w', encoding='utf-8') as f:
                data = {k: asdict(v) for k, v in self.keyword_data.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save topic mappings
            topic_file = self.cache_dir / "topic_mappings.json"
            with open(topic_file, 'w', encoding='utf-8') as f:
                data = {k: asdict(v) for k, v in self.topic_mappings.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save page profiles
            page_file = self.cache_dir / "page_profiles.json"
            with open(page_file, 'w', encoding='utf-8') as f:
                data = {k: asdict(v) for k, v in self.page_profiles.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Save summary statistics
            summary_file = self.cache_dir / "mapping_summary.json"
            summary = {
                'total_keywords': len(self.keyword_data),
                'total_topics': len(self.topic_mappings),
                'total_pages': len(self.page_profiles),
                'last_updated': time.time(),
                'categories': {cat: len(terms) for cat, terms in self.keyword_categories.items()}
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Saved mappings: {len(self.keyword_data)} keywords, {len(self.topic_mappings)} topics, {len(self.page_profiles)} pages")

        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")

    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get summary of current mappings."""
        return {
            'keywords': {
                'total': len(self.keyword_data),
                'by_category': self._count_keywords_by_category(),
                'top_keywords': self._get_top_keywords(10)
            },
            'topics': {
                'total': len(self.topic_mappings),
                'hierarchical': self._count_hierarchical_topics(),
                'top_topics': list(self.topic_mappings.keys())[:10]
            },
            'pages': {
                'total': len(self.page_profiles),
                'by_type': self._count_pages_by_type(),
                'high_importance': self._get_high_importance_pages(5)
            }
        }

    def _count_keywords_by_category(self) -> Dict[str, int]:
        """Count keywords by category."""
        counts = {}
        for category, terms in self.keyword_categories.items():
            count = sum(1 for kw in self.keyword_data.keys()
                       if kw.lower() in [t.lower() for t in terms])
            counts[category] = count
        return counts

    def _get_top_keywords(self, limit: int) -> List[str]:
        """Get top keywords by frequency."""
        sorted_keywords = sorted(
            self.keyword_data.items(),
            key=lambda x: x[1].frequency,
            reverse=True
        )
        return [kw for kw, _ in sorted_keywords[:limit]]

    def _count_hierarchical_topics(self) -> Dict[str, int]:
        """Count topics by hierarchy level."""
        counts = {'parent': 0, 'child': 0, 'standalone': 0}

        for topic_data in self.topic_mappings.values():
            if topic_data.parent_topic:
                counts['child'] += 1
            elif topic_data.child_topics:
                counts['parent'] += 1
            else:
                counts['standalone'] += 1

        return counts

    def _count_pages_by_type(self) -> Dict[str, int]:
        """Count pages by content type."""
        counts = defaultdict(int)
        for profile in self.page_profiles.values():
            counts[profile.content_type] += 1
        return dict(counts)

    def _get_high_importance_pages(self, limit: int) -> List[str]:
        """Get highest importance pages."""
        sorted_pages = sorted(
            self.page_profiles.items(),
            key=lambda x: x[1].importance_score,
            reverse=True
        )
        return [url for url, _ in sorted_pages[:limit]]


def build_comprehensive_keyword_mapping(cache_dir: str = None) -> KeywordMapper:
    """Build comprehensive keyword mapping from available data."""
    print("Building Comprehensive Keyword Mapping System")
    print("=" * 50)

    mapper = KeywordMapper(cache_dir)

    # For demonstration, create sample data
    # In real implementation, this would process scraped content
    sample_pages = [
        {
            'url': 'https://nrp.ai/documentation/admindocs/cluster/fpga/',
            'title': 'FPGA Configuration and Management',
            'content': '''FPGA flashing and management procedures for Alveo U55C cards.
                         Administrative access required. Use Vivado tools for configuration.
                         ESnet SmartNIC workflow integration. XRT setup and validation.''',
            'keywords': ['fpga', 'alveo', 'smartnic', 'admin', 'vivado', 'xrt']
        },
        {
            'url': 'https://nrp.ai/documentation/userguide/gpu/',
            'title': 'GPU Computing Guide',
            'content': '''GPU resource allocation and management. Kubernetes GPU scheduling.
                         NVIDIA GPU support. Container GPU access. Resource limits and quotas.''',
            'keywords': ['gpu', 'nvidia', 'kubernetes', 'container', 'resource']
        },
        {
            'url': 'https://nrp.ai/documentation/userguide/storage/',
            'title': 'Storage Configuration',
            'content': '''Persistent volume configuration. Storage classes and provisioning.
                         File system access. Backup and snapshot procedures.''',
            'keywords': ['storage', 'persistent', 'volume', 'filesystem', 'backup']
        }
    ]

    # Build keyword mappings
    for page in sample_pages:
        keywords = mapper.extract_keywords_from_content(
            page['content'], page['url'], page['title']
        )

        # Update keyword data
        for keyword in keywords:
            if keyword in mapper.keyword_data:
                mapper.keyword_data[keyword].frequency += 1
                mapper.keyword_data[keyword].pages.append(page['url'])
            else:
                # Determine category
                category = 'general'
                for cat, terms in mapper.keyword_categories.items():
                    if keyword.lower() in [t.lower() for t in terms]:
                        category = cat
                        break

                mapper.keyword_data[keyword] = KeywordData(
                    keyword=keyword,
                    frequency=1,
                    pages=[page['url']],
                    contexts=[page['content'][:100]],
                    category=category,
                    importance_score=0.5
                )

    # Build topic relationships
    mapper.build_topic_relationships(sample_pages)

    # Create page profiles
    mapper.create_page_profiles(sample_pages)

    # Save mappings
    mapper.save_mappings()

    print(f"Keyword mapping completed!")
    print(f"Summary: {mapper.get_mapping_summary()}")

    return mapper


if __name__ == "__main__":
    # Build comprehensive keyword mapping
    mapper = build_comprehensive_keyword_mapping()

    print("\nKeyword Mapping System Ready!")
    print("This system provides:")
    print("- Comprehensive keyword extraction and categorization")
    print("- Topic relationship mapping and hierarchy")
    print("- Page profiling with importance scoring")
    print("- Related content discovery")
    print("- Quality assessment for extracted content")