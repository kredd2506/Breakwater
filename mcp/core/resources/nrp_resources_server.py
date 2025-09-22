#!/usr/bin/env python3
"""
NRP.ai Resources FastMCP Server
==============================
Comprehensive resource system based on NRP.ai documentation providing:
- Static and dynamic resource generation
- Data source exposure for MCP clients
- Template-based resource creation
- Real-time content generation from NRP.ai
"""

import os
import re
import sys
import yaml
import json
import asyncio
import aiohttp
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from fastmcp import FastMCP
import logging

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize storage and cache
STORAGE_DIR = Path(__file__).parent / "nrp_resources"
STORAGE_DIR.mkdir(exist_ok=True)
CACHE_DB = STORAGE_DIR / "nrp_cache.db"

def init_resource_database():
    """Initialize SQLite database for resource caching"""
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nrp_documentation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            yaml_resources TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS k8s_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            template_type TEXT NOT NULL,
            yaml_content TEXT NOT NULL,
            description TEXT,
            parameters TEXT,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resource_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            content_type TEXT DEFAULT 'text/plain',
            expires_at TIMESTAMP,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

init_resource_database()

# NRP.ai Documentation Scraper
class NRPDocumentationScraper:
    """Scraper for NRP.ai documentation with intelligent parsing"""

    BASE_URL = "https://nrp.ai"

    @staticmethod
    async def scrape_documentation_section(path: str) -> Dict[str, Any]:
        """Scrape a specific documentation section"""
        try:
            full_url = f"{NRPDocumentationScraper.BASE_URL}{path}"

            async with aiohttp.ClientSession() as session:
                async with session.get(full_url) as response:
                    content = await response.text()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else path

            # Extract main content
            content_selectors = [
                'article', '.content', '.documentation', 'main',
                '.doc-content', '#content', '.markdown-body'
            ]

            main_content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove navigation and sidebar elements
                    for nav in content_elem.select('nav, .nav, .sidebar, .toc'):
                        nav.decompose()
                    main_content = content_elem.get_text(separator='\n', strip=True)
                    break

            if not main_content:
                # Fallback to body content
                for script in soup(["script", "style"]):
                    script.decompose()
                main_content = soup.get_text(separator='\n', strip=True)

            # Extract YAML blocks
            yaml_pattern = r'```ya?ml\n(.*?)\n```'
            yaml_matches = re.findall(yaml_pattern, content, re.DOTALL | re.IGNORECASE)

            # Extract code blocks
            code_pattern = r'```(\w+)?\n(.*?)\n```'
            code_matches = re.findall(code_pattern, content, re.DOTALL | re.IGNORECASE)

            # Extract links to other documentation
            doc_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/') and any(keyword in href for keyword in ['doc', 'guide', 'tutorial']):
                    doc_links.append(href)

            return {
                "url": full_url,
                "path": path,
                "title": title_text,
                "content": main_content,
                "yaml_blocks": yaml_matches,
                "code_blocks": code_matches,
                "doc_links": doc_links[:10],  # Limit links
                "scraped_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error scraping NRP documentation {path}: {e}")
            return {
                "url": f"{NRPDocumentationScraper.BASE_URL}{path}",
                "path": path,
                "title": f"Error loading {path}",
                "content": f"Failed to load content: {str(e)}",
                "yaml_blocks": [],
                "code_blocks": [],
                "doc_links": [],
                "scraped_at": datetime.now().isoformat(),
                "error": str(e)
            }

    @staticmethod
    def store_documentation(doc_data: Dict[str, Any]) -> int:
        """Store documentation in database"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO nrp_documentation
                (path, title, content, yaml_resources, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                doc_data["path"],
                doc_data["title"],
                doc_data["content"],
                json.dumps(doc_data["yaml_blocks"]),
                json.dumps({
                    "code_blocks": doc_data["code_blocks"],
                    "doc_links": doc_data["doc_links"],
                    "scraped_at": doc_data["scraped_at"],
                    "url": doc_data["url"]
                })
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

# K8s Template Generator
class K8sTemplateGenerator:
    """Generate Kubernetes templates from NRP.ai documentation"""

    @staticmethod
    def extract_k8s_templates(yaml_blocks: List[str]) -> List[Dict[str, Any]]:
        """Extract K8s templates from YAML blocks"""
        templates = []

        for i, yaml_content in enumerate(yaml_blocks):
            try:
                yaml_data = yaml.safe_load(yaml_content)

                if isinstance(yaml_data, dict) and 'kind' in yaml_data:
                    template = {
                        "name": yaml_data.get('metadata', {}).get('name', f'template-{i}'),
                        "template_type": yaml_data.get('kind', 'Unknown'),
                        "yaml_content": yaml_content,
                        "description": f"K8s {yaml_data.get('kind')} template extracted from NRP.ai",
                        "parameters": K8sTemplateGenerator._extract_parameters(yaml_content),
                        "api_version": yaml_data.get('apiVersion', ''),
                        "namespace": yaml_data.get('metadata', {}).get('namespace', 'default')
                    }
                    templates.append(template)

            except yaml.YAMLError as e:
                logger.warning(f"Invalid YAML in block {i}: {e}")
                continue

        return templates

    @staticmethod
    def _extract_parameters(yaml_content: str) -> List[str]:
        """Extract parameterizable fields from YAML"""
        # Look for common template patterns
        parameter_patterns = [
            r'\{\{\.(\w+)\}\}',  # Helm-style templates
            r'\$\{(\w+)\}',      # Environment variable style
            r'<(\w+)>',          # Placeholder style
        ]

        parameters = set()
        for pattern in parameter_patterns:
            matches = re.findall(pattern, yaml_content)
            parameters.update(matches)

        return list(parameters)

    @staticmethod
    def store_template(template: Dict[str, Any], source_url: str = None) -> int:
        """Store K8s template in database"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO k8s_templates
                (name, template_type, yaml_content, description, parameters, source_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template["name"],
                template["template_type"],
                template["yaml_content"],
                template["description"],
                json.dumps(template["parameters"]),
                source_url
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

# Resource Cache Manager
class ResourceCacheManager:
    """Manage resource caching with TTL"""

    @staticmethod
    def get_cached_resource(uri: str) -> Optional[Dict[str, Any]]:
        """Get cached resource if not expired"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                SELECT content, content_type, expires_at, metadata
                FROM resource_cache
                WHERE uri = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            """, (uri,))

            row = cursor.fetchone()
            if row:
                return {
                    "content": row[0],
                    "content_type": row[1],
                    "expires_at": row[2],
                    "metadata": json.loads(row[3] or '{}')
                }
        finally:
            conn.close()
        return None

    @staticmethod
    def cache_resource(uri: str, content: str, content_type: str = 'text/plain',
                      ttl_seconds: int = 3600, metadata: Dict = None) -> None:
        """Cache resource with TTL"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        conn = sqlite3.connect(CACHE_DB)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO resource_cache
                (uri, content, content_type, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (uri, content, content_type, expires_at.isoformat(),
                  json.dumps(metadata or {})))
            conn.commit()
        finally:
            conn.close()

# Create the FastMCP server
mcp = FastMCP(
    name="NRP.ai Resources Server",
    instructions="""
    Advanced NRP.ai documentation resource server providing:
    - Dynamic documentation fetching from NRP.ai
    - Kubernetes template generation and management
    - Real-time content caching and delivery
    - Template-based resource creation with parameters
    """
)

# ======================== STATIC RESOURCES ========================

@mcp.resource("nrp://status")
def get_server_status() -> Dict[str, Any]:
    """Get current server status and capabilities"""
    conn = sqlite3.connect(CACHE_DB)
    try:
        # Count cached documentation
        doc_count = conn.execute("SELECT COUNT(*) FROM nrp_documentation").fetchone()[0]
        template_count = conn.execute("SELECT COUNT(*) FROM k8s_templates").fetchone()[0]
        cache_count = conn.execute("SELECT COUNT(*) FROM resource_cache WHERE expires_at > datetime('now')").fetchone()[0]

        return {
            "server_name": "NRP.ai Resources Server",
            "status": "operational",
            "capabilities": [
                "Dynamic NRP.ai documentation fetching",
                "Kubernetes template extraction and management",
                "Resource caching with TTL",
                "Template-based resource generation",
                "Real-time content delivery"
            ],
            "statistics": {
                "cached_documentation_pages": doc_count,
                "k8s_templates": template_count,
                "active_cache_entries": cache_count
            },
            "resource_types": {
                "static": ["nrp://status", "nrp://docs/index", "nrp://templates/index"],
                "dynamic": [
                    "nrp://docs/{path}",
                    "nrp://templates/{name}",
                    "nrp://k8s/template/{type}",
                    "nrp://cache/stats"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    finally:
        conn.close()

@mcp.resource("nrp://docs/index")
def get_documentation_index() -> Dict[str, Any]:
    """Get index of all cached documentation"""
    conn = sqlite3.connect(CACHE_DB)
    try:
        cursor = conn.execute("""
            SELECT path, title, last_updated
            FROM nrp_documentation
            ORDER BY last_updated DESC
        """)

        docs = []
        for row in cursor.fetchall():
            docs.append({
                "path": row[0],
                "title": row[1],
                "last_updated": row[2],
                "resource_uri": f"nrp://docs{row[0]}"
            })

        return {
            "title": "NRP.ai Documentation Index",
            "total_documents": len(docs),
            "documents": docs,
            "last_updated": datetime.now().isoformat()
        }
    finally:
        conn.close()

@mcp.resource("nrp://templates/index")
def get_templates_index() -> Dict[str, Any]:
    """Get index of all Kubernetes templates"""
    conn = sqlite3.connect(CACHE_DB)
    try:
        cursor = conn.execute("""
            SELECT name, template_type, description, created_at
            FROM k8s_templates
            ORDER BY created_at DESC
        """)

        templates = []
        for row in cursor.fetchall():
            templates.append({
                "name": row[0],
                "type": row[1],
                "description": row[2],
                "created_at": row[3],
                "resource_uri": f"nrp://templates/{row[0]}"
            })

        return {
            "title": "Kubernetes Templates Index",
            "total_templates": len(templates),
            "templates": templates,
            "template_types": list(set(t["type"] for t in templates)),
            "last_updated": datetime.now().isoformat()
        }
    finally:
        conn.close()

# ======================== DYNAMIC RESOURCES ========================

@mcp.resource("nrp://docs/{path}")
async def get_documentation_page(path: str) -> Union[Dict[str, Any], str]:
    """
    Get specific documentation page from NRP.ai with caching.

    Args:
        path: Documentation path (e.g., "/documentation/getting-started")
    """
    full_path = f"/{path}" if not path.startswith('/') else path
    cache_uri = f"nrp://docs{full_path}"

    # Check cache first
    cached = ResourceCacheManager.get_cached_resource(cache_uri)
    if cached:
        return json.loads(cached["content"])

    # Fetch from NRP.ai
    doc_data = await NRPDocumentationScraper.scrape_documentation_section(full_path)

    # Store in database
    NRPDocumentationScraper.store_documentation(doc_data)

    # Extract and store K8s templates
    if doc_data["yaml_blocks"]:
        templates = K8sTemplateGenerator.extract_k8s_templates(doc_data["yaml_blocks"])
        for template in templates:
            K8sTemplateGenerator.store_template(template, doc_data["url"])

    # Cache the result
    result = {
        "path": full_path,
        "title": doc_data["title"],
        "content": doc_data["content"],
        "yaml_resources": len(doc_data["yaml_blocks"]),
        "code_blocks": len(doc_data["code_blocks"]),
        "related_links": doc_data["doc_links"],
        "source_url": doc_data["url"],
        "cached_at": datetime.now().isoformat()
    }

    ResourceCacheManager.cache_resource(
        cache_uri,
        json.dumps(result),
        'application/json',
        ttl_seconds=1800  # 30 minutes
    )

    return result

@mcp.resource("nrp://templates/{name}")
def get_template_by_name(name: str) -> Union[Dict[str, Any], str]:
    """
    Get specific Kubernetes template by name.

    Args:
        name: Template name
    """
    conn = sqlite3.connect(CACHE_DB)
    try:
        cursor = conn.execute("""
            SELECT name, template_type, yaml_content, description, parameters, source_url, created_at
            FROM k8s_templates
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        if not row:
            return f"Template '{name}' not found"

        return {
            "name": row[0],
            "type": row[1],
            "yaml_content": row[2],
            "description": row[3],
            "parameters": json.loads(row[4] or '[]'),
            "source_url": row[5],
            "created_at": row[6],
            "usage_example": f"kubectl apply -f <(echo '{row[2]}')",
            "parameter_substitution": "Replace template variables with actual values before applying"
        }
    finally:
        conn.close()

@mcp.resource("nrp://k8s/template/{template_type}")
def get_templates_by_type(template_type: str) -> Dict[str, Any]:
    """
    Get all templates of a specific Kubernetes resource type.

    Args:
        template_type: K8s resource type (Pod, Deployment, Service, etc.)
    """
    conn = sqlite3.connect(CACHE_DB)
    try:
        cursor = conn.execute("""
            SELECT name, yaml_content, description, parameters, source_url
            FROM k8s_templates
            WHERE LOWER(template_type) = LOWER(?)
            ORDER BY name
        """, (template_type,))

        templates = []
        for row in cursor.fetchall():
            templates.append({
                "name": row[0],
                "yaml_content": row[1],
                "description": row[2],
                "parameters": json.loads(row[3] or '[]'),
                "source_url": row[4]
            })

        return {
            "template_type": template_type,
            "total_templates": len(templates),
            "templates": templates,
            "usage_instructions": f"Templates for {template_type} resources from NRP.ai documentation"
        }
    finally:
        conn.close()

@mcp.resource("nrp://cache/stats")
def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics and performance metrics"""
    conn = sqlite3.connect(CACHE_DB)
    try:
        # Documentation statistics
        doc_stats = conn.execute("""
            SELECT COUNT(*), SUM(LENGTH(content)), MAX(last_updated)
            FROM nrp_documentation
        """).fetchone()

        # Template statistics by type
        template_stats = conn.execute("""
            SELECT template_type, COUNT(*)
            FROM k8s_templates
            GROUP BY template_type
        """).fetchall()

        # Cache performance
        cache_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as active,
                COUNT(CASE WHEN expires_at <= datetime('now') THEN 1 END) as expired
            FROM resource_cache
        """).fetchone()

        # Recent activity
        recent_docs = conn.execute("""
            SELECT COUNT(*) FROM nrp_documentation
            WHERE last_updated > datetime('now', '-1 hour')
        """).fetchone()[0]

        return {
            "documentation": {
                "total_pages": doc_stats[0] or 0,
                "total_content_size": doc_stats[1] or 0,
                "last_updated": doc_stats[2],
                "pages_updated_last_hour": recent_docs
            },
            "templates": {
                "total_templates": sum(count for _, count in template_stats),
                "by_type": dict(template_stats)
            },
            "cache": {
                "total_entries": cache_stats[0] or 0,
                "active_entries": cache_stats[1] or 0,
                "expired_entries": cache_stats[2] or 0,
                "hit_rate": f"{((cache_stats[1] or 0) / max(cache_stats[0] or 1, 1)) * 100:.1f}%"
            },
            "storage": {
                "database_path": str(CACHE_DB),
                "database_size_mb": round(CACHE_DB.stat().st_size / (1024*1024), 2) if CACHE_DB.exists() else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    finally:
        conn.close()

# ======================== PARAMETERIZED RESOURCE TEMPLATES ========================

@mcp.resource("nrp://search/{query}")
def search_documentation(query: str) -> Dict[str, Any]:
    """
    Search through cached documentation content.

    Args:
        query: Search query string
    """
    limit_int = 10  # Default limit

    conn = sqlite3.connect(CACHE_DB)
    try:
        cursor = conn.execute("""
            SELECT path, title, content, last_updated
            FROM nrp_documentation
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY
                CASE
                    WHEN title LIKE ? THEN 1
                    WHEN content LIKE ? THEN 2
                    ELSE 3
                END,
                last_updated DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit_int))

        results = []
        for row in cursor.fetchall():
            # Extract relevant snippet
            content = row[2]
            query_pos = content.lower().find(query.lower())
            if query_pos != -1:
                start = max(0, query_pos - 100)
                end = min(len(content), query_pos + 200)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
            else:
                snippet = content[:200] + "..." if len(content) > 200 else content

            results.append({
                "path": row[0],
                "title": row[1],
                "snippet": snippet,
                "last_updated": row[3],
                "resource_uri": f"nrp://docs{row[0]}"
            })

        return {
            "query": query,
            "total_results": len(results),
            "limit": limit_int,
            "results": results,
            "searched_at": datetime.now().isoformat()
        }
    finally:
        conn.close()

@mcp.resource("nrp://generate/{resource_type}")
def generate_k8s_template(resource_type: str) -> str:
    """
    Generate a basic Kubernetes template for the specified resource type.

    Args:
        resource_type: Type of K8s resource (pod, deployment, service, etc.)
    """
    name = "example"
    namespace = "default"
    templates = {
        "pod": f"""apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: {namespace}
spec:
  containers:
  - name: {name}
    image: nginx:latest
    ports:
    - containerPort: 80
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
""",
        "deployment": f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          limits:
            memory: "256Mi"
            cpu: "200m"
          requests:
            memory: "128Mi"
            cpu: "100m"
""",
        "service": f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
    app: {name}
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
"""
    }

    template = templates.get(resource_type.lower())
    if not template:
        return f"# Error: Unknown resource type '{resource_type}'\n# Supported types: {', '.join(templates.keys())}"

    return template

# ======================== TOOLS FOR RESOURCE MANAGEMENT ========================

@mcp.tool
async def refresh_nrp_documentation(path: str = "/documentation") -> str:
    """
    Force refresh of NRP.ai documentation from the specified path.

    Args:
        path: Documentation path to refresh
    """
    try:
        doc_data = await NRPDocumentationScraper.scrape_documentation_section(path)
        doc_id = NRPDocumentationScraper.store_documentation(doc_data)

        # Extract templates
        template_count = 0
        if doc_data["yaml_blocks"]:
            templates = K8sTemplateGenerator.extract_k8s_templates(doc_data["yaml_blocks"])
            for template in templates:
                K8sTemplateGenerator.store_template(template, doc_data["url"])
                template_count += 1

        return f"Successfully refreshed documentation for {path}\n" \
               f"Content length: {len(doc_data['content'])} characters\n" \
               f"YAML blocks found: {len(doc_data['yaml_blocks'])}\n" \
               f"Templates extracted: {template_count}\n" \
               f"Title: {doc_data['title']}"

    except Exception as e:
        return f"Error refreshing documentation: {str(e)}"

@mcp.tool
async def clear_resource_cache(older_than_hours: int = 24) -> str:
    """
    Clear expired or old resource cache entries.

    Args:
        older_than_hours: Clear entries older than this many hours
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                DELETE FROM resource_cache
                WHERE expires_at <= datetime('now') OR expires_at < ?
            """, (cutoff_time.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            return f"Cleared {deleted_count} expired cache entries older than {older_than_hours} hours"
        finally:
            conn.close()

    except Exception as e:
        return f"Error clearing cache: {str(e)}"

if __name__ == "__main__":
    # Run the NRP resources server
    print("Starting NRP.ai Resources FastMCP Server...")
    print(f"Storage Directory: {STORAGE_DIR}")
    print(f"Database: {CACHE_DB}")
    print("\nAvailable Resource Types:")
    print("- Static: nrp://status, nrp://docs/index, nrp://templates/index")
    print("- Dynamic: nrp://docs/{path}, nrp://templates/{name}")
    print("- Parameterized: nrp://search/docs?q={query}, nrp://generate/k8s/{type}")
    mcp.run(transport="http", host="localhost", port=8005)