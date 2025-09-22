#!/usr/bin/env python3
"""
NRP Comprehensive Documentation Scraper
=======================================
Infogent architecture to navigate, extract, aggregate, and store ALL NRP documentation anchors.
"""

import asyncio
import aiohttp
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path

class NRPDocumentationScraper:
    """Infogent for comprehensive NRP documentation scraping"""

    def __init__(self):
        self.base_url = "https://nrp.ai/documentation/"
        self.all_anchors = {}
        self.scraped_urls = set()
        self.failed_urls = set()

        # Known documentation structure from navigation
        self.known_pages = [
            # Start section
            "userdocs/start/getting-started/",
            "userdocs/start/using-nautilus/",
            "userdocs/start/hierarchical-resources/",
            "userdocs/start/policies/",
            "userdocs/start/deployed-services/",
            "userdocs/start/glossary/",
            "userdocs/start/faq/",
            "userdocs/start/support/",

            # Tutorial section
            "userdocs/tutorial/",
            "userdocs/tutorial/introduction/",
            "userdocs/tutorial/docker/",
            "userdocs/tutorial/basic/",
            "userdocs/tutorial/scaling/",
            "userdocs/tutorial/scheduling/",
            "userdocs/tutorial/jobs/",
            "userdocs/tutorial/images/",
            "userdocs/tutorial/storage/",
            "userdocs/tutorial/debugging/",
            "userdocs/tutorial/distributing-images/",
            "userdocs/tutorial/mnist/",

            # Running section
            "userdocs/running/",
            "userdocs/running/gpu-pods/",
            "userdocs/running/long-idle-pods/",
            "userdocs/running/monitoring/",
            "userdocs/running/client-scripts/",
            "userdocs/running/ingress/",
            "userdocs/running/special-use/",
            "userdocs/running/virtualization/",
            "userdocs/running/distributed-computing/",
            "userdocs/running/performance/",

            # Specialized sections
            "userdocs/jupyter/",
            "userdocs/coder/",
            "userdocs/ai-llms/",
            "userdocs/networks/",
            "userdocs/fpga/",
            "userdocs/storage/",
            "userdocs/development/",

            # Admin section
            "admindocs/participating/",
            "admindocs/perfsonar/",
            "admindocs/fiona/",
            "admindocs/nrp/",
            "admindocs/storage/",
            "admindocs/storage/broken-drives/",
            "admindocs/storage/user-pvc-issues/",
            "admindocs/vault/",
            "admindocs/links/",
            "admindocs/cluster-admin/",
        ]

    async def scrape_page_anchors(self, session, page_url):
        """Scrape anchors from a single page"""
        try:
            async with session.get(page_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.extract_anchors_from_html(html, page_url)
                else:
                    self.failed_urls.add(page_url)
                    return None
        except Exception as e:
            print(f"Failed to scrape {page_url}: {e}")
            self.failed_urls.add(page_url)
            return None

    def extract_anchors_from_html(self, html, page_url):
        """Extract all anchors from HTML content"""
        import re

        # Extract anchor IDs from the HTML
        anchor_patterns = [
            r'id="([^"]+)"',  # Standard id attributes
            r'href="#([^"]+)"',  # Internal links
            r'<h[1-6][^>]*id="([^"]+)"',  # Headers with IDs
        ]

        anchors = set()
        for pattern in anchor_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            anchors.update(matches)

        # Filter out non-useful anchors
        filtered_anchors = {
            anchor for anchor in anchors
            if anchor and not anchor.startswith('_') or anchor == '_top'
        }

        return {
            "url": page_url,
            "anchors": sorted(list(filtered_anchors)),
            "anchor_count": len(filtered_anchors)
        }

    async def scrape_all_documentation(self):
        """Comprehensive scraping of all NRP documentation"""
        print("[SCRAPER] Starting comprehensive NRP documentation scraping...")

        async with aiohttp.ClientSession() as session:
            tasks = []

            # Scrape all known pages
            for page_path in self.known_pages:
                full_url = urljoin(self.base_url, page_path)
                tasks.append(self.scrape_page_anchors(session, full_url))

            # Execute all scraping tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if result and not isinstance(result, Exception):
                    page_name = self.get_page_name(result["url"])
                    self.all_anchors[page_name] = result
                    print(f"[OK] {page_name}: {result['anchor_count']} anchors")
                    self.scraped_urls.add(result["url"])

        print(f"\n[SUMMARY] Scraping Summary:")
        print(f"   Successfully scraped: {len(self.scraped_urls)} pages")
        print(f"   Failed to scrape: {len(self.failed_urls)} pages")
        print(f"   Total unique anchors collected: {sum(data['anchor_count'] for data in self.all_anchors.values())}")

    def get_page_name(self, url):
        """Extract page name from URL"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) >= 2:
            return '_'.join(path_parts[-2:])
        return path_parts[-1] if path_parts else 'unknown'

    def save_anchors_database(self, output_file):
        """Save the complete anchors database"""
        output_path = Path(output_file)

        # Create comprehensive anchor database
        anchor_db = {
            "metadata": {
                "total_pages": len(self.all_anchors),
                "total_anchors": sum(data['anchor_count'] for data in self.all_anchors.values()),
                "failed_urls": list(self.failed_urls),
                "scraped_urls": list(self.scraped_urls)
            },
            "pages": self.all_anchors
        }

        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(anchor_db, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Anchor database saved to: {output_path}")
        return anchor_db

    def generate_python_knowledge_base(self, anchor_db, output_file):
        """Generate Python knowledge base from anchor database"""

        python_code = '''#!/usr/bin/env python3
"""
NRP Complete Anchor Database
===========================
Auto-generated comprehensive anchor database from ALL NRP documentation pages.
Generated using infogent architecture for navigation, extraction, aggregation, and storage.
"""

# Complete NRP Documentation Anchor Database
NRP_COMPLETE_ANCHORS = {
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
                section_name = anchor.replace('-', '_').replace('#', '')
                python_code += f'            "{section_name}": "#{anchor}",\n'

            python_code += '        }\n'
            python_code += '    },\n'

        python_code += '}\n\n'

        # Add utility functions
        python_code += '''
def get_all_anchor_urls():
    """Get all anchor URLs from complete database"""
    all_urls = {}
    for page_name, page_data in NRP_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        all_urls[page_name] = {}
        for section, anchor in page_data["sections"].items():
            all_urls[page_name][section] = f"{base_url}{anchor}"
    return all_urls

def find_anchor_by_keyword(keyword):
    """Find anchors containing specific keyword"""
    matches = []
    keyword_lower = keyword.lower()

    for page_name, page_data in NRP_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        for anchor in page_data["anchors"]:
            if keyword_lower in anchor.lower():
                matches.append({
                    "page": page_name,
                    "anchor": anchor,
                    "url": f"{base_url}#{anchor}"
                })
    return matches

def search_complete_anchors(query):
    """Comprehensive anchor search across all NRP documentation"""
    query_lower = query.lower()
    results = []

    # Search for keyword matches in anchors
    for page_name, page_data in NRP_COMPLETE_ANCHORS.items():
        base_url = page_data["base_url"]
        for anchor in page_data["anchors"]:
            if any(term in anchor.lower() for term in query_lower.split()):
                results.append({
                    "page": page_name,
                    "anchor": anchor,
                    "url": f"{base_url}#{anchor}",
                    "relevance": sum(1 for term in query_lower.split() if term in anchor.lower())
                })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:10]  # Return top 10 matches

# Statistics
TOTAL_PAGES = len(NRP_COMPLETE_ANCHORS)
TOTAL_ANCHORS = sum(len(page_data["anchors"]) for page_data in NRP_COMPLETE_ANCHORS.values())

print(f"NRP Complete Anchor Database loaded: {TOTAL_PAGES} pages, {TOTAL_ANCHORS} anchors")
'''

        # Save Python file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(python_code)

        print(f"[PYTHON] Python knowledge base generated: {output_file}")

async def main():
    """Run comprehensive NRP documentation scraping"""
    scraper = NRPDocumentationScraper()

    # Scrape all documentation
    await scraper.scrape_all_documentation()

    # Save results
    json_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_complete_anchors.json"
    python_file = "D:/Gsoc Gitlab/ocean/breakwater/mcp/cache/nrp_complete_anchor_db.py"

    anchor_db = scraper.save_anchors_database(json_file)
    scraper.generate_python_knowledge_base(anchor_db, python_file)

    print("[COMPLETE] Comprehensive NRP anchor scraping complete!")

if __name__ == "__main__":
    asyncio.run(main())