#!/usr/bin/env python3
"""
Comprehensive NRP Scraper
=========================

Systematic dry-run scraping of ALL NRP documentation to build comprehensive
knowledge base, validate links, and create exhaustive keyword mappings.

This solves edge cases by proactively building complete knowledge rather than
reactive extraction.

Features:
- Complete NRP documentation tree traversal
- Link validation and health checking
- Keyword extraction and mapping
- Content categorization and indexing
- Broken link detection and reporting
- Comprehensive knowledge base population
"""

import os
import re
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from collections import defaultdict
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class ComprehensiveNRPScraper:
    """Complete NRP documentation scraper with edge case handling."""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "comprehensive_scraping"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Storage files
        self.links_db_file = self.cache_dir / "all_nrp_links.json"
        self.content_db_file = self.cache_dir / "content_database.json"
        self.keywords_db_file = self.cache_dir / "keyword_mappings.json"
        self.broken_links_file = self.cache_dir / "broken_links.json"
        self.scraping_report_file = self.cache_dir / "scraping_report.json"

        # NRP documentation structure
        self.nrp_base = "https://nrp.ai/documentation/"
        self.discovered_links = set()
        self.validated_links = {}
        self.broken_links = []
        self.content_database = {}
        self.keyword_mappings = defaultdict(set)
        self.section_mappings = {}

        # Comprehensive link patterns for NRP
        self.nrp_sections = [
            "",  # Main documentation
            "userdocs/",
            "userdocs/ai/",
            "userdocs/ai/llm-managed/",
            "userdocs/storage/",
            "userdocs/kubernetes/",
            "userdocs/gpu/",
            "userdocs/networking/",
            "userdocs/jupyter/",
            "admindocs/",
            "admindocs/cluster/",
            "admindocs/cluster/fpga/",
            "admindocs/cluster/gpu/",
            "admindocs/cluster/storage/",
            "admindocs/cluster/networking/",
            "admindocs/operations/",
            "admindocs/policies/",
            "tutorials/",
            "tutorials/quickstart/",
            "tutorials/gpu/",
            "tutorials/storage/",
            "tutorials/networking/",
            "examples/",
            "examples/kubernetes/",
            "examples/gpu/",
            "examples/storage/",
            "faq/",
            "glossary/",
            "changelog/",
            "support/",
        ]

        # Content categories for better organization
        self.content_categories = {
            'gpu': ['gpu', 'nvidia', 'cuda', 'a100', 'v100', 'graphics'],
            'fpga': ['fpga', 'alveo', 'smartnic', 'esnet', 'xilinx', 'vivado'],
            'storage': ['storage', 'pvc', 'volume', 'persistent', 'ceph', 'nfs'],
            'networking': ['network', 'ingress', 'service', 'loadbalancer'],
            'kubernetes': ['kubernetes', 'k8s', 'pod', 'deployment', 'job'],
            'ai_ml': ['ai', 'ml', 'llm', 'model', 'pytorch', 'tensorflow'],
            'admin': ['admin', 'cluster', 'node', 'policy', 'operations'],
            'jupyter': ['jupyter', 'notebook', 'lab', 'hub'],
            'tutorials': ['tutorial', 'example', 'quickstart', 'guide'],
            'troubleshooting': ['troubleshoot', 'debug', 'error', 'fix', 'issue']
        }

    def run_comprehensive_scraping(self) -> Dict[str, Any]:
        """Run complete NRP documentation scraping."""
        print(f"[Comprehensive Scraper] Starting complete NRP documentation scraping...")
        start_time = time.time()

        try:
            # Step 1: Discover all possible links
            print(f"[Step 1] Discovering all NRP documentation links...")
            self._discover_all_nrp_links()

            # Step 2: Validate all discovered links
            print(f"[Step 2] Validating discovered links...")
            self._validate_all_links()

            # Step 3: Scrape content from valid links
            print(f"[Step 3] Scraping content from valid links...")
            self._scrape_all_content()

            # Step 4: Extract and map keywords
            print(f"[Step 4] Extracting and mapping keywords...")
            self._extract_comprehensive_keywords()

            # Step 5: Build section mappings
            print(f"[Step 5] Building section mappings...")
            self._build_section_mappings()

            # Step 6: Save all data
            print(f"[Step 6] Saving comprehensive database...")
            self._save_comprehensive_data()

            # Step 7: Generate report
            report = self._generate_scraping_report(start_time)

            print(f"[Comprehensive Scraper] Complete! Processed {len(self.validated_links)} pages")
            return report

        except Exception as e:
            logger.error(f"Comprehensive scraping failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _discover_all_nrp_links(self):
        """Discover all possible NRP documentation links."""
        print(f"[Discovery] Starting link discovery...")

        # Method 1: Systematic section exploration
        for section in self.nrp_sections:
            url = urljoin(self.nrp_base, section)
            self.discovered_links.add(url)

            # Also try common variations
            variations = [
                f"{section}index.html",
                f"{section}README.md",
                f"{section}overview/",
                f"{section}getting-started/",
                f"{section}configuration/",
                f"{section}examples/",
                f"{section}troubleshooting/",
            ]

            for variation in variations:
                variant_url = urljoin(self.nrp_base, variation)
                self.discovered_links.add(variant_url)

        # Method 2: Sitemap exploration (if available)
        self._explore_sitemap()

        # Method 3: Recursive link following from main pages
        self._recursive_link_discovery()

        print(f"[Discovery] Discovered {len(self.discovered_links)} potential links")

    def _explore_sitemap(self):
        """Try to find and explore sitemap."""
        sitemap_urls = [
            f"{self.nrp_base}sitemap.xml",
            f"{self.nrp_base}sitemap/",
            f"https://nrp.ai/sitemap.xml",
        ]

        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    # Parse sitemap XML
                    soup = BeautifulSoup(response.text, 'xml')
                    urls = soup.find_all('url')
                    for url in urls:
                        loc = url.find('loc')
                        if loc and 'documentation' in loc.text:
                            self.discovered_links.add(loc.text)
                    print(f"[Discovery] Found sitemap with {len(urls)} URLs")
                    break
            except Exception as e:
                logger.debug(f"Sitemap exploration failed for {sitemap_url}: {e}")

    def _recursive_link_discovery(self):
        """Recursively discover links from main documentation pages."""
        seed_urls = [
            self.nrp_base,
            f"{self.nrp_base}userdocs/",
            f"{self.nrp_base}admindocs/",
            f"{self.nrp_base}tutorials/",
        ]

        for seed_url in seed_urls:
            try:
                response = requests.get(seed_url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find all internal links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(seed_url, href)

                        # Only include NRP documentation links
                        if (full_url.startswith('https://nrp.ai/documentation/') and
                            '#' not in full_url and  # Exclude anchors
                            '?' not in full_url):   # Exclude query params
                            self.discovered_links.add(full_url)

            except Exception as e:
                logger.debug(f"Recursive discovery failed for {seed_url}: {e}")

    def _validate_all_links(self):
        """Validate all discovered links and categorize them."""
        print(f"[Validation] Validating {len(self.discovered_links)} links...")

        valid_count = 0
        broken_count = 0

        for url in self.discovered_links:
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)

                if response.status_code == 200:
                    self.validated_links[url] = {
                        'status_code': response.status_code,
                        'content_type': response.headers.get('content-type', ''),
                        'last_modified': response.headers.get('last-modified', ''),
                        'final_url': response.url,
                        'is_redirect': url != response.url
                    }
                    valid_count += 1
                else:
                    self.broken_links.append({
                        'url': url,
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    })
                    broken_count += 1

            except Exception as e:
                self.broken_links.append({
                    'url': url,
                    'status_code': None,
                    'error': str(e)
                })
                broken_count += 1

            # Rate limiting
            time.sleep(0.1)

        print(f"[Validation] Valid: {valid_count}, Broken: {broken_count}")

    def _scrape_all_content(self):
        """Scrape content from all valid links."""
        print(f"[Scraping] Extracting content from {len(self.validated_links)} valid pages...")

        scraped_count = 0

        for url, link_info in self.validated_links.items():
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract comprehensive content
                    content_data = {
                        'url': url,
                        'title': self._extract_title(soup),
                        'headings': self._extract_headings(soup),
                        'paragraphs': self._extract_paragraphs(soup),
                        'code_blocks': self._extract_code_blocks(soup),
                        'yaml_blocks': self._extract_yaml_blocks(soup),
                        'warnings': self._extract_warnings(soup),
                        'links': self._extract_internal_links(soup, url),
                        'meta_keywords': self._extract_meta_keywords(soup),
                        'section_type': self._determine_section_type(url),
                        'content_category': self._categorize_content(soup.get_text()),
                        'last_scraped': datetime.now().isoformat(),
                        'word_count': len(soup.get_text().split()),
                        'has_yaml': len(self._extract_yaml_blocks(soup)) > 0,
                        'has_warnings': len(self._extract_warnings(soup)) > 0
                    }

                    self.content_database[url] = content_data
                    scraped_count += 1

            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")

            # Rate limiting
            time.sleep(0.2)

        print(f"[Scraping] Successfully scraped {scraped_count} pages")

    def _extract_comprehensive_keywords(self):
        """Extract and map keywords from all content."""
        print(f"[Keywords] Extracting keywords from {len(self.content_database)} pages...")

        for url, content in self.content_database.items():
            # Extract keywords from various sources
            all_text = f"{content['title']} {' '.join(content['headings'])} {' '.join(content['paragraphs'])}"

            # Technical keywords
            tech_keywords = self._extract_technical_keywords(all_text)
            for keyword in tech_keywords:
                self.keyword_mappings[keyword.lower()].add(url)

            # Command keywords
            for code_block in content['code_blocks']:
                command_keywords = self._extract_command_keywords(code_block)
                for keyword in command_keywords:
                    self.keyword_mappings[f"cmd_{keyword}"].add(url)

            # YAML resource keywords
            for yaml_block in content['yaml_blocks']:
                yaml_keywords = self._extract_yaml_keywords(yaml_block)
                for keyword in yaml_keywords:
                    self.keyword_mappings[f"yaml_{keyword}"].add(url)

            # Category keywords
            for category in content['content_category']:
                self.keyword_mappings[f"category_{category}"].add(url)

        print(f"[Keywords] Created {len(self.keyword_mappings)} keyword mappings")

    def _build_section_mappings(self):
        """Build hierarchical section mappings."""
        print(f"[Sections] Building section hierarchy...")

        for url in self.content_database.keys():
            path = urlparse(url).path
            path_parts = [p for p in path.split('/') if p]

            if len(path_parts) >= 2 and path_parts[0] == 'documentation':
                section_path = '/'.join(path_parts[1:])

                if section_path not in self.section_mappings:
                    self.section_mappings[section_path] = {
                        'urls': [],
                        'subsections': [],
                        'keywords': set(),
                        'content_types': set()
                    }

                self.section_mappings[section_path]['urls'].append(url)

                # Add content metadata
                content = self.content_database[url]
                self.section_mappings[section_path]['content_types'].update(content['content_category'])
                self.section_mappings[section_path]['keywords'].update(
                    self._extract_technical_keywords(content['title'])
                )

    def _save_comprehensive_data(self):
        """Save all collected data to files."""
        try:
            # Save links database
            with open(self.links_db_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'discovered_links': list(self.discovered_links),
                    'validated_links': self.validated_links,
                    'total_discovered': len(self.discovered_links),
                    'total_valid': len(self.validated_links),
                    'total_broken': len(self.broken_links)
                }, f, indent=2)

            # Save content database
            with open(self.content_db_file, 'w', encoding='utf-8') as f:
                # Convert sets to lists for JSON serialization
                serializable_content = {}
                for url, content in self.content_database.items():
                    serializable_content[url] = {**content}
                    if isinstance(content.get('content_category'), set):
                        serializable_content[url]['content_category'] = list(content['content_category'])

                json.dump(serializable_content, f, indent=2)

            # Save keyword mappings
            with open(self.keywords_db_file, 'w', encoding='utf-8') as f:
                keyword_data = {k: list(v) for k, v in self.keyword_mappings.items()}
                json.dump(keyword_data, f, indent=2)

            # Save broken links
            with open(self.broken_links_file, 'w', encoding='utf-8') as f:
                json.dump(self.broken_links, f, indent=2)

            print(f"[Save] All data saved to {self.cache_dir}")

        except Exception as e:
            logger.error(f"Failed to save comprehensive data: {e}")

    def _generate_scraping_report(self, start_time: float) -> Dict[str, Any]:
        """Generate comprehensive scraping report."""
        end_time = time.time()
        duration = end_time - start_time

        # Analyze content by category
        category_stats = defaultdict(int)
        section_stats = defaultdict(int)

        for content in self.content_database.values():
            for category in content['content_category']:
                category_stats[category] += 1
            section_stats[content['section_type']] += 1

        report = {
            'scraping_summary': {
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
                'duration_seconds': round(duration, 2),
                'total_links_discovered': len(self.discovered_links),
                'total_links_validated': len(self.validated_links),
                'total_broken_links': len(self.broken_links),
                'total_pages_scraped': len(self.content_database),
                'total_keywords_mapped': len(self.keyword_mappings)
            },
            'content_analysis': {
                'by_category': dict(category_stats),
                'by_section': dict(section_stats),
                'pages_with_yaml': sum(1 for c in self.content_database.values() if c['has_yaml']),
                'pages_with_warnings': sum(1 for c in self.content_database.values() if c['has_warnings']),
                'average_word_count': round(sum(c['word_count'] for c in self.content_database.values()) / len(self.content_database))
            },
            'link_health': {
                'broken_links': self.broken_links[:10],  # Top 10 broken links
                'redirect_count': sum(1 for l in self.validated_links.values() if l['is_redirect']),
                'health_percentage': round((len(self.validated_links) / len(self.discovered_links)) * 100, 2)
            },
            'keyword_coverage': {
                'top_keywords': sorted([(k, len(v)) for k, v in self.keyword_mappings.items()],
                                     key=lambda x: x[1], reverse=True)[:20],
                'category_coverage': {cat: len([k for k in self.keyword_mappings.keys() if any(word in k for word in words)])
                                    for cat, words in self.content_categories.items()}
            },
            'success': True
        }

        # Save report
        with open(self.scraping_report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return report

    # Helper extraction methods
    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""

    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        headings = []
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(level):
                headings.append(heading.get_text().strip())
        return headings

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if len(text) > 20:  # Filter out short paragraphs
                paragraphs.append(text)
        return paragraphs

    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[str]:
        code_blocks = []
        for code in soup.find_all(['pre', 'code']):
            text = code.get_text().strip()
            if len(text) > 10:
                code_blocks.append(text)
        return code_blocks

    def _extract_yaml_blocks(self, soup: BeautifulSoup) -> List[str]:
        yaml_blocks = []
        # NRP-specific YAML patterns
        for pre in soup.find_all('pre', attrs={'data-language': 'yaml'}):
            yaml_blocks.append(pre.get_text().strip())
        for code in soup.find_all('code', class_=re.compile(r'language-yaml', re.I)):
            yaml_blocks.append(code.get_text().strip())
        return yaml_blocks

    def _extract_warnings(self, soup: BeautifulSoup) -> List[str]:
        warnings = []
        # NRP-specific warning patterns
        for elem in soup.find_all(class_=re.compile(r'warning|caution|danger|note', re.I)):
            warnings.append(elem.get_text().strip())
        return warnings

    def _extract_internal_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            if full_url.startswith('https://nrp.ai/documentation/'):
                links.append(full_url)
        return links

    def _extract_meta_keywords(self, soup: BeautifulSoup) -> List[str]:
        keywords = []
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords['content'].split(',')]
        return keywords

    def _determine_section_type(self, url: str) -> str:
        path = urlparse(url).path.lower()
        if 'admindocs' in path:
            return 'admin'
        elif 'userdocs' in path:
            return 'user'
        elif 'tutorials' in path:
            return 'tutorial'
        elif 'examples' in path:
            return 'example'
        elif 'faq' in path:
            return 'faq'
        else:
            return 'general'

    def _categorize_content(self, text: str) -> Set[str]:
        categories = set()
        text_lower = text.lower()

        for category, keywords in self.content_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.add(category)

        return categories or {'general'}

    def _extract_technical_keywords(self, text: str) -> Set[str]:
        # Extract technical terms, commands, and important keywords
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b', text.lower())

        # Filter technical terms
        technical_terms = set()
        for word in words:
            if (word in ['kubernetes', 'docker', 'nvidia', 'gpu', 'cpu', 'memory', 'storage'] or
                word.startswith(('k8s', 'kubectl', 'helm', 'api', 'yaml', 'json')) or
                word.endswith(('gpu', 'cpu', 'api', 'cli'))):
                technical_terms.add(word)

        return technical_terms

    def _extract_command_keywords(self, code_block: str) -> Set[str]:
        # Extract command keywords from code blocks
        commands = set()
        lines = code_block.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith(('kubectl', 'docker', 'helm', 'git', 'pip', 'sudo')):
                commands.add(line.split()[0])

        return commands

    def _extract_yaml_keywords(self, yaml_block: str) -> Set[str]:
        # Extract YAML resource types and important fields
        keywords = set()
        lines = yaml_block.split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line:
                key = line.split(':')[0].strip()
                if key in ['apiVersion', 'kind', 'name', 'namespace', 'image', 'command']:
                    keywords.add(key)

        return keywords


def run_comprehensive_scraping():
    """Run the comprehensive NRP scraping."""
    scraper = ComprehensiveNRPScraper()
    return scraper.run_comprehensive_scraping()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run comprehensive scraping
    result = run_comprehensive_scraping()

    if result['success']:
        print(f"\n" + "="*60)
        print("COMPREHENSIVE SCRAPING COMPLETE")
        print("="*60)
        print(f"Duration: {result['scraping_summary']['duration_seconds']} seconds")
        print(f"Pages Scraped: {result['scraping_summary']['total_pages_scraped']}")
        print(f"Keywords Mapped: {result['scraping_summary']['total_keywords_mapped']}")
        print(f"Link Health: {result['link_health']['health_percentage']}%")
        print(f"\nTop Content Categories:")
        for category, count in list(result['content_analysis']['by_category'].items())[:5]:
            print(f"  {category}: {count} pages")
    else:
        print(f"Scraping failed: {result.get('error', 'Unknown error')}")