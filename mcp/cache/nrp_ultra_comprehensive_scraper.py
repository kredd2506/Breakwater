#!/usr/bin/env python3
"""
NRP Ultra-Comprehensive Documentation Scraper
=============================================
Massive enhancement to capture ALL 131 sidebar navigation pages with complete anchor coverage.
This addresses the critical gap: only 19/131 pages (14.5%) currently covered.
"""

import asyncio
import aiohttp
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

class NRPUltraComprehensiveScraper:
    """Ultra-comprehensive scraper for complete NRP documentation coverage"""

    def __init__(self):
        self.base_url = "https://nrp.ai/documentation/"
        self.all_anchors = {}
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

    async def scrape_page_anchors(self, session, page_url):
        """Scrape anchors from a single page with enhanced error handling"""
        try:
            async with session.get(page_url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.extract_anchors_from_html(html, page_url)
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
        """Extract all anchors from HTML content with enhanced patterns"""
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
        filtered_anchors = set()
        for anchor in anchors:
            if anchor and len(anchor.strip()) > 0:
                # Keep most anchors, but filter out obviously useless ones
                if not anchor.startswith('_') or anchor == '_top':
                    if not anchor.startswith('footnote-') and not anchor.startswith('fn:'):
                        filtered_anchors.add(anchor.strip())

        return {
            "url": page_url,
            "anchors": sorted(list(filtered_anchors)),
            "anchor_count": len(filtered_anchors)
        }

    async def scrape_all_sidebar_pages(self):
        """Scrape ALL discovered sidebar navigation pages"""
        if not self.discovery_data:
            print("[ERROR] No sidebar discovery data available")
            return

        print(f"[ULTRA-SCRAPE] Starting comprehensive scraping of {len(self.discovery_data['all_discovered_links'])} pages...")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

        async def scrape_with_semaphore(session, url):
            async with semaphore:
                result = await self.scrape_page_anchors(session, url)
                if result:
                    await asyncio.sleep(0.1)  # Small delay between requests
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

            for result in asyncio.as_completed(tasks):
                try:
                    page_result = await result
                    completed += 1

                    if page_result:
                        page_name = self.get_page_name(page_result["url"])
                        self.all_anchors[page_name] = page_result
                        self.scraped_urls.add(page_result["url"])
                        print(f"[{completed:3d}/{total}] {page_name}: {page_result['anchor_count']} anchors")
                    else:
                        print(f"[{completed:3d}/{total}] FAILED")

                except Exception as e:
                    completed += 1
                    print(f"[{completed:3d}/{total}] ERROR: {e}")

        print(f"\n[ULTRA-SUMMARY] Scraping Results:")
        print(f"   Successfully scraped: {len(self.scraped_urls)} pages")
        print(f"   Failed to scrape: {len(self.failed_urls)} pages")
        print(f"   Total unique anchors: {sum(data['anchor_count'] for data in self.all_anchors.values())}")
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

    def save_ultra_comprehensive_database(self, output_file):
        """Save the ultra-comprehensive anchor database"""
        output_path = Path(output_file)

        # Create ultra-comprehensive anchor database
        anchor_db = {
            "metadata": {
                "total_pages": len(self.all_anchors),
                "total_anchors": sum(data['anchor_count'] for data in self.all_anchors.values()),
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
            json.dump(anchor_db, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Ultra-comprehensive database saved: {output_path}")
        return anchor_db

    def generate_ultra_python_knowledge_base(self, anchor_db, output_file):
        """Generate ultra-comprehensive Python knowledge base"""

        python_code = '''#!/usr/bin/env python3
"""
NRP Ultra-Comprehensive Anchor Database
======================================
Auto-generated ultra-comprehensive anchor database from ALL NRP sidebar navigation pages.
This represents complete coverage of the NRP documentation structure.

Generated using ultra-comprehensive infogent architecture for navigation,
extraction, aggregation, and storage of the complete documentation ecosystem.
"""

# Ultra-Comprehensive NRP Documentation Anchor Database
NRP_ULTRA_COMPLETE_ANCHORS = {
'''

        # Generate anchor mappings for each page
        for page_name, page_data in anchor_db["pages"].items():
            url = page_data["url"]
            anchors = page_data["anchors"]

            python_code += f'    "{page_name}": {{\n'
            python_code += f'        "base_url": "{url}",\n'
            python_code += f'        "anchors": {anchors},\n'
            python_code += f'        "sections": {{\n'

            for anchor in anchors:
                section_name = anchor.replace('-', '_').replace('#', '').replace('.', '_').replace(':', '_')
                # Ensure valid Python identifier
                if section_name and not section_name[0].isdigit():
                    python_code += f'            "{section_name}": "#{anchor}",\n'

            python_code += '        }\n'
            python_code += '    },\n'

        python_code += '}\n\n'

        # Add enhanced utility functions
        python_code += '''
def get_all_ultra_anchor_urls():
    """Get all anchor URLs from ultra-comprehensive database"""
    all_urls = {}
    for page_name, page_data in NRP_ULTRA_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        all_urls[page_name] = {}
        for section, anchor in page_data["sections"].items():
            all_urls[page_name][section] = f"{base_url}{anchor}"
    return all_urls

def find_ultra_anchor_by_keyword(keyword):
    """Find anchors containing specific keyword across all pages"""
    matches = []
    keyword_lower = keyword.lower()

    for page_name, page_data in NRP_ULTRA_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        for anchor in page_data["anchors"]:
            if keyword_lower in anchor.lower():
                matches.append({
                    "page": page_name,
                    "anchor": anchor,
                    "url": f"{base_url}#{anchor}"
                })
    return matches

def search_ultra_complete_anchors(query):
    """Ultra-comprehensive anchor search across ALL NRP documentation"""
    query_lower = query.lower()
    results = []

    # Search for keyword matches in anchors
    for page_name, page_data in NRP_ULTRA_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        page_relevance = 0

        # Check page URL for relevance
        if any(term in base_url.lower() for term in query_lower.split()):
            page_relevance += 2

        for anchor in page_data["anchors"]:
            anchor_relevance = 0
            for term in query_lower.split():
                if term in anchor.lower():
                    anchor_relevance += 1

            if anchor_relevance > 0:
                total_relevance = anchor_relevance + page_relevance
                results.append({
                    "page": page_name,
                    "anchor": anchor,
                    "url": f"{base_url}#{anchor}",
                    "relevance": total_relevance
                })

    # Sort by relevance and return top matches
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:15]  # Return top 15 matches for ultra-comprehensive coverage

# Ultra-Comprehensive Statistics
ULTRA_TOTAL_PAGES = len(NRP_ULTRA_COMPLETE_ANCHORS)
ULTRA_TOTAL_ANCHORS = sum(len(page_data["anchors"]) for page_data in NRP_ULTRA_COMPLETE_ANCHORS.values())

print(f"NRP Ultra-Comprehensive Anchor Database loaded: {ULTRA_TOTAL_PAGES} pages, {ULTRA_TOTAL_ANCHORS} anchors")
'''

        # Save Python file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(python_code)

        print(f"[PYTHON] Ultra-comprehensive Python knowledge base generated: {output_file}")

async def main():
    """Run ultra-comprehensive NRP documentation scraping"""
    scraper = NRPUltraComprehensiveScraper()

    # Scrape all sidebar navigation pages
    await scraper.scrape_all_sidebar_pages()

    # Save ultra-comprehensive results
    json_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_ultra_complete_anchors.json"
    python_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_ultra_complete_anchor_db.py"

    anchor_db = scraper.save_ultra_comprehensive_database(json_file)
    scraper.generate_ultra_python_knowledge_base(anchor_db, python_file)

    print(f"\n[ULTRA-COMPLETE] Ultra-comprehensive NRP documentation scraping complete!")
    print(f"[ACHIEVEMENT] Attempted to capture all {len(scraper.discovery_data['all_discovered_links']) if scraper.discovery_data else 0} sidebar navigation pages")

if __name__ == "__main__":
    asyncio.run(main())