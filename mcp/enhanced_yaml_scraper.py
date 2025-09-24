#!/usr/bin/env python3
"""
Enhanced YAML & A100 GPU Documentation Scraper
==============================================
Comprehensive scraper that extracts:
1. All navigation anchors from 131 sidebar pages
2. All YAML code examples with context
3. A100-specific GPU configurations
4. Template generation from extracted examples
"""

import asyncio
import aiohttp
import json
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
from bs4 import BeautifulSoup

class EnhancedYAMLScraper:
    """Enhanced scraper for complete YAML extraction and A100 configurations"""

    def __init__(self):
        self.base_url = "https://nrp.ai/documentation/"
        self.all_anchors = {}
        self.yaml_examples = {}
        self.a100_configs = {}
        self.scraped_urls = set()
        self.failed_urls = set()
        self.discovery_data = None

        # Load discovered sidebar navigation
        self.load_sidebar_discovery()

    def load_sidebar_discovery(self):
        """Load the discovered sidebar navigation data"""
        try:
            discovery_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/sidebar_navigation_discovery.json")
            with open(discovery_path, 'r', encoding='utf-8') as f:
                self.discovery_data = json.load(f)
            print(f"[LOADED] {len(self.discovery_data['all_discovered_links'])} sidebar pages to scrape")
        except Exception as e:
            print(f"[ERROR] Could not load sidebar discovery: {e}")
            self.discovery_data = None

    def extract_yaml_examples(self, html, page_url):
        """Extract YAML code examples from HTML content"""
        yaml_examples = []

        # Multiple patterns to catch YAML code blocks
        yaml_patterns = [
            r'```yaml\s*(.*?)\s*```',  # Standard YAML code blocks
            r'```yml\s*(.*?)\s*```',   # Alternative yml extension
            r'<pre[^>]*>\s*<code[^>]*yaml[^>]*>(.*?)</code>\s*</pre>',  # HTML code blocks
            r'<pre[^>]*class="[^"]*yaml[^"]*"[^>]*>(.*?)</pre>',  # Pre blocks with YAML class
            r'<code[^>]*class="[^"]*yaml[^"]*"[^>]*>(.*?)</code>',  # Code blocks with YAML class
        ]

        for pattern in yaml_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Clean the YAML content
                yaml_content = self.clean_yaml_content(match)
                if yaml_content and len(yaml_content.strip()) > 10:  # Filter out tiny snippets
                    yaml_examples.append({
                        'content': yaml_content,
                        'source_url': page_url,
                        'type': 'yaml_block'
                    })

        # Also try BeautifulSoup for more robust HTML parsing
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find code blocks
            code_blocks = soup.find_all(['pre', 'code'])
            for block in code_blocks:
                text = block.get_text()
                if self.looks_like_yaml(text):
                    cleaned = self.clean_yaml_content(text)
                    if cleaned and len(cleaned.strip()) > 10:
                        yaml_examples.append({
                            'content': cleaned,
                            'source_url': page_url,
                            'type': 'html_parsed'
                        })
        except Exception as e:
            print(f"[WARNING] BeautifulSoup parsing failed for {page_url}: {e}")

        return yaml_examples

    def clean_yaml_content(self, raw_content):
        """Clean and normalize YAML content"""
        # Remove HTML entities and tags
        cleaned = re.sub(r'&lt;', '<', raw_content)
        cleaned = re.sub(r'&gt;', '>', cleaned)
        cleaned = re.sub(r'&amp;', '&', cleaned)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)  # Remove any remaining HTML tags

        # Normalize whitespace while preserving YAML structure
        lines = cleaned.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove leading/trailing whitespace but preserve indentation structure
            if line.strip():
                cleaned_lines.append(line.rstrip())

        return '\n'.join(cleaned_lines).strip()

    def looks_like_yaml(self, text):
        """Heuristic to determine if text looks like YAML"""
        text = text.strip()
        if len(text) < 10:
            return False

        # Check for YAML indicators
        yaml_indicators = [
            'apiVersion:', 'kind:', 'metadata:', 'spec:',
            'resources:', 'limits:', 'requests:',
            'nvidia.com/', 'containers:', 'image:',
            'name:', 'namespace:', 'labels:'
        ]

        return any(indicator in text for indicator in yaml_indicators)

    def extract_a100_configurations(self, yaml_examples, page_url):
        """Extract A100-specific GPU configurations"""
        a100_configs = []

        for example in yaml_examples:
            content = example['content']

            # Look for A100-specific patterns
            a100_patterns = [
                r'nvidia\.com/a100[:\s]*\d+',  # nvidia.com/a100: 1
                r'a100[:\s]*\d+',             # a100: 1
                r'gpu[:\s]*a100',             # gpu: a100
                r'A100',                      # Direct A100 references
            ]

            has_a100 = any(re.search(pattern, content, re.IGNORECASE) for pattern in a100_patterns)

            if has_a100:
                a100_configs.append({
                    'yaml_content': content,
                    'source_url': page_url,
                    'detected_patterns': [pattern for pattern in a100_patterns
                                        if re.search(pattern, content, re.IGNORECASE)]
                })

        return a100_configs

    async def scrape_page_comprehensive(self, session, page_url):
        """Comprehensive scraping of a single page for anchors, YAML, and A100 configs"""
        try:
            async with session.get(page_url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()

                    # Extract anchors
                    anchors = self.extract_anchors_from_html(html, page_url)

                    # Extract YAML examples
                    yaml_examples = self.extract_yaml_examples(html, page_url)

                    # Extract A100 configurations
                    a100_configs = self.extract_a100_configurations(yaml_examples, page_url)

                    return {
                        'url': page_url,
                        'anchors': anchors,
                        'yaml_examples': yaml_examples,
                        'a100_configs': a100_configs,
                        'yaml_count': len(yaml_examples),
                        'a100_count': len(a100_configs)
                    }
                else:
                    print(f"[HTTP {response.status}] {page_url}")
                    self.failed_urls.add(page_url)
                    return None
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] {page_url}")
            self.failed_urls.add(page_url)
            return None
        except Exception as e:
            print(f"[ERROR] {page_url}: {str(e)[:100]}")
            self.failed_urls.add(page_url)
            return None

    def extract_anchors_from_html(self, html, page_url):
        """Extract all anchors from HTML content"""
        import re

        # Enhanced anchor extraction patterns
        anchor_patterns = [
            r'id=\"([^\"]+)\"',  # Standard id attributes
            r'href=\"#([^\"]+)\"',  # Internal links
            r'<h[1-6][^>]*id=\"([^\"]+)\"',  # Headers with IDs
            r'<a[^>]*name=\"([^\"]+)\"',  # Named anchors
            r'<[^>]*data-anchor=\"([^\"]+)\"',  # Data anchors
        ]

        anchors = set()
        for pattern in anchor_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            anchors.update(matches)

        # Enhanced filtering for useful anchors
        filtered_anchors = []
        for anchor in anchors:
            if anchor and len(anchor.strip()) > 0:
                # Keep most anchors, but filter out obviously useless ones
                if not anchor.startswith('_') or anchor == '_top':
                    if not anchor.startswith('footnote-') and not anchor.startswith('fn:'):
                        filtered_anchors.append(anchor.strip())

        return sorted(filtered_anchors)

    async def scrape_all_comprehensive(self):
        """Comprehensive scraping of ALL sidebar pages for anchors, YAML, and A100"""
        if not self.discovery_data:
            print("[ERROR] No sidebar discovery data available")
            return

        print(f"[COMPREHENSIVE] Starting enhanced scraping of {len(self.discovery_data['all_discovered_links'])} pages...")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(8)  # Limit to 8 concurrent requests

        async def scrape_with_semaphore(session, url):
            async with semaphore:
                result = await self.scrape_page_comprehensive(session, url)
                if result:
                    await asyncio.sleep(0.2)  # Small delay between requests
                return result

        async with aiohttp.ClientSession() as session:
            # Create tasks for all discovered URLs
            tasks = [
                scrape_with_semaphore(session, url)
                for url in self.discovery_data['all_discovered_links']
            ]

            # Execute all scraping tasks with progress tracking
            completed = 0
            total = len(tasks)
            total_yaml = 0
            total_a100 = 0

            for result in asyncio.as_completed(tasks):
                try:
                    page_result = await result
                    completed += 1

                    if page_result:
                        page_name = self.get_page_name(page_result["url"])
                        self.all_anchors[page_name] = page_result
                        self.scraped_urls.add(page_result["url"])

                        yaml_count = page_result['yaml_count']
                        a100_count = page_result['a100_count']
                        total_yaml += yaml_count
                        total_a100 += a100_count

                        status = f"anchors:{len(page_result['anchors'])}, yaml:{yaml_count}, a100:{a100_count}"
                        print(f"[{completed:3d}/{total}] {page_name}: {status}")
                    else:
                        print(f"[{completed:3d}/{total}] FAILED")

                except Exception as e:
                    completed += 1
                    print(f"[{completed:3d}/{total}] ERROR: {e}")

        print(f"\n[COMPREHENSIVE SUMMARY] Enhanced Scraping Results:")
        print(f"   Successfully scraped: {len(self.scraped_urls)} pages")
        print(f"   Failed to scrape: {len(self.failed_urls)} pages")
        print(f"   Total unique anchors: {sum(len(data['anchors']) for data in self.all_anchors.values())}")
        print(f"   Total YAML examples: {total_yaml}")
        print(f"   Total A100 configs: {total_a100}")
        print(f"   Coverage achieved: {len(self.scraped_urls)}/{len(self.discovery_data['all_discovered_links'])} ({(len(self.scraped_urls)/len(self.discovery_data['all_discovered_links']))*100:.1f}%)")

    def get_page_name(self, url):
        """Generate consistent page names from URLs"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p and p != 'documentation']

        if len(path_parts) >= 2:
            # Create hierarchical name: section_subsection_page
            if len(path_parts) >= 3:
                return f"{path_parts[1]}_{path_parts[2].replace('-', '_')}"
            else:
                return f"{path_parts[1]}_main"
        return 'unknown'

    def save_comprehensive_database(self, output_file):
        """Save the comprehensive database with YAML and A100 configs"""
        output_path = Path(output_file)

        # Create comprehensive database
        comprehensive_db = {
            "metadata": {
                "total_pages": len(self.all_anchors),
                "total_anchors": sum(len(data['anchors']) for data in self.all_anchors.values()),
                "total_yaml_examples": sum(data['yaml_count'] for data in self.all_anchors.values()),
                "total_a100_configs": sum(data['a100_count'] for data in self.all_anchors.values()),
                "failed_urls": list(self.failed_urls),
                "scraped_urls": list(self.scraped_urls),
                "discovery_total": len(self.discovery_data['all_discovered_links']) if self.discovery_data else 0,
                "coverage_percentage": (len(self.scraped_urls)/len(self.discovery_data['all_discovered_links']))*100 if self.discovery_data else 0,
                "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "pages": self.all_anchors
        }

        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_db, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Comprehensive database saved: {output_path}")
        return comprehensive_db

    def generate_a100_template_fixes(self, comprehensive_db):
        """Generate proper A100 template fixes based on scraped data"""
        a100_templates = {}

        # Collect all A100 configurations
        for page_name, page_data in comprehensive_db["pages"].items():
            if page_data.get('a100_configs'):
                for config in page_data['a100_configs']:
                    # Extract and fix the YAML content
                    yaml_content = config['yaml_content']

                    # Fix generic nvidia.com/gpu to nvidia.com/a100
                    fixed_yaml = re.sub(
                        r'nvidia\.com/gpu:',
                        'nvidia.com/a100:',
                        yaml_content
                    )

                    # Also handle different formatting variations
                    fixed_yaml = re.sub(
                        r'nvidia\.com/gpu\s*:\s*(\d+)',
                        r'nvidia.com/a100: \1',
                        fixed_yaml
                    )

                    template_name = f"a100_config_{len(a100_templates) + 1}"
                    a100_templates[template_name] = {
                        'original_yaml': yaml_content,
                        'fixed_yaml': fixed_yaml,
                        'source_page': page_name,
                        'source_url': config['source_url'],
                        'detected_patterns': config['detected_patterns']
                    }

        return a100_templates

async def main():
    """Run enhanced comprehensive NRP documentation scraping"""
    scraper = EnhancedYAMLScraper()

    # Scrape all sidebar navigation pages comprehensively
    await scraper.scrape_all_comprehensive()

    # Save comprehensive results
    json_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/enhanced_comprehensive_scrape.json"
    comprehensive_db = scraper.save_comprehensive_database(json_file)

    # Generate A100 template fixes
    a100_fixes = scraper.generate_a100_template_fixes(comprehensive_db)

    a100_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/a100_template_fixes.json"
    with open(a100_file, 'w', encoding='utf-8') as f:
        json.dump(a100_fixes, f, indent=2, ensure_ascii=False)

    print(f"\n[ENHANCED COMPLETE] Comprehensive scraping with YAML and A100 extraction complete!")
    print(f"[YAML EXTRACTED] Found {sum(data['yaml_count'] for data in comprehensive_db['pages'].values())} YAML examples")
    print(f"[A100 CONFIGS] Found {len(a100_fixes)} A100 configurations")
    print(f"[TEMPLATES] A100 template fixes saved to: {a100_file}")

if __name__ == "__main__":
    asyncio.run(main())