#!/usr/bin/env python3
"""
Ultimate NRP.ai Resources FastMCP Server
=======================================
Integrates comprehensive NRP.ai documentation crawler with FastMCP resources
providing access to ALL discovered NRP documentation pages including:
- /documentation/admindocs/cluster/fpga/
- /documentation/userdocs/storage/ceph-s3/
- And thousands of other discovered pages
"""

import os
import re
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse
from fastmcp import FastMCP

# Import our crawler
from nrp_crawler_and_indexer import NRPDocumentationCrawler

# Setup
logging = print  # Simple logging for now
STORAGE_DIR = Path(__file__).parent / "ultimate_nrp_resources"
STORAGE_DIR.mkdir(exist_ok=True)
CRAWLER_DB = Path(__file__).parent / "nrp_crawled_data" / "nrp_crawled_docs.db"

# Initialize FastMCP
mcp = FastMCP("Ultimate NRP.ai Resources Server")

class UltimateNRPResourcesManager:
    def __init__(self):
        self.crawler_db = CRAWLER_DB
        self.last_crawl_check = None

    def get_crawled_page(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a crawled page from the database by path"""
        if not self.crawler_db.exists():
            return None

        try:
            conn = sqlite3.connect(self.crawler_db)

            # Try exact path match first
            cursor = conn.execute("""
                SELECT url, title, content, content_length, yaml_blocks, keywords, crawled_at
                FROM crawled_pages WHERE path = ? OR url LIKE ?
                ORDER BY content_length DESC LIMIT 1
            """, (path, f"%{path}%"))

            row = cursor.fetchone()
            conn.close()

            if row:
                url, title, content, content_length, yaml_blocks, keywords, crawled_at = row

                # Parse stored data
                yaml_examples = json.loads(yaml_blocks or '[]')
                keyword_list = json.loads(keywords or '[]')

                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'content_length': content_length,
                    'yaml_examples': yaml_examples,
                    'yaml_count': len(yaml_examples),
                    'keywords': keyword_list,
                    'crawled_at': crawled_at,
                    'status': 'found_in_crawl'
                }

            return None

        except Exception as e:
            logging(f"Database error: {e}")
            return None

    def search_crawled_pages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search through all crawled pages"""
        if not self.crawler_db.exists():
            return []

        try:
            conn = sqlite3.connect(self.crawler_db)

            # Multi-field search
            cursor = conn.execute("""
                SELECT url, path, title, content_length, yaml_blocks, keywords, crawled_at
                FROM crawled_pages
                WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ? OR path LIKE ?
                ORDER BY content_length DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))

            results = []
            for row in cursor:
                url, path, title, content_length, yaml_blocks, keywords, crawled_at = row
                results.append({
                    'url': url,
                    'path': path,
                    'title': title,
                    'content_length': content_length,
                    'yaml_count': len(json.loads(yaml_blocks or '[]')),
                    'keywords': json.loads(keywords or '[]'),
                    'crawled_at': crawled_at,
                    'relevance': self.calculate_relevance(query, title, keywords)
                })

            conn.close()

            # Sort by relevance
            results.sort(key=lambda x: x['relevance'], reverse=True)
            return results

        except Exception as e:
            logging(f"Search error: {e}")
            return []

    def calculate_relevance(self, query: str, title: str, keywords: str) -> float:
        """Calculate search relevance score"""
        score = 0.0
        query_lower = query.lower()

        # Title match
        if query_lower in title.lower():
            score += 2.0

        # Keywords match
        try:
            keyword_list = json.loads(keywords or '[]')
            if any(query_lower in kw.lower() for kw in keyword_list):
                score += 1.0
        except:
            pass

        return score

    def get_crawl_statistics(self) -> Dict[str, Any]:
        """Get statistics from the crawled database"""
        if not self.crawler_db.exists():
            return {
                'error': 'No crawled database found',
                'suggestion': 'Run nrp_crawler_and_indexer.py first'
            }

        try:
            conn = sqlite3.connect(self.crawler_db)

            # Basic stats
            cursor = conn.execute("SELECT COUNT(*) FROM crawled_pages")
            total_pages = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM discovered_links")
            total_discovered = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM yaml_examples")
            total_yaml = cursor.fetchone()[0]

            # Pages by type/category
            cursor = conn.execute("""
                SELECT
                    CASE
                        WHEN path LIKE '%admindocs%' THEN 'admin'
                        WHEN path LIKE '%userdocs%' THEN 'user'
                        WHEN path LIKE '%tutorial%' THEN 'tutorial'
                        ELSE 'other'
                    END as category,
                    COUNT(*)
                FROM crawled_pages
                GROUP BY category
            """)
            pages_by_category = dict(cursor.fetchall())

            # Top keywords
            cursor = conn.execute("""
                SELECT keywords FROM crawled_pages WHERE keywords IS NOT NULL
            """)
            all_keywords = []
            for row in cursor:
                try:
                    keywords = json.loads(row[0] or '[]')
                    all_keywords.extend(keywords)
                except:
                    pass

            # Count keyword frequency
            keyword_counts = {}
            for kw in all_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            conn.close()

            return {
                'total_pages_crawled': total_pages,
                'total_links_discovered': total_discovered,
                'total_yaml_examples': total_yaml,
                'pages_by_category': pages_by_category,
                'top_keywords': dict(top_keywords),
                'database_path': str(self.crawler_db),
                'database_size_mb': round(self.crawler_db.stat().st_size / 1024 / 1024, 2)
            }

        except Exception as e:
            return {'error': str(e)}

# Initialize the manager
resource_manager = UltimateNRPResourcesManager()

# 1. STATIC RESOURCES
@mcp.resource("nrp://ultimate/info")
def get_ultimate_server_info() -> Dict[str, Any]:
    """Ultimate server information with crawl statistics"""
    stats = resource_manager.get_crawl_statistics()

    return {
        'name': 'Ultimate NRP.ai Resources Server',
        'version': '3.0.0',
        'description': 'Comprehensive access to ALL discovered NRP.ai documentation',
        'capabilities': [
            'crawled_documentation_access',
            'comprehensive_search',
            'dynamic_page_discovery',
            'yaml_extraction',
            'keyword_indexing',
            'multi_category_support'
        ],
        'crawl_statistics': stats,
        'supported_paths': [
            '/documentation/admindocs/cluster/fpga/',
            '/documentation/userdocs/storage/ceph-s3/',
            '/documentation/admindocs/storage/ceph-s3/',
            'And 4000+ more discovered pages'
        ],
        'last_updated': datetime.now().isoformat()
    }

@mcp.resource("nrp://crawled/stats")
def get_comprehensive_crawl_stats() -> Dict[str, Any]:
    """Detailed crawl statistics and database information"""
    return resource_manager.get_crawl_statistics()

# 2. DYNAMIC RESOURCES - Access ANY crawled page
@mcp.resource("nrp://crawled/{path}")
def get_any_crawled_page(path: str) -> Dict[str, Any]:
    """Access any crawled NRP.ai documentation page by path"""

    # Handle the path - ensure it starts with /
    if not path.startswith('/'):
        path = '/' + path

    # Get the page from crawled database
    page_data = resource_manager.get_crawled_page(path)

    if page_data:
        return {
            'path': path,
            'title': page_data['title'],
            'url': page_data['url'],
            'content_preview': page_data['content'][:1000] + '...' if len(page_data['content']) > 1000 else page_data['content'],
            'full_content_length': page_data['content_length'],
            'yaml_examples_count': page_data['yaml_count'],
            'yaml_examples': page_data['yaml_examples'][:3] if page_data['yaml_examples'] else [],
            'keywords': page_data['keywords'],
            'crawled_at': page_data['crawled_at'],
            'status': 'found',
            'source': 'crawled_database'
        }
    else:
        return {
            'path': path,
            'title': 'Page Not Found',
            'status': 'not_found',
            'suggestion': 'Try running the crawler to discover more pages',
            'available_similar': resource_manager.search_crawled_pages(path.split('/')[-1], 5)
        }

# 3. COMPREHENSIVE SEARCH
@mcp.resource("nrp://search/all/{query}")
def search_all_crawled_content(query: str) -> Dict[str, Any]:
    """Search across ALL crawled NRP.ai documentation"""

    results = resource_manager.search_crawled_pages(query, 50)

    # Categorize results
    admin_docs = [r for r in results if 'admindocs' in r['path']]
    user_docs = [r for r in results if 'userdocs' in r['path']]
    tutorials = [r for r in results if 'tutorial' in r['path']]
    other_docs = [r for r in results if r not in admin_docs + user_docs + tutorials]

    return {
        'query': query,
        'total_results': len(results),
        'results_by_category': {
            'admin_documentation': {
                'count': len(admin_docs),
                'results': admin_docs[:10]
            },
            'user_documentation': {
                'count': len(user_docs),
                'results': user_docs[:10]
            },
            'tutorials': {
                'count': len(tutorials),
                'results': tutorials[:10]
            },
            'other': {
                'count': len(other_docs),
                'results': other_docs[:10]
            }
        },
        'all_results': results[:20],  # Top 20 overall
        'search_performed_at': datetime.now().isoformat()
    }

# 4. SPECIFIC ACCESS RESOURCES for the requested pages
@mcp.resource("nrp://specific/fpga")
def get_fpga_documentation() -> Dict[str, Any]:
    """Direct access to FPGA documentation"""
    fpga_page = resource_manager.get_crawled_page('/documentation/admindocs/cluster/fpga/')

    if fpga_page:
        return {
            'title': fpga_page['title'],
            'url': fpga_page['url'],
            'content_length': fpga_page['content_length'],
            'keywords': fpga_page['keywords'],
            'summary': 'FPGA Flashing documentation for NRP Nautilus cluster administrators',
            'content_preview': fpga_page['content'][:2000],
            'yaml_examples': fpga_page['yaml_examples'],
            'related_pages': resource_manager.search_crawled_pages('fpga', 5)
        }
    else:
        return {'error': 'FPGA documentation not found in crawled data'}

@mcp.resource("nrp://specific/ceph-s3-user")
def get_ceph_s3_user_docs() -> Dict[str, Any]:
    """Direct access to user Ceph S3 documentation"""
    ceph_page = resource_manager.get_crawled_page('/documentation/userdocs/storage/ceph-s3/')

    if ceph_page:
        return {
            'title': ceph_page['title'],
            'url': ceph_page['url'],
            'content_length': ceph_page['content_length'],
            'keywords': ceph_page['keywords'],
            'summary': 'User guide for Ceph S3 storage on NRP Nautilus',
            'content_preview': ceph_page['content'][:2000],
            'yaml_examples': ceph_page['yaml_examples'],
            'related_pages': resource_manager.search_crawled_pages('ceph s3', 5)
        }
    else:
        return {'error': 'Ceph S3 user documentation not found in crawled data'}

@mcp.resource("nrp://specific/ceph-s3-admin")
def get_ceph_s3_admin_docs() -> Dict[str, Any]:
    """Direct access to admin Ceph S3 documentation"""
    ceph_page = resource_manager.get_crawled_page('/documentation/admindocs/storage/ceph-s3/')

    if ceph_page:
        return {
            'title': ceph_page['title'],
            'url': ceph_page['url'],
            'content_length': ceph_page['content_length'],
            'keywords': ceph_page['keywords'],
            'summary': 'Administrator guide for Ceph S3 storage management',
            'content_preview': ceph_page['content'][:2000],
            'yaml_examples': ceph_page['yaml_examples'],
            'related_pages': resource_manager.search_crawled_pages('ceph admin', 5)
        }
    else:
        return {'error': 'Ceph S3 admin documentation not found in crawled data'}

# 5. TOOLS for crawl management
@mcp.tool()
async def run_fresh_crawl(max_pages: int = 100) -> str:
    """Run a fresh crawl to discover new NRP.ai documentation"""
    try:
        crawler = NRPDocumentationCrawler(Path(__file__).parent / "nrp_crawled_data")

        start_urls = [
            "https://nrp.ai/documentation",
            "https://nrp.ai/documentation/admindocs/cluster/fpga/",
            "https://nrp.ai/documentation/userdocs/storage/ceph-s3/",
            "https://nrp.ai/documentation/admindocs/storage/ceph-s3/"
        ]

        results = await crawler.comprehensive_crawl(start_urls, max_depth=2, max_pages=max_pages)

        return f"Fresh crawl completed: {results['pages_crawled']} pages crawled, {results['pages_discovered']} links discovered, {results['yaml_blocks_found']} YAML blocks found"

    except Exception as e:
        return f"Crawl failed: {str(e)}"

@mcp.tool()
def search_crawled_docs(query: str, limit: int = 10) -> str:
    """Search through crawled documentation"""
    results = resource_manager.search_crawled_pages(query, limit)

    if results:
        response = f"Found {len(results)} results for '{query}':\\n"
        for i, result in enumerate(results[:limit], 1):
            response += f"{i}. {result['title']} ({result['content_length']} chars)\\n"
            response += f"   URL: {result['url']}\\n"
            response += f"   Keywords: {', '.join(result['keywords'][:5])}\\n\\n"
        return response
    else:
        return f"No results found for '{query}'"

if __name__ == "__main__":
    print("Starting Ultimate NRP.ai Resources FastMCP Server...")
    print(f"Crawler Database: {CRAWLER_DB}")
    print(f"Database exists: {CRAWLER_DB.exists()}")

    if CRAWLER_DB.exists():
        stats = resource_manager.get_crawl_statistics()
        print(f"Crawled pages available: {stats.get('total_pages_crawled', 0)}")
        print(f"Database size: {stats.get('database_size_mb', 0)} MB")
    else:
        print("Warning: No crawled database found. Run nrp_crawler_and_indexer.py first.")

    print()
    print("Available Resource Categories:")
    print("- nrp://ultimate/info - Server information")
    print("- nrp://crawled/stats - Crawl statistics")
    print("- nrp://crawled/{path} - Any crawled page by path")
    print("- nrp://search/all/{query} - Search all crawled content")
    print("- nrp://specific/fpga - FPGA documentation")
    print("- nrp://specific/ceph-s3-user - User Ceph S3 docs")
    print("- nrp://specific/ceph-s3-admin - Admin Ceph S3 docs")
    print()

    mcp.run(transport="http", port=8007)