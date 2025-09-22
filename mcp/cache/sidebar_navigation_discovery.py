#!/usr/bin/env python3
"""
NRP Sidebar Navigation Discovery
================================
Comprehensively scrape and analyze ALL left sidebar navigation links
to ensure complete knowledge base coverage.
"""

import asyncio
import aiohttp
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re

class SidebarNavigationDiscovery:
    """Discover all sidebar navigation links from NRP documentation"""

    def __init__(self):
        self.base_url = "https://nrp.ai/documentation/"
        self.discovered_links = []
        self.organized_links = {}

    async def discover_all_sidebar_links(self):
        """Discover all navigation links from the sidebar"""
        print("[DISCOVERY] Starting comprehensive sidebar navigation discovery...")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        self.extract_sidebar_navigation(html)
                    else:
                        print(f"[ERROR] Failed to fetch main page: {response.status}")
            except Exception as e:
                print(f"[ERROR] Failed to discover sidebar links: {e}")

    def extract_sidebar_navigation(self, html):
        """Extract all navigation links from sidebar HTML"""
        print("[EXTRACT] Analyzing sidebar navigation structure...")

        # Look for sidebar navigation patterns
        nav_patterns = [
            r'href="(/documentation/[^"]+)"',  # Standard documentation links
            r'href="(https://nrp\.ai/documentation/[^"]+)"',  # Full URLs
        ]

        all_links = set()
        for pattern in nav_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    full_url = f"https://nrp.ai{match}"
                else:
                    full_url = match
                all_links.add(full_url)

        # Filter out non-documentation links and organize
        for link in all_links:
            if '/documentation/' in link and not link.endswith('/documentation/'):
                self.discovered_links.append(link)
                self.categorize_link(link)

        print(f"[FOUND] Discovered {len(self.discovered_links)} navigation links")

    def categorize_link(self, link):
        """Categorize links by section"""
        parsed = urlparse(link)
        path_parts = [p for p in parsed.path.split('/') if p]

        if len(path_parts) >= 3:
            doc_type = path_parts[1]  # userdocs or admindocs
            section = path_parts[2] if len(path_parts) > 2 else 'root'
            subsection = path_parts[3] if len(path_parts) > 3 else 'main'

            if doc_type not in self.organized_links:
                self.organized_links[doc_type] = {}
            if section not in self.organized_links[doc_type]:
                self.organized_links[doc_type][section] = []

            self.organized_links[doc_type][section].append({
                'url': link,
                'path': '/'.join(path_parts[2:]),
                'subsection': subsection
            })

    def compare_with_current_knowledge_base(self):
        """Compare discovered links with current knowledge base"""
        print("\n[COMPARE] Comparing with current knowledge base...")

        # Load current knowledge base
        try:
            json_path = Path("D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_complete_anchors.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                current_kb = json.load(f)

            current_urls = set(current_kb['metadata']['scraped_urls'])
            failed_urls = set(current_kb['metadata']['failed_urls'])

            print(f"[CURRENT] Knowledge base has {len(current_urls)} pages")
            print(f"[FAILED] {len(failed_urls)} pages previously failed")

            # Check coverage
            missing_pages = []
            covered_pages = []

            for link in self.discovered_links:
                if link in current_urls:
                    covered_pages.append(link)
                elif link in failed_urls:
                    print(f"[FAILED] {link}")
                else:
                    missing_pages.append(link)

            print(f"\n[COVERAGE] Analysis:")
            print(f"  • Covered: {len(covered_pages)}/{len(self.discovered_links)} pages")
            print(f"  • Missing: {len(missing_pages)} pages")
            print(f"  • Previously Failed: {len([l for l in self.discovered_links if l in failed_urls])} pages")

            if missing_pages:
                print(f"\n[MISSING] Pages not in knowledge base:")
                for page in missing_pages:
                    print(f"  - {page}")

            return {
                'discovered_total': len(self.discovered_links),
                'covered': len(covered_pages),
                'missing': missing_pages,
                'failed': [l for l in self.discovered_links if l in failed_urls]
            }

        except Exception as e:
            print(f"[ERROR] Could not load current knowledge base: {e}")
            return None

    def generate_comprehensive_page_list(self):
        """Generate complete page list for enhanced scraper"""
        print("\n[GENERATE] Creating comprehensive page list...")

        page_paths = []
        for link in self.discovered_links:
            parsed = urlparse(link)
            # Remove base and convert to relative path
            if parsed.path.startswith('/documentation/'):
                relative_path = parsed.path[len('/documentation/'):]
                if relative_path and not relative_path.endswith('/'):
                    relative_path += '/'
                page_paths.append(relative_path)

        # Sort and deduplicate
        page_paths = sorted(list(set(page_paths)))

        print(f"[PATHS] Generated {len(page_paths)} unique page paths")
        return page_paths

    def save_discovery_results(self, output_file):
        """Save discovery results to file"""
        results = {
            'discovery_metadata': {
                'total_discovered_links': len(self.discovered_links),
                'base_url': self.base_url,
                'organized_sections': len(self.organized_links)
            },
            'all_discovered_links': self.discovered_links,
            'organized_navigation': self.organized_links
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Discovery results saved to: {output_file}")
        return results

async def main():
    """Run comprehensive sidebar navigation discovery"""
    discovery = SidebarNavigationDiscovery()

    # Discover all sidebar links
    await discovery.discover_all_sidebar_links()

    # Compare with current knowledge base
    coverage_analysis = discovery.compare_with_current_knowledge_base()

    # Generate comprehensive page list
    comprehensive_paths = discovery.generate_comprehensive_page_list()

    # Save results
    results_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/sidebar_navigation_discovery.json"
    discovery_results = discovery.save_discovery_results(results_file)

    print(f"\n[COMPLETE] Sidebar navigation discovery complete!")
    print(f"[SUMMARY] Discovered {len(discovery.discovered_links)} total navigation links")

    if coverage_analysis:
        print(f"[COVERAGE] {coverage_analysis['covered']}/{coverage_analysis['discovered_total']} pages covered")
        if coverage_analysis['missing']:
            print(f"[ACTION] {len(coverage_analysis['missing'])} pages need to be added to knowledge base")

if __name__ == "__main__":
    asyncio.run(main())