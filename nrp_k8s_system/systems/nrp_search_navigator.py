#!/usr/bin/env python3
"""
NRP Search Navigator
===================

Utilizes the nrp.ai/documentation search functionality (Ctrl+K) to find
relevant documentation more efficiently than manual link discovery.

Features:
- Direct integration with NRP's built-in search
- Automated search query optimization for better results
- Parse structured search results
- Extract content from top search results
- Better accuracy for specific queries like A100 GPUs
"""

import os
import re
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NRPSearchNavigator:
    """
    Navigator that uses NRP's built-in search functionality for better results.

    This approach is more effective because:
    1. Uses NRP's own search index
    2. Gets pre-ranked results
    3. Accesses the same results users would see
    4. More accurate than manual link discovery
    """

    def __init__(self):
        self.base_url = "https://nrp.ai"
        self.doc_base = "https://nrp.ai/documentation"

        # Cache for search results
        self.search_cache = {}

        # Session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def search_nrp_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search NRP documentation using their built-in search.

        Args:
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List of search results with metadata
        """
        try:
            print(f"[NRP Search] Searching for: {query}")

            # Check cache first
            cache_key = f"{query}_{limit}"
            if cache_key in self.search_cache:
                print(f"[NRP Search] Using cached results")
                return self.search_cache[cache_key]

            # Optimize query for better results
            optimized_query = self._optimize_search_query(query)
            print(f"[NRP Search] Optimized query: {optimized_query}")

            # Try multiple search approaches
            results = []

            # Approach 1: Try to find and use the search API endpoint
            api_results = self._search_via_api(optimized_query, limit)
            if api_results:
                results.extend(api_results)

            # Approach 2: Search via site search if API doesn't work
            if not results:
                site_results = self._search_via_site_search(optimized_query, limit)
                results.extend(site_results)

            # Approach 3: Fallback to Google site search
            if not results:
                google_results = self._search_via_google_site(optimized_query, limit)
                results.extend(google_results)

            # Enhance results with content previews
            enhanced_results = self._enhance_search_results(results, query)

            # Cache results
            self.search_cache[cache_key] = enhanced_results

            print(f"[NRP Search] Found {len(enhanced_results)} results")
            return enhanced_results

        except Exception as e:
            logger.error(f"NRP search failed: {e}")
            return []

    def _optimize_search_query(self, query: str) -> str:
        """Optimize search query for better NRP documentation results."""
        optimized = query.lower()

        # Add NRP-specific context
        optimizations = []

        # GPU-specific optimizations
        if any(gpu_term in optimized for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
            optimizations.extend(['gpu', 'nvidia', 'kubernetes'])

            # Specific GPU model optimization
            if 'a100' in optimized:
                optimizations.append('a100')
            elif 'v100' in optimized:
                optimizations.append('v100')

        # Resource request optimizations
        if any(resource_term in optimized for resource_term in ['request', 'limit', 'quota']):
            optimizations.extend(['resources', 'limits', 'requests'])

        # Job/workload optimizations
        if any(job_term in optimized for job_term in ['job', 'batch', 'workload']):
            optimizations.extend(['job', 'batch', 'kubernetes'])

        # Storage optimizations
        if any(storage_term in optimized for storage_term in ['storage', 'volume', 'pvc']):
            optimizations.extend(['storage', 'persistent', 'volume'])

        # Combine original query with optimizations
        query_terms = query.split() + optimizations

        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in query_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)

        return ' '.join(unique_terms)

    def _search_via_api(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using NRP's search API if available."""
        try:
            # First, try to find the search endpoint by examining the documentation site
            search_endpoints = [
                f"{self.base_url}/api/search",
                f"{self.doc_base}/search",
                f"{self.base_url}/search",
                f"{self.doc_base}/api/search"
            ]

            for endpoint in search_endpoints:
                try:
                    # Try GET request with query parameter
                    response = self.session.get(
                        endpoint,
                        params={'q': query, 'limit': limit},
                        timeout=10
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and 'results' in data:
                                return self._parse_api_results(data['results'])
                            elif isinstance(data, list):
                                return self._parse_api_results(data)
                        except json.JSONDecodeError:
                            # Not JSON, might be HTML with results
                            html_results = self._parse_search_html(response.text, query)
                            if html_results:
                                return html_results

                except requests.RequestException:
                    continue

            return []

        except Exception as e:
            logger.warning(f"API search failed: {e}")
            return []

    def _search_via_site_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search by accessing the documentation site search functionality."""
        try:
            # Visit the documentation homepage first
            homepage_response = self.session.get(f"{self.doc_base}/", timeout=15)
            homepage_response.raise_for_status()

            # Look for search functionality in the page
            soup = BeautifulSoup(homepage_response.content, 'html.parser')

            # Look for search forms or search-related elements
            search_forms = soup.find_all('form', {'role': 'search'}) or soup.find_all('form', class_=re.compile(r'search', re.I))
            search_inputs = soup.find_all('input', {'type': 'search'}) or soup.find_all('input', {'placeholder': re.compile(r'search', re.I)})

            # Try to find search endpoint from forms
            search_url = None
            for form in search_forms:
                action = form.get('action')
                if action:
                    search_url = urljoin(self.doc_base, action)
                    break

            if not search_url:
                # Look for JavaScript-based search
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'search' in script.string.lower():
                        # Try to extract search endpoint from JavaScript
                        search_patterns = [
                            r'["\']([^"\']*search[^"\']*)["\']',
                            r'endpoint["\']?\s*:\s*["\']([^"\']+)["\']',
                            r'url["\']?\s*:\s*["\']([^"\']*search[^"\']*)["\']'
                        ]

                        for pattern in search_patterns:
                            matches = re.findall(pattern, script.string, re.I)
                            for match in matches:
                                if 'search' in match.lower() and '/' in match:
                                    search_url = urljoin(self.doc_base, match)
                                    break
                            if search_url:
                                break

            # If we found a search URL, try to use it
            if search_url:
                print(f"[NRP Search] Found search endpoint: {search_url}")

                # Try different parameter formats
                param_formats = [
                    {'q': query},
                    {'query': query},
                    {'search': query},
                    {'term': query}
                ]

                for params in param_formats:
                    try:
                        response = self.session.get(search_url, params=params, timeout=10)
                        if response.status_code == 200:
                            results = self._parse_search_html(response.text, query)
                            if results:
                                return results[:limit]
                    except:
                        continue

            # Fallback: Look for sitemap or all documentation links
            return self._fallback_content_discovery(query, limit)

        except Exception as e:
            logger.warning(f"Site search failed: {e}")
            return []

    def _search_via_google_site(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Use Google site search as fallback."""
        try:
            # Google site search query
            google_query = f"site:nrp.ai/documentation {query}"
            google_url = f"https://www.google.com/search?q={quote(google_query)}"

            response = self.session.get(google_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            # Parse Google search results
            for result in soup.find_all('div', class_='g')[:limit]:
                try:
                    link_elem = result.find('a', href=True)
                    title_elem = result.find('h3')
                    snippet_elem = result.find('span', class_=re.compile(r'st|aCOpRe'))

                    if link_elem and title_elem:
                        url = link_elem['href']
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]

                        if 'nrp.ai/documentation' in url:
                            results.append({
                                'title': title_elem.get_text(strip=True),
                                'url': url,
                                'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                                'source': 'google_site_search',
                                'relevance_score': self._calculate_relevance(
                                    title_elem.get_text(strip=True),
                                    snippet_elem.get_text(strip=True) if snippet_elem else '',
                                    query
                                )
                            })
                except:
                    continue

            return results

        except Exception as e:
            logger.warning(f"Google site search failed: {e}")
            return []

    def _fallback_content_discovery(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback method to discover relevant content."""
        try:
            # Get the main documentation page and extract all links
            response = self.session.get(f"{self.doc_base}/", timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all documentation links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(self.doc_base, href)

                # Filter for documentation URLs
                if ('nrp.ai/documentation' in full_url and
                    not any(skip in full_url for skip in ['#', 'javascript:', 'mailto:'])):

                    title = link.get_text(strip=True) or self._extract_title_from_url(full_url)

                    # Calculate relevance based on URL and title
                    relevance = self._calculate_relevance(title, full_url, query)

                    if relevance > 0.1:  # Only include somewhat relevant links
                        links.append({
                            'title': title,
                            'url': full_url,
                            'snippet': '',
                            'source': 'fallback_discovery',
                            'relevance_score': relevance
                        })

            # Sort by relevance and return top results
            links.sort(key=lambda x: x['relevance_score'], reverse=True)
            return links[:limit]

        except Exception as e:
            logger.warning(f"Fallback content discovery failed: {e}")
            return []

    def _parse_api_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Parse search results from API response."""
        parsed_results = []

        for result in results:
            try:
                parsed_result = {
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('description', result.get('snippet', '')),
                    'source': 'api_search',
                    'relevance_score': result.get('score', result.get('relevance', 0.5))
                }

                # Ensure URL is absolute
                if parsed_result['url'].startswith('/'):
                    parsed_result['url'] = urljoin(self.base_url, parsed_result['url'])

                parsed_results.append(parsed_result)

            except Exception as e:
                logger.warning(f"Failed to parse API result: {e}")
                continue

        return parsed_results

    def _parse_search_html(self, html: str, query: str) -> List[Dict[str, Any]]:
        """Parse search results from HTML response."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = []

            # Look for common search result patterns
            result_selectors = [
                '.search-result',
                '.search-item',
                '.result',
                '.hit',
                '[data-search-result]',
                'article',
                '.doc-item'
            ]

            for selector in result_selectors:
                result_elements = soup.select(selector)
                if result_elements:
                    break

            if not result_elements:
                # Fallback: look for any links in the page
                result_elements = soup.find_all('a', href=True)

            for element in result_elements:
                try:
                    # Extract link
                    if element.name == 'a':
                        link = element
                    else:
                        link = element.find('a', href=True)

                    if not link:
                        continue

                    url = link['href']
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)

                    # Only include documentation URLs
                    if 'nrp.ai/documentation' not in url:
                        continue

                    # Extract title
                    title = ''
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or link
                    if title_elem:
                        title = title_elem.get_text(strip=True)

                    # Extract snippet
                    snippet = ''
                    snippet_elem = element.find(['p', '.excerpt', '.description', '.summary'])
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)[:200]

                    # Calculate relevance
                    relevance = self._calculate_relevance(title, snippet, query)

                    if relevance > 0.1:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'html_parse',
                            'relevance_score': relevance
                        })

                except Exception as e:
                    logger.warning(f"Failed to parse search result element: {e}")
                    continue

            # Remove duplicates and sort by relevance
            seen_urls = set()
            unique_results = []
            for result in results:
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    unique_results.append(result)

            unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return unique_results

        except Exception as e:
            logger.warning(f"Failed to parse search HTML: {e}")
            return []

    def _enhance_search_results(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Enhance search results with additional metadata and content previews."""
        enhanced_results = []

        for result in results:
            try:
                enhanced_result = result.copy()

                # Get content preview if snippet is missing or short
                if len(result.get('snippet', '')) < 50:
                    preview = self._get_content_preview(result['url'])
                    if preview:
                        enhanced_result['content_preview'] = preview

                # Enhance relevance score
                enhanced_result['relevance_score'] = self._enhanced_relevance_calculation(
                    result, original_query
                )

                # Add topic classification
                enhanced_result['topic'] = self._classify_content_topic(result)

                # Add content type
                enhanced_result['content_type'] = self._classify_content_type(result)

                enhanced_results.append(enhanced_result)

            except Exception as e:
                logger.warning(f"Failed to enhance result {result.get('url', '')}: {e}")
                enhanced_results.append(result)  # Add original if enhancement fails

        return enhanced_results

    def _get_content_preview(self, url: str) -> Optional[str]:
        """Get a content preview from the URL."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get main content
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

            # Fallback to all text
            if not content:
                content = soup.get_text(' ', strip=True)

            # Return first 300 characters
            return content[:300] + "..." if len(content) > 300 else content

        except Exception as e:
            logger.warning(f"Failed to get content preview for {url}: {e}")
            return None

    def _calculate_relevance(self, title: str, text: str, query: str) -> float:
        """Calculate relevance score for a result."""
        relevance = 0.0

        title_lower = title.lower()
        text_lower = text.lower()
        query_lower = query.lower()

        query_words = query_lower.split()

        # Title matching (highest weight)
        for word in query_words:
            if word in title_lower:
                relevance += 0.4

        # Text matching
        for word in query_words:
            if word in text_lower:
                relevance += 0.2

        # Exact phrase matching
        if query_lower in title_lower:
            relevance += 0.5
        if query_lower in text_lower:
            relevance += 0.3

        # GPU-specific boosting
        if any(gpu_term in query_lower for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
            if any(gpu_term in title_lower for gpu_term in ['gpu', 'a100', 'v100', 'nvidia']):
                relevance += 0.3

        return min(1.0, relevance)

    def _enhanced_relevance_calculation(self, result: Dict[str, Any], query: str) -> float:
        """Enhanced relevance calculation with more factors."""
        base_score = result.get('relevance_score', 0.5)

        # URL quality bonus
        url = result.get('url', '')
        if '/gpu/' in url.lower():
            base_score += 0.2
        if '/examples/' in url.lower() or '/tutorial/' in url.lower():
            base_score += 0.1

        # Title quality
        title = result.get('title', '')
        if any(quality_term in title.lower() for quality_term in ['guide', 'tutorial', 'example', 'how-to']):
            base_score += 0.1

        return min(1.0, base_score)

    def _classify_content_topic(self, result: Dict[str, Any]) -> str:
        """Classify the topic of the content."""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        text = result.get('snippet', '').lower()

        all_text = f"{url} {title} {text}"

        if any(gpu_term in all_text for gpu_term in ['gpu', 'nvidia', 'cuda', 'a100', 'v100']):
            return 'gpu'
        elif any(storage_term in all_text for storage_term in ['storage', 'volume', 'pvc', 'ceph']):
            return 'storage'
        elif any(net_term in all_text for net_term in ['network', 'ingress', 'service']):
            return 'networking'
        elif any(job_term in all_text for job_term in ['job', 'batch', 'cron']):
            return 'jobs'
        else:
            return 'general'

    def _classify_content_type(self, result: Dict[str, Any]) -> str:
        """Classify the type of content."""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        if any(example_term in title for example_term in ['example', 'tutorial', 'guide']):
            return 'tutorial'
        elif any(ref_term in url for ref_term in ['reference', 'api']):
            return 'reference'
        elif any(concept_term in title for concept_term in ['concept', 'overview', 'introduction']):
            return 'concept'
        else:
            return 'documentation'

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL."""
        path = urlparse(url).path
        parts = [part for part in path.split('/') if part]
        if parts:
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        return url

    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for improving queries."""
        suggestions = []
        query_lower = query.lower()

        # GPU-specific suggestions
        if 'gpu' in query_lower:
            if 'a100' not in query_lower and 'v100' not in query_lower:
                suggestions.extend([
                    f"{query} A100",
                    f"{query} V100",
                    f"{query} NVIDIA"
                ])

            if 'kubernetes' not in query_lower:
                suggestions.append(f"{query} Kubernetes")

        # Add context suggestions
        context_additions = {
            'storage': ['PVC', 'persistent volume', 'Ceph'],
            'network': ['ingress', 'service', 'load balancer'],
            'job': ['batch', 'workload', 'scheduling']
        }

        for topic, additions in context_additions.items():
            if topic in query_lower:
                for addition in additions:
                    if addition.lower() not in query_lower:
                        suggestions.append(f"{query} {addition}")

        return suggestions[:5]


# Convenience functions
def search_nrp_docs(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search NRP documentation using the enhanced search navigator."""
    navigator = NRPSearchNavigator()
    return navigator.search_nrp_documentation(query, limit)

def get_best_nrp_result(query: str) -> Optional[Dict[str, Any]]:
    """Get the best single result for a query."""
    results = search_nrp_docs(query, limit=1)
    return results[0] if results else None