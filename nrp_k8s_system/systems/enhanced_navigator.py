#!/usr/bin/env python3
"""
Enhanced Navigator for NRP K8s System
=====================================

Specifically designed to navigate and scrape the correct documentation sources:
- NRP Documentation: https://nrp.ai/documentation/ and subpages
- Kubernetes Official Docs: https://kubernetes.io/docs/ and specific sections
- Targeted search with proper link storage and citation
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import logging
from .nrp_search_navigator import NRPSearchNavigator
# Removed Ctrl+K search import

logger = logging.getLogger(__name__)

class EnhancedNavigator:
    """
    Enhanced Navigator that specifically targets NRP and Kubernetes documentation.

    Primary Sources:
    - https://nrp.ai/documentation/
    - https://nrp.ai/documentation/userdocs/ai/llm-managed/
    - https://kubernetes.io/docs/concepts/workloads/controllers/job/
    - Other kubernetes.io documentation sections
    """

    def __init__(self):
        # Initialize the NRP search navigator for better search results
        self.nrp_search_navigator = NRPSearchNavigator()

        # Removed Ctrl+K search initialization

        self.primary_sources = {
            "nrp_docs": [
                "https://nrp.ai/documentation/",
                "https://nrp.ai/documentation/userdocs/ai/llm-managed/",
                "https://nrp.ai/documentation/userdocs/",
                "https://nrp.ai/documentation/userdocs/storage/",
                "https://nrp.ai/documentation/userdocs/kubernetes/",
                "https://nrp.ai/documentation/userdocs/gpu/",
                "https://nrp.ai/documentation/userdocs/fpgas/",
                "https://nrp.ai/documentation/userdocs/fpgas/esnet_development/",
                "https://nrp.ai/documentation/admindocs/",
                "https://nrp.ai/documentation/admindocs/cluster/",
                "https://nrp.ai/documentation/admindocs/cluster/fpga/",
            ],
            "k8s_docs": [
                "https://kubernetes.io/docs/concepts/",
                "https://kubernetes.io/docs/concepts/workloads/controllers/job/",
                "https://kubernetes.io/docs/concepts/workloads/pods/",
                "https://kubernetes.io/docs/concepts/services-networking/",
                "https://kubernetes.io/docs/concepts/storage/",
                "https://kubernetes.io/docs/concepts/configuration/",
                "https://kubernetes.io/docs/tasks/",
                "https://kubernetes.io/docs/reference/",
            ]
        }

        self.scraped_links = {}  # Cache for discovered links
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def discover_relevant_links(self, query: str) -> List[Dict[str, str]]:
        """
        Discover relevant documentation links based on query.
        Uses NRP's built-in search functionality for better accuracy.

        Returns:
            List of dicts with 'url', 'title', 'source_type', 'relevance'
        """
        discovered_links = []

        # Analyze query to determine focus areas
        query_lower = query.lower()
        focus_areas = self._analyze_query_focus(query_lower)

        print(f"[Enhanced Navigator] Query focus areas: {focus_areas}")

        # Method 1: Direct NRP documentation links for specific topics (highest priority)
        if 'fpga' in focus_areas or 'admin' in focus_areas:
            print(f"[Enhanced Navigator] FPGA/Admin query detected, using direct admin documentation links")
            direct_admin_links = self._get_direct_admin_links(query_lower, focus_areas)
            discovered_links.extend(direct_admin_links)

        # Method 2: Enhanced NRP search for better targeting (high priority)

        # Method 3: Use NRP's built-in search (high priority)
        nrp_search_results = self._search_nrp_using_builtin_search(query, focus_areas)
        discovered_links.extend(nrp_search_results)

        # Method 4: Fallback to manual NRP link discovery if search returns insufficient results
        if len(discovered_links) < 3:
            print(f"[Enhanced Navigator] Need more sources, using manual discovery (current: {len(discovered_links)})")
            manual_nrp_links = self._discover_nrp_links(query_lower, focus_areas)
            discovered_links.extend(manual_nrp_links)

        # Method 4: Search Kubernetes documentation (only if not FPGA/admin)
        if not any(area in focus_areas for area in ['fpga', 'admin']):
            if any(area in focus_areas for area in ['k8s', 'job', 'pod', 'service', 'storage', 'general']):
                k8s_links = self._discover_k8s_links(query_lower, focus_areas)
                discovered_links.extend(k8s_links)

        # Remove duplicates while preserving order
        seen_urls = set()
        unique_links = []
        for link in discovered_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)

        # Sort by relevance
        unique_links.sort(key=lambda x: x.get('relevance', 0), reverse=True)

        print(f"[Enhanced Navigator] Discovered {len(unique_links)} unique relevant links")
        return unique_links[:10]  # Return top 10 most relevant

    def _get_direct_admin_links(self, query: str, focus_areas: List[str]) -> List[Dict[str, str]]:
        """Get direct links to admin documentation for FPGA and hardware queries."""
        admin_links = []

        # DPDK/ESnet development queries get highest priority
        if 'dpdk' in focus_areas or 'esnet_development' in focus_areas:
            admin_links.append({
                'url': 'https://nrp.ai/documentation/userdocs/fpgas/esnet_development/',
                'title': 'ESnet SmartNIC Development Guide',
                'description': 'Complete ESnet development guide including DPDK prerequisites (hugepages, IOMMU)',
                'source_type': 'nrp_user_docs',
                'relevance': 1.0  # Highest relevance for DPDK/ESnet queries
            })
            admin_links.append({
                'url': 'https://nrp.ai/documentation/userdocs/fpgas/esnet_development/#technical-information-for-reproducing-this-experiment-in-a-different-environment',
                'title': 'ESnet DPDK Technical Prerequisites',
                'description': 'Specific technical information for DPDK hugepages and IOMMU requirements',
                'source_type': 'nrp_user_docs',
                'relevance': 1.0
            })

        # FPGA-specific direct links
        if 'fpga' in focus_areas:
            admin_links.append({
                'url': 'https://nrp.ai/documentation/admindocs/cluster/fpga/',
                'title': 'FPGA Configuration and Management',
                'description': 'Administrative documentation for FPGA hardware including Alveo U55C and SmartNIC workflows',
                'source_type': 'nrp_admin_docs',
                'relevance': 0.9  # High relevance for general FPGA queries
            })

        # Admin cluster documentation
        if 'admin' in focus_areas or 'cluster' in query:
            admin_links.append({
                'url': 'https://nrp.ai/documentation/admindocs/cluster/',
                'title': 'Cluster Administration Documentation',
                'description': 'Administrative documentation for cluster management and hardware configuration',
                'source_type': 'nrp_admin_docs',
                'relevance': 0.9
            })

        # General admin docs
        admin_links.append({
            'url': 'https://nrp.ai/documentation/admindocs/',
            'title': 'Administrative Documentation',
            'description': 'Complete administrative documentation for NRP infrastructure',
            'source_type': 'nrp_admin_docs',
            'relevance': 0.8
        })

        print(f"[Enhanced Navigator] Added {len(admin_links)} direct admin documentation links")
        return admin_links

    # Removed _search_using_ctrlk method - using enhanced NRP search instead

    def _analyze_query_focus(self, query: str) -> List[str]:
        """Analyze query to determine focus areas with enhanced GPU detection."""
        focus_areas = []
        query_lower = query.lower()

        # Enhanced GPU detection
        gpu_keywords = [
            'gpu', 'nvidia', 'cuda', 'a100', 'v100', 'k80', 'titan', 'tesla',
            'graphics', 'compute', 'ml', 'ai', 'machine learning', 'deep learning',
            'pytorch', 'tensorflow', 'training', 'inference', 'model'
        ]
        if any(keyword in query_lower for keyword in gpu_keywords):
            focus_areas.append('gpu')

            # Specific GPU types
            if any(gpu_type in query_lower for gpu_type in ['a100', 'ampere']):
                focus_areas.append('a100')
            if any(gpu_type in query_lower for gpu_type in ['v100', 'volta']):
                focus_areas.append('v100')

        # NRP-specific keywords
        nrp_keywords = ['nrp', 'nautilus', 'prp', 'ucsd', 'national research platform']
        if any(keyword in query_lower for keyword in nrp_keywords):
            focus_areas.append('nrp')

        # Kubernetes-specific keywords
        k8s_keywords = ['kubernetes', 'k8s', 'pod', 'deployment', 'service', 'kubectl', 'helm']
        if any(keyword in query_lower for keyword in k8s_keywords):
            focus_areas.append('k8s')

        # FPGA and specialized hardware detection
        fpga_keywords = ['fpga', 'alveo', 'smartnic', 'esnet', 'xilinx', 'vivado', 'xrt', 'flash', 'u55c']
        dpdk_keywords = ['dpdk', 'hugepages', 'iommu', 'passthrough', 'userspace', 'polling']
        if any(keyword in query_lower for keyword in fpga_keywords + dpdk_keywords):
            focus_areas.append('fpga')
            focus_areas.append('admin')  # FPGA docs are in admin section

            # Specific detection for DPDK/ESnet development queries
            if any(keyword in query_lower for keyword in dpdk_keywords + ['esnet', 'development', 'prerequisites']):
                focus_areas.append('dpdk')
                focus_areas.append('esnet_development')

        # Admin documentation keywords
        admin_keywords = ['admin', 'cluster', 'node', 'flashing', 'hardware', 'pci', 'lspci']
        if any(keyword in query_lower for keyword in admin_keywords):
            focus_areas.append('admin')

        # Enhanced resource type detection
        if any(keyword in query_lower for keyword in ['job', 'cronjob', 'batch', 'workload', 'task']):
            focus_areas.append('job')
        if any(keyword in query_lower for keyword in ['pod', 'container', 'docker']):
            focus_areas.append('pod')
        if any(keyword in query_lower for keyword in ['service', 'networking', 'ingress', 'load', 'balance']):
            focus_areas.append('service')
        if any(keyword in query_lower for keyword in ['storage', 'volume', 'pvc', 'persistent', 'ceph', 'nfs']):
            focus_areas.append('storage')
        if any(keyword in query_lower for keyword in ['llm', 'model', 'ai', 'machine learning', 'ml']):
            focus_areas.append('llm')

        # Resource management keywords
        if any(keyword in query_lower for keyword in ['quota', 'limit', 'request', 'resource', 'memory', 'cpu']):
            focus_areas.append('resources')

        # Policy and compliance keywords
        if any(keyword in query_lower for keyword in ['policy', 'rule', 'compliance', 'violation', 'warning']):
            focus_areas.append('policy')

        # Default to general if no specific focus
        if not focus_areas:
            focus_areas = ['general']

        return focus_areas

    def _search_nrp_using_builtin_search(self, query: str, focus_areas: List[str]) -> List[Dict[str, str]]:
        """
        Use NRP's built-in search functionality (Ctrl+K) for more accurate results.

        This method leverages the site's own search index for better accuracy.
        """
        try:
            print(f"[Enhanced Navigator] Using NRP built-in search for: {query}")

            # Use the NRP search navigator
            search_results = self.nrp_search_navigator.search_nrp_documentation(query, limit=8)

            # Convert search results to the expected format
            nrp_links = []
            for result in search_results:
                # Enhance relevance based on focus areas
                enhanced_relevance = self._enhance_search_relevance(result, focus_areas)

                nrp_link = {
                    'url': result['url'],
                    'title': result['title'],
                    'source_type': 'nrp_docs_search',
                    'relevance': enhanced_relevance,
                    'search_method': result.get('source', 'nrp_search'),
                    'snippet': result.get('snippet', ''),
                    'topic': result.get('topic', 'general'),
                    'content_type': result.get('content_type', 'documentation')
                }

                nrp_links.append(nrp_link)

            # Sort by enhanced relevance
            nrp_links.sort(key=lambda x: x['relevance'], reverse=True)

            print(f"[Enhanced Navigator] NRP search found {len(nrp_links)} results")
            return nrp_links

        except Exception as e:
            print(f"[!] NRP built-in search failed: {e}")
            return []

    def _enhance_search_relevance(self, result: Dict[str, Any], focus_areas: List[str]) -> float:
        """Enhance search result relevance based on focus areas."""
        base_relevance = result.get('relevance_score', 0.5)

        # Boost for focus area matches
        result_topic = result.get('topic', 'general')
        if result_topic in focus_areas:
            base_relevance += 0.2

        # Special boost for GPU-related content when GPU is in focus
        if 'gpu' in focus_areas or 'a100' in focus_areas or 'v100' in focus_areas:
            url_lower = result['url'].lower()
            title_lower = result['title'].lower()
            snippet_lower = result.get('snippet', '').lower()

            gpu_keywords = ['gpu', 'nvidia', 'cuda', 'a100', 'v100', 'tesla']
            for keyword in gpu_keywords:
                if keyword in url_lower:
                    base_relevance += 0.3
                    break
                elif keyword in title_lower:
                    base_relevance += 0.2
                    break
                elif keyword in snippet_lower:
                    base_relevance += 0.1
                    break

        # Boost for high-quality content types
        content_type = result.get('content_type', 'documentation')
        if content_type in ['tutorial', 'guide']:
            base_relevance += 0.1

        # Boost for official search results (they're pre-ranked by the site)
        if result.get('source') in ['api_search', 'html_parse']:
            base_relevance += 0.1

        return min(1.0, base_relevance)

    def _discover_nrp_links(self, query: str, focus_areas: List[str]) -> List[Dict[str, str]]:
        """Discover relevant NRP documentation links."""
        links = []

        # Prioritize sources based on focus areas with enhanced targeting
        prioritized_sources = []

        # FPGA/Admin-specific sources (highest priority for FPGA queries)
        if 'fpga' in focus_areas or 'admin' in focus_areas:
            prioritized_sources.extend([
                "https://nrp.ai/documentation/admindocs/cluster/fpga/",
                "https://nrp.ai/documentation/admindocs/cluster/",
                "https://nrp.ai/documentation/admindocs/",
                "https://nrp.ai/documentation/",
            ])

        # GPU-specific sources (highest priority for GPU queries)
        if 'gpu' in focus_areas or 'a100' in focus_areas or 'v100' in focus_areas:
            prioritized_sources.extend([
                "https://nrp.ai/documentation/userdocs/gpu/",
                "https://nrp.ai/documentation/userdocs/kubernetes/",  # K8s docs often have GPU examples
                "https://nrp.ai/documentation/userdocs/ai/llm-managed/",  # LLM docs often have GPU config
                "https://nrp.ai/documentation/userdocs/",
                "https://nrp.ai/documentation/",
            ])

        # LLM-specific sources
        if 'llm' in focus_areas:
            prioritized_sources.extend([
                "https://nrp.ai/documentation/userdocs/ai/llm-managed/",
                "https://nrp.ai/documentation/userdocs/gpu/",  # LLM usually needs GPU
            ])

        # Storage-specific sources
        if 'storage' in focus_areas:
            prioritized_sources.append("https://nrp.ai/documentation/userdocs/storage/")

        # Kubernetes-specific sources
        if 'k8s' in focus_areas:
            prioritized_sources.append("https://nrp.ai/documentation/userdocs/kubernetes/")

        # Policy and resource management
        if 'policy' in focus_areas or 'resources' in focus_areas:
            prioritized_sources.extend([
                "https://nrp.ai/documentation/userdocs/",
                "https://nrp.ai/documentation/policies/",
                "https://nrp.ai/documentation/best-practices/",
            ])

        # Always include main documentation if not already added
        if "https://nrp.ai/documentation/" not in prioritized_sources:
            prioritized_sources.append("https://nrp.ai/documentation/")
        if "https://nrp.ai/documentation/userdocs/" not in prioritized_sources:
            prioritized_sources.append("https://nrp.ai/documentation/userdocs/")

        for base_url in prioritized_sources:
            try:
                discovered = self._scrape_documentation_links(base_url, 'nrp', query, focus_areas)
                links.extend(discovered)
            except Exception as e:
                print(f"[!] Failed to scrape {base_url}: {e}")
                # Add the base URL as fallback
                links.append({
                    'url': base_url,
                    'title': f"NRP Documentation - {base_url.split('/')[-2] or 'Main'}",
                    'source_type': 'nrp_docs',
                    'relevance': 0.7
                })

        return links

    def _discover_k8s_links(self, query: str, focus_areas: List[str]) -> List[Dict[str, str]]:
        """Discover relevant Kubernetes documentation links."""
        links = []

        # Map focus areas to specific K8s documentation sections
        focus_to_k8s_sections = {
            'job': [
                "https://kubernetes.io/docs/concepts/workloads/controllers/job/",
                "https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/"
            ],
            'pod': [
                "https://kubernetes.io/docs/concepts/workloads/pods/",
                "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"
            ],
            'service': [
                "https://kubernetes.io/docs/concepts/services-networking/service/",
                "https://kubernetes.io/docs/concepts/services-networking/ingress/"
            ],
            'storage': [
                "https://kubernetes.io/docs/concepts/storage/volumes/",
                "https://kubernetes.io/docs/concepts/storage/persistent-volumes/"
            ],
            'gpu': [
                "https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/",
                "https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/"
            ]
        }

        # Collect relevant sections
        target_sections = []
        for focus in focus_areas:
            if focus in focus_to_k8s_sections:
                target_sections.extend(focus_to_k8s_sections[focus])

        # Add general sections if no specific focus
        if not target_sections or 'general' in focus_areas:
            target_sections.extend([
                "https://kubernetes.io/docs/concepts/",
                "https://kubernetes.io/docs/tasks/",
                "https://kubernetes.io/docs/reference/"
            ])

        for section_url in target_sections:
            try:
                discovered = self._scrape_documentation_links(section_url, 'k8s', query, focus_areas)
                links.extend(discovered)
            except Exception as e:
                print(f"[!] Failed to scrape {section_url}: {e}")
                # Add the section URL as fallback
                links.append({
                    'url': section_url,
                    'title': f"Kubernetes Docs - {section_url.split('/')[-2]}",
                    'source_type': 'k8s_docs',
                    'relevance': 0.6
                })

        return links

    def _scrape_documentation_links(self, base_url: str, source_type: str,
                                   query: str, focus_areas: List[str]) -> List[Dict[str, str]]:
        """Scrape a documentation site for relevant links."""
        if base_url in self.scraped_links:
            return self.scraped_links[base_url]

        try:
            print(f"[Enhanced Navigator] Scraping {base_url}")
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = []

            # Find all relevant links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if not href:
                    continue

                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)

                # Filter relevant links
                if self._is_relevant_link(full_url, source_type, query, focus_areas):
                    title = link.get_text(strip=True) or self._extract_title_from_url(full_url)
                    relevance = self._calculate_link_relevance(full_url, title, query, focus_areas)

                    links.append({
                        'url': full_url,
                        'title': title,
                        'source_type': f"{source_type}_docs",
                        'relevance': relevance
                    })

            # Cache the results
            self.scraped_links[base_url] = links
            print(f"[Enhanced Navigator] Found {len(links)} links in {base_url}")
            return links

        except Exception as e:
            print(f"[!] Error scraping {base_url}: {e}")
            return []

    def _is_relevant_link(self, url: str, source_type: str, query: str, focus_areas: List[str]) -> bool:
        """Check if a link is relevant for the query."""
        url_lower = url.lower()

        # Filter by source type
        if source_type == 'nrp':
            if not ('nrp.ai' in url_lower and 'documentation' in url_lower):
                return False
        elif source_type == 'k8s':
            if not ('kubernetes.io' in url_lower and 'docs' in url_lower):
                return False

        # Check for focus area relevance
        for focus in focus_areas:
            if focus in url_lower:
                return True

        # Check query keywords in URL
        query_words = re.findall(r'\w+', query.lower())
        for word in query_words:
            if len(word) > 3 and word in url_lower:
                return True

        return False

    def _calculate_link_relevance(self, url: str, title: str, query: str, focus_areas: List[str]) -> float:
        """Calculate relevance score for a link with enhanced GPU prioritization."""
        relevance = 0.0

        url_lower = url.lower()
        title_lower = title.lower()
        query_lower = query.lower()

        # Base relevance for official sources
        if 'nrp.ai' in url_lower:
            relevance += 0.8
        elif 'kubernetes.io' in url_lower:
            relevance += 0.7

        # Enhanced focus area boosting
        for focus in focus_areas:
            # Higher boost for GPU-related focus areas
            if focus in ['gpu', 'a100', 'v100'] and focus in url_lower:
                relevance += 0.4  # Higher boost for GPU
            elif focus in url_lower:
                relevance += 0.3

            if focus in ['gpu', 'a100', 'v100'] and focus in title_lower:
                relevance += 0.3  # Higher boost for GPU titles
            elif focus in title_lower:
                relevance += 0.2

        # Enhanced query keyword matching
        query_words = re.findall(r'\w+', query_lower)
        for word in query_words:
            if len(word) > 3:
                # Specific GPU model matching gets highest boost
                if word in ['a100', 'v100', 'k80'] and word in url_lower:
                    relevance += 0.5
                elif word in ['a100', 'v100', 'k80'] and word in title_lower:
                    relevance += 0.4
                # General keyword matching
                elif word in url_lower:
                    relevance += 0.2
                elif word in title_lower:
                    relevance += 0.3

        # Special boost for GPU documentation paths
        if 'gpu' in focus_areas or 'a100' in focus_areas or 'v100' in focus_areas:
            if any(gpu_path in url_lower for gpu_path in ['/gpu/', '/nvidia/', '/cuda/', '/hardware/']):
                relevance += 0.3

        # Boost for resource-related documentation when asking about resources
        if 'resources' in focus_areas or any(resource_word in query_lower for resource_word in ['request', 'limit', 'quota']):
            if any(resource_path in url_lower for resource_path in ['/resources/', '/limits/', '/quota/']):
                relevance += 0.2

        # Boost for specific documentation sections
        high_value_sections = [
            'examples', 'tutorials', 'getting-started', 'how-to', 'configuration',
            'best-practices', 'troubleshooting', 'reference'
        ]
        for section in high_value_sections:
            if section in url_lower or section in title_lower:
                relevance += 0.1

        # Cap at 1.0
        return min(1.0, relevance)

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL."""
        path = urlparse(url).path
        parts = [part for part in path.split('/') if part]
        if parts:
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        return url

    def extract_content_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """Extract content from a specific documentation URL."""
        try:
            print(f"[Enhanced Navigator] Extracting content from {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove navigation, script, style elements
            for element in soup(['nav', 'script', 'style', 'footer', 'header']):
                element.decompose()

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.get_text(strip=True)
            elif soup.h1:
                title = soup.h1.get_text(strip=True)

            # Extract main content
            content_selectors = [
                'main', 'article', '.content', '.documentation',
                '.docs-content', '.markdown-body', '#content'
            ]

            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(' ', strip=True)
                    break

            # Fallback to all paragraphs and headings
            if not content:
                elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                content = ' '.join(elem.get_text(' ', strip=True) for elem in elements)

            # Clean up content
            content = re.sub(r'\s+', ' ', content).strip()

            return {
                'url': url,
                'title': title,
                'content': content[:10000],  # Limit content length
                'source_type': 'nrp_docs' if 'nrp.ai' in url else 'k8s_docs'
            }

        except Exception as e:
            print(f"[!] Failed to extract content from {url}: {e}")
            return None

    def get_cached_links(self) -> Dict[str, List[Dict[str, str]]]:
        """Get all cached links organized by source."""
        return self.scraped_links