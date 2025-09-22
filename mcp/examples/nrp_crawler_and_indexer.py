#!/usr/bin/env python3
"""
NRP.ai Documentation Crawler and Indexer
========================================
Comprehensive system to discover, crawl, and index ALL NRP.ai documentation
including deep nested paths like:
- /documentation/admindocs/cluster/fpga/
- /documentation/userdocs/storage/ceph-s3/
- And automatically discover new links
"""

import asyncio
import aiohttp
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time

class NRPDocumentationCrawler:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        self.db_path = storage_dir / "nrp_crawled_docs.db"
        self.visited_urls: Set[str] = set()
        self.discovered_links: Set[str] = set()
        self.base_url = "https://nrp.ai"
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize database
        self.init_database()

    def init_database(self):
        """Initialize comprehensive database for crawled documentation"""
        conn = sqlite3.connect(self.db_path)

        # Table for discovered and crawled pages
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL,
                title TEXT,
                content TEXT,
                content_length INTEGER,
                yaml_blocks TEXT,
                links_found TEXT,
                keywords TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                http_status INTEGER,
                content_type TEXT,
                depth_level INTEGER DEFAULT 0
            )
        """)

        # Table for discovered links not yet crawled
        conn.execute("""
            CREATE TABLE IF NOT EXISTS discovered_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source_url TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawled BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 0
            )
        """)

        # Table for YAML examples extracted
        conn.execute("""
            CREATE TABLE IF NOT EXISTS yaml_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                yaml_content TEXT NOT NULL,
                yaml_type TEXT,
                resource_kind TEXT,
                api_version TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for crawl statistics
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crawl_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_session_id TEXT NOT NULL,
                pages_discovered INTEGER DEFAULT 0,
                pages_crawled INTEGER DEFAULT 0,
                yaml_blocks_found INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                crawl_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawl_completed TIMESTAMP,
                status TEXT DEFAULT 'running'
            )
        """)

        conn.commit()
        conn.close()

    async def start_session(self):
        """Start aiohttp session"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'NRP Documentation Crawler/1.0'}
        )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def discover_links_from_page(self, url: str, content: str) -> List[str]:
        """Discover all NRP.ai documentation links from a page"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        # Find all links
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']

            # Convert relative URLs to absolute
            full_url = urljoin(url, href)

            # Filter for NRP.ai documentation links
            if (full_url.startswith('https://nrp.ai/documentation') or
                full_url.startswith('https://nrp.ai/guides') or
                full_url.startswith('https://nrp.ai/tutorials')):

                # Clean URL (remove fragments and query params for consistency)
                clean_url = full_url.split('#')[0].split('?')[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]

                links.append(clean_url)

        return list(set(links))  # Remove duplicates

    async def extract_yaml_content(self, content: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract YAML content blocks and analyze them"""
        yaml_examples = []

        # Multiple patterns for YAML detection
        patterns = [
            r'```ya?ml\s*([\s\S]*?)```',
            r'<pre[^>]*class="[^"]*yaml[^"]*"[^>]*>([\s\S]*?)</pre>',
            r'<code[^>]*class="[^"]*yaml[^"]*"[^>]*>([\s\S]*?)</code>',
            r'(apiVersion:\s*[\w/]+[\s\S]*?)(?=\n\s*(?:apiVersion|---|$))',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                yaml_content = match.strip()

                # Analyze YAML content
                yaml_info = {
                    'content': yaml_content,
                    'source_url': source_url,
                    'length': len(yaml_content),
                    'type': 'unknown',
                    'api_version': None,
                    'kind': None
                }

                # Extract Kubernetes resource info
                if 'apiVersion:' in yaml_content:
                    api_match = re.search(r'apiVersion:\s*(.+)', yaml_content)
                    if api_match:
                        yaml_info['api_version'] = api_match.group(1).strip()
                        yaml_info['type'] = 'kubernetes'

                if 'kind:' in yaml_content:
                    kind_match = re.search(r'kind:\s*(.+)', yaml_content)
                    if kind_match:
                        yaml_info['kind'] = kind_match.group(1).strip()

                # Detect other types
                if any(keyword in yaml_content.lower() for keyword in ['ceph', 's3', 'storage']):
                    yaml_info['type'] = 'storage'
                elif any(keyword in yaml_content.lower() for keyword in ['fpga', 'gpu', 'accelerator']):
                    yaml_info['type'] = 'hardware'
                elif any(keyword in yaml_content.lower() for keyword in ['network', 'ingress', 'service']):
                    yaml_info['type'] = 'networking'

                yaml_examples.append(yaml_info)

        return yaml_examples

    async def crawl_page(self, url: str, depth: int = 0) -> Optional[Dict[str, Any]]:
        """Crawl a single page and extract all relevant information"""
        if url in self.visited_urls or not self.session:
            return None

        try:
            print(f"Crawling (depth {depth}): {url}")
            async with self.session.get(url) as response:
                if response.status != 200:
                    print(f"  HTTP {response.status}: {url}")
                    return None

                content = await response.text()
                self.visited_urls.add(url)

                # Extract basic information
                soup = BeautifulSoup(content, 'html.parser')
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else "No title"

                # Extract path from URL
                path = urlparse(url).path

                # Discover links on this page
                discovered_links = await self.discover_links_from_page(url, content)
                self.discovered_links.update(discovered_links)

                # Extract YAML content
                yaml_examples = await self.extract_yaml_content(content, url)

                # Extract keywords
                keywords = self.extract_keywords(content, url)

                page_info = {
                    'url': url,
                    'path': path,
                    'title': title,
                    'content': content[:5000],  # Store first 5000 chars for search
                    'full_content': content,
                    'content_length': len(content),
                    'yaml_examples': yaml_examples,
                    'discovered_links': discovered_links,
                    'keywords': keywords,
                    'depth': depth,
                    'http_status': response.status,
                    'content_type': response.headers.get('content-type', 'unknown')
                }

                # Store in database
                await self.store_page_info(page_info)

                print(f"  SUCCESS: Crawled: {title} ({len(content)} chars, {len(yaml_examples)} YAML, {len(discovered_links)} links)")
                return page_info

        except Exception as e:
            print(f"  ERROR crawling {url}: {e}")
            return None

    def extract_keywords(self, content: str, url: str) -> List[str]:
        """Extract relevant keywords from content"""
        keywords = set()

        # URL-based keywords
        path_parts = urlparse(url).path.split('/')
        keywords.update([part for part in path_parts if part and len(part) > 2])

        # Content-based keywords
        text_content = BeautifulSoup(content, 'html.parser').get_text().lower()

        # Technical keywords
        tech_keywords = [
            'kubernetes', 'k8s', 'docker', 'container', 'pod', 'deployment', 'service',
            'ceph', 's3', 'storage', 'volume', 'pvc', 'pv',
            'fpga', 'gpu', 'nvidia', 'cuda', 'accelerator',
            'network', 'ingress', 'egress', 'firewall',
            'nautilus', 'nrp', 'cluster', 'node', 'namespace'
        ]

        for keyword in tech_keywords:
            if keyword in text_content:
                keywords.add(keyword)

        return list(keywords)

    async def store_page_info(self, page_info: Dict[str, Any]):
        """Store crawled page information in database"""
        conn = sqlite3.connect(self.db_path)

        try:
            # Store main page info
            conn.execute("""
                INSERT OR REPLACE INTO crawled_pages
                (url, path, title, content, content_length, yaml_blocks, links_found,
                 keywords, http_status, content_type, depth_level, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_info['url'],
                page_info['path'],
                page_info['title'],
                page_info['content'],
                page_info['content_length'],
                json.dumps([y['content'] for y in page_info['yaml_examples']]),
                json.dumps(page_info['discovered_links']),
                json.dumps(page_info['keywords']),
                page_info['http_status'],
                page_info['content_type'],
                page_info['depth'],
                datetime.now().isoformat()
            ))

            # Store YAML examples
            for yaml_example in page_info['yaml_examples']:
                conn.execute("""
                    INSERT OR REPLACE INTO yaml_examples
                    (source_url, yaml_content, yaml_type, resource_kind, api_version)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    page_info['url'],
                    yaml_example['content'],
                    yaml_example['type'],
                    yaml_example.get('kind'),
                    yaml_example.get('api_version')
                ))

            # Store discovered links
            for link in page_info['discovered_links']:
                conn.execute("""
                    INSERT OR IGNORE INTO discovered_links
                    (url, source_url, priority)
                    VALUES (?, ?, ?)
                """, (link, page_info['url'], page_info['depth'] + 1))

            conn.commit()

        except Exception as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    async def comprehensive_crawl(self, start_urls: List[str], max_depth: int = 3, max_pages: int = 100) -> Dict[str, Any]:
        """Perform comprehensive crawl of NRP.ai documentation"""
        crawl_session_id = f"crawl_{int(time.time())}"

        # Initialize crawl session
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO crawl_stats (crawl_session_id, status)
            VALUES (?, 'running')
        """, (crawl_session_id,))
        conn.commit()
        conn.close()

        await self.start_session()

        try:
            pages_crawled = 0
            pages_discovered = 0
            yaml_blocks_found = 0
            errors = 0

            # Start with seed URLs
            url_queue = [(url, 0) for url in start_urls]

            while url_queue and pages_crawled < max_pages:
                url, depth = url_queue.pop(0)

                if depth > max_depth or url in self.visited_urls:
                    continue

                page_info = await self.crawl_page(url, depth)

                if page_info:
                    pages_crawled += 1
                    yaml_blocks_found += len(page_info['yaml_examples'])

                    # Add discovered links to queue
                    for link in page_info['discovered_links']:
                        if link not in self.visited_urls:
                            url_queue.append((link, depth + 1))
                            pages_discovered += 1

                    # Rate limiting
                    await asyncio.sleep(0.5)
                else:
                    errors += 1

            # Update crawl statistics
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                UPDATE crawl_stats SET
                pages_discovered = ?, pages_crawled = ?, yaml_blocks_found = ?,
                errors_encountered = ?, crawl_completed = ?, status = 'completed'
                WHERE crawl_session_id = ?
            """, (pages_discovered, pages_crawled, yaml_blocks_found, errors,
                  datetime.now().isoformat(), crawl_session_id))
            conn.commit()
            conn.close()

            return {
                'session_id': crawl_session_id,
                'pages_crawled': pages_crawled,
                'pages_discovered': pages_discovered,
                'yaml_blocks_found': yaml_blocks_found,
                'errors': errors,
                'total_discovered_links': len(self.discovered_links)
            }

        finally:
            await self.close_session()

    def search_crawled_content(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search through crawled content"""
        conn = sqlite3.connect(self.db_path)

        # Search in multiple fields
        results = []

        # Title and content search
        cursor = conn.execute("""
            SELECT url, path, title, content_length, yaml_blocks, keywords, crawled_at
            FROM crawled_pages
            WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
            ORDER BY content_length DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))

        for row in cursor:
            url, path, title, content_length, yaml_blocks, keywords, crawled_at = row
            results.append({
                'url': url,
                'path': path,
                'title': title,
                'content_length': content_length,
                'yaml_blocks': len(json.loads(yaml_blocks or '[]')),
                'keywords': json.loads(keywords or '[]'),
                'crawled_at': crawled_at,
                'type': 'page'
            })

        # YAML content search
        cursor = conn.execute("""
            SELECT DISTINCT source_url, yaml_type, resource_kind, api_version, COUNT(*) as yaml_count
            FROM yaml_examples
            WHERE yaml_content LIKE ? OR yaml_type LIKE ? OR resource_kind LIKE ?
            GROUP BY source_url
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit // 2))

        for row in cursor:
            source_url, yaml_type, resource_kind, api_version, yaml_count = row
            results.append({
                'url': source_url,
                'yaml_type': yaml_type,
                'resource_kind': resource_kind,
                'api_version': api_version,
                'yaml_count': yaml_count,
                'type': 'yaml'
            })

        conn.close()
        return results

    def get_crawl_statistics(self) -> Dict[str, Any]:
        """Get comprehensive crawl statistics"""
        conn = sqlite3.connect(self.db_path)

        # Overall stats
        cursor = conn.execute("SELECT COUNT(*) FROM crawled_pages")
        total_pages = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM discovered_links WHERE crawled = 0")
        uncrawled_links = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM yaml_examples")
        total_yaml = cursor.fetchone()[0]

        # YAML by type
        cursor = conn.execute("""
            SELECT yaml_type, COUNT(*) FROM yaml_examples
            GROUP BY yaml_type ORDER BY COUNT(*) DESC
        """)
        yaml_by_type = dict(cursor.fetchall())

        # Recent crawl sessions
        cursor = conn.execute("""
            SELECT crawl_session_id, pages_crawled, yaml_blocks_found, status, crawl_started
            FROM crawl_stats ORDER BY crawl_started DESC LIMIT 5
        """)
        recent_crawls = [dict(zip([col[0] for col in cursor.description], row))
                        for row in cursor.fetchall()]

        conn.close()

        return {
            'total_pages_crawled': total_pages,
            'uncrawled_links_discovered': uncrawled_links,
            'total_yaml_examples': total_yaml,
            'yaml_by_type': yaml_by_type,
            'recent_crawl_sessions': recent_crawls,
            'database_path': str(self.db_path)
        }

async def main():
    """Test the crawler with specific NRP.ai pages"""
    storage_dir = Path(__file__).parent / "nrp_crawled_data"
    crawler = NRPDocumentationCrawler(storage_dir)

    # Test URLs including the ones mentioned
    start_urls = [
        "https://nrp.ai/documentation",
        "https://nrp.ai/documentation/admindocs/cluster/fpga/",
        "https://nrp.ai/documentation/userdocs/storage/ceph-s3/",
        "https://nrp.ai/documentation/admindocs/storage/ceph-s3/",
        "https://nrp.ai/guides"
    ]

    print("Starting comprehensive NRP.ai documentation crawl...")
    results = await crawler.comprehensive_crawl(start_urls, max_depth=2, max_pages=50)

    print(f"\nCrawl Results:")
    print(f"  Pages crawled: {results['pages_crawled']}")
    print(f"  Pages discovered: {results['pages_discovered']}")
    print(f"  YAML blocks found: {results['yaml_blocks_found']}")
    print(f"  Total links discovered: {results['total_discovered_links']}")

    # Test search functionality
    print(f"\nTesting search functionality:")
    search_queries = ["ceph", "s3", "fpga", "gpu", "storage"]

    for query in search_queries:
        results = crawler.search_crawled_content(query, 5)
        print(f"  Search '{query}': {len(results)} results")
        for result in results[:2]:
            title = result.get('title', 'No title')[:50]
            print(f"    - {title}... ({result['type']})")

    # Show statistics
    stats = crawler.get_crawl_statistics()
    print(f"\nCrawl Statistics:")
    print(f"  Total pages: {stats['total_pages_crawled']}")
    print(f"  YAML examples: {stats['total_yaml_examples']}")
    print(f"  YAML by type: {stats['yaml_by_type']}")

if __name__ == "__main__":
    asyncio.run(main())