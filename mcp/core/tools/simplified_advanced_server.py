#!/usr/bin/env python3
"""
Simplified Advanced K8s Infogent FastMCP Server
==============================================
Implementing FastMCP advanced concepts with simplified returns:
- Async/sync tool support
- Advanced parameter validation
- Content scraping and storage
- Navigator-extractor-aggregator architecture
- NRP.ai documentation integration
"""

import os
import re
import sys
import yaml
import json
import asyncio
import aiohttp
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator
import logging

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing components
try:
    from kubernetes import client, config
    from nrp_k8s_system.systems.k8s_operations import (
        list_pods, list_deployments, list_services, list_jobs,
        describe_pod, describe_deployment, describe_service,
        create_pod_programmatic, create_deployment_programmatic,
        delete_pod, delete_deployment, pod_logs, pod_exec,
        check_permissions, get_service_account, get_pod_info,
        validate_k8s_name, handle_api_error, CURRENT_NAMESPACE
    )
except ImportError as e:
    print(f"Warning: Could not import K8s components: {e}")
    CURRENT_NAMESPACE = "gsoc"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize storage directory
STORAGE_DIR = Path(__file__).parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)
CACHE_DB = STORAGE_DIR / "content_cache.db"

# Initialize database
def init_database():
    """Initialize SQLite database for content storage"""
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scraped_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            content_type TEXT NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hash TEXT NOT NULL,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS yaml_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            yaml_content TEXT NOT NULL,
            source_url TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            validated BOOLEAN DEFAULT FALSE,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

init_database()

# Advanced Enums and Types
class ResourceType(str, Enum):
    POD = "pod"
    DEPLOYMENT = "deployment"
    SERVICE = "service"
    JOB = "job"

class ContentType(str, Enum):
    DOCUMENTATION = "documentation"
    YAML = "yaml"
    CODE = "code"
    TUTORIAL = "tutorial"

# Advanced Pydantic Models
class PodSpec(BaseModel):
    """Advanced pod specification with validation"""
    name: str = Field(..., pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
    image: str = Field(..., description="Container image")
    memory_limit: str = Field(default="128Mi", pattern=r'^\d+[KMGT]i?$')
    cpu_limit: str = Field(default="100m", pattern=r'^\d+m?$')
    memory_request: str = Field(default="64Mi", pattern=r'^\d+[KMGT]i?$')
    cpu_request: str = Field(default="50m", pattern=r'^\d+m?$')
    command: Optional[List[str]] = Field(default=None)
    restart_policy: Literal["Always", "OnFailure", "Never"] = Field(default="Always")

class ScrapingConfig(BaseModel):
    """Configuration for content scraping operations"""
    url: str = Field(..., description="URL to scrape")
    content_type: ContentType = Field(default=ContentType.DOCUMENTATION)
    extract_yaml: bool = Field(default=True, description="Extract YAML content")
    follow_links: bool = Field(default=False, description="Follow internal links")
    max_depth: int = Field(default=1, ge=1, le=3, description="Maximum crawling depth")
    cache_duration: int = Field(default=3600, description="Cache duration in seconds")

# Storage Classes
@dataclass
class ContentItem:
    """Structured content item for storage"""
    url: str
    content: str
    content_type: ContentType
    scraped_at: datetime
    hash: str
    metadata: Dict[str, Any]

class ContentStorage:
    """Content storage with caching"""

    @staticmethod
    def store_content(item: ContentItem) -> int:
        """Store content item in database"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO scraped_content
                (url, content, content_type, hash, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (item.url, item.content, item.content_type.value,
                  item.hash, json.dumps(item.metadata)))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_content(url: str) -> Optional[ContentItem]:
        """Retrieve content by URL"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                SELECT url, content, content_type, scraped_at, hash, metadata
                FROM scraped_content WHERE url = ?
            """, (url,))
            row = cursor.fetchone()
            if row:
                return ContentItem(
                    url=row[0], content=row[1], content_type=ContentType(row[2]),
                    scraped_at=datetime.fromisoformat(row[3]), hash=row[4],
                    metadata=json.loads(row[5] or '{}')
                )
        finally:
            conn.close()
        return None

    @staticmethod
    def store_yaml_resource(name: str, resource_type: str, yaml_content: str,
                          source_url: Optional[str] = None, metadata: Dict = None) -> int:
        """Store extracted YAML resource"""
        conn = sqlite3.connect(CACHE_DB)
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO yaml_resources
                (name, resource_type, yaml_content, source_url, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (name, resource_type, yaml_content, source_url,
                  json.dumps(metadata or {})))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

# Web Scraper Components
class WebNavigator:
    """Navigator component for discovering content"""

    @staticmethod
    async def discover_links(url: str, max_depth: int = 1) -> List[str]:
        """Discover relevant links from a page"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/'):
                        href = f"{url.rstrip('/')}{href}"
                    elif not href.startswith('http'):
                        continue

                    # Filter for relevant documentation links
                    if any(keyword in href.lower() for keyword in ['doc', 'guide', 'tutorial', 'example', 'yaml']):
                        links.append(href)

                return links[:10]  # Limit results
        except Exception as e:
            logger.error(f"Error discovering links from {url}: {e}")
            return []

class ContentExtractor:
    """Extractor component for processing content"""

    @staticmethod
    async def extract_content(url: str) -> str:
        """Extract content from a webpage"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text()
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""

    @staticmethod
    def extract_yaml_blocks(content: str) -> List[str]:
        """Extract YAML blocks from content"""
        yaml_pattern = r'```ya?ml\n(.*?)\n```'
        matches = re.findall(yaml_pattern, content, re.DOTALL | re.IGNORECASE)
        return matches

class ContentAggregator:
    """Aggregator component for organizing and storing content"""

    @staticmethod
    async def aggregate_and_store(url: str, content: str, content_type: ContentType,
                                metadata: Dict = None) -> ContentItem:
        """Aggregate content and store it"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        item = ContentItem(
            url=url,
            content=content,
            content_type=content_type,
            scraped_at=datetime.now(),
            hash=content_hash,
            metadata=metadata or {}
        )

        ContentStorage.store_content(item)

        # Extract and store YAML if present
        if content_type in [ContentType.DOCUMENTATION, ContentType.TUTORIAL]:
            yaml_blocks = ContentExtractor.extract_yaml_blocks(content)
            for i, yaml_block in enumerate(yaml_blocks):
                try:
                    yaml_data = yaml.safe_load(yaml_block)
                    if isinstance(yaml_data, dict) and 'kind' in yaml_data:
                        resource_name = yaml_data.get('metadata', {}).get('name', f'extracted-{i}')
                        resource_type = yaml_data.get('kind', 'unknown').lower()

                        ContentStorage.store_yaml_resource(
                            name=resource_name,
                            resource_type=resource_type,
                            yaml_content=yaml_block,
                            source_url=url,
                            metadata={'extraction_index': i}
                        )
                except yaml.YAMLError:
                    continue

        return item

# Create the FastMCP server
mcp = FastMCP(
    name="Simplified Advanced K8s Infogent Server",
    instructions="""
    Advanced Kubernetes operations server with comprehensive FastMCP features:
    - Kubernetes resource management with validation
    - Content scraping with navigator-extractor-aggregator architecture
    - NRP.ai documentation integration and YAML processing
    - Intelligent caching and content search
    """
)

# ======================== KUBERNETES TOOLS ========================

@mcp.tool
async def k8s_list_resources_advanced(
    resource_type: ResourceType,
    namespace: str = CURRENT_NAMESPACE,
    use_cache: bool = True,
    cache_ttl: int = 300
) -> str:
    """
    Advanced resource listing with caching and filtering.
    """
    try:
        # Cache key
        cache_key = f"{resource_type.value}:{namespace}"

        # Check cache if enabled
        if use_cache:
            cached = ContentStorage.get_content(f"cache://k8s/{cache_key}")
            if cached and (datetime.now() - cached.scraped_at).seconds < cache_ttl:
                return f"Cached {resource_type.value}s in {namespace}: {cached.content}"

        # Fetch fresh data
        if resource_type == ResourceType.POD:
            resources = list_pods()
        elif resource_type == ResourceType.DEPLOYMENT:
            resources = list_deployments()
        elif resource_type == ResourceType.SERVICE:
            resources = list_services()
        elif resource_type == ResourceType.JOB:
            resources = list_jobs()
        else:
            return f"Resource type {resource_type} not yet supported"

        # Store in cache
        if use_cache:
            cache_item = ContentItem(
                url=f"cache://k8s/{cache_key}",
                content=json.dumps(resources),
                content_type=ContentType.CODE,
                scraped_at=datetime.now(),
                hash=hashlib.sha256(json.dumps(resources).encode()).hexdigest(),
                metadata={"resource_type": resource_type.value, "namespace": namespace}
            )
            ContentStorage.store_content(cache_item)

        result = f"{resource_type.value.title()}s in namespace '{namespace}':\n" + \
                "\n".join(f"- {resource}" for resource in resources)
        return result

    except Exception as e:
        logger.error(f"Error listing {resource_type}: {e}")
        return f"Error: Failed to list {resource_type}: {str(e)}"

@mcp.tool
async def k8s_create_pod_advanced(spec: PodSpec) -> str:
    """
    Create a Kubernetes pod with comprehensive validation.
    """
    try:
        # Create the pod
        result = create_pod_programmatic(
            name=spec.name,
            image=spec.image,
            memory_limit=spec.memory_limit,
            cpu_limit=spec.cpu_limit,
            memory_request=spec.memory_request,
            cpu_request=spec.cpu_request,
            command=spec.command,
            namespace=CURRENT_NAMESPACE
        )

        # Store creation record
        creation_record = {
            "operation": "create_pod",
            "spec": spec.dict(),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        cache_item = ContentItem(
            url=f"operation://k8s/create_pod/{spec.name}",
            content=json.dumps(creation_record),
            content_type=ContentType.CODE,
            scraped_at=datetime.now(),
            hash=hashlib.sha256(json.dumps(creation_record).encode()).hexdigest(),
            metadata={"operation_type": "create", "resource_type": "pod"}
        )
        ContentStorage.store_content(cache_item)

        return f"Pod creation result: {result}"

    except Exception as e:
        logger.error(f"Error creating pod {spec.name}: {e}")
        return f"Error: Failed to create pod: {str(e)}"

# ======================== CONTENT SCRAPING TOOLS ========================

@mcp.tool
async def scrape_content(config: ScrapingConfig) -> str:
    """
    Scrape web content using navigator-extractor-aggregator architecture.
    """
    try:
        # Check cache first
        cached = ContentStorage.get_content(config.url)
        if cached and (datetime.now() - cached.scraped_at).seconds < config.cache_duration:
            return f"Cached content from {config.url} (length: {len(cached.content)} chars)"

        # Navigator: Discover content
        logger.info(f"Navigating to {config.url}")
        if config.follow_links:
            discovered_links = await WebNavigator.discover_links(config.url, config.max_depth)
        else:
            discovered_links = [config.url]

        all_content = []
        yaml_blocks = []

        # Extractor: Process each discovered URL
        for url in discovered_links[:5]:  # Limit to prevent overload
            logger.info(f"Extracting content from {url}")
            content = await ContentExtractor.extract_content(url)

            if content:
                all_content.append(f"=== Content from {url} ===\n{content}")

                # Extract YAML if requested
                if config.extract_yaml:
                    yaml_blocks.extend(ContentExtractor.extract_yaml_blocks(content))

        # Aggregator: Store and organize content
        combined_content = "\n\n".join(all_content)
        metadata = {
            "discovered_links": discovered_links,
            "yaml_blocks_found": len(yaml_blocks),
            "total_urls_processed": len([c for c in all_content if c])
        }

        stored_item = await ContentAggregator.aggregate_and_store(
            url=config.url,
            content=combined_content,
            content_type=config.content_type,
            metadata=metadata
        )

        return f"Successfully scraped content from {config.url}\n" \
               f"Processed {len(discovered_links)} URLs\n" \
               f"Found {len(yaml_blocks)} YAML blocks\n" \
               f"Content length: {len(combined_content)} characters"

    except Exception as e:
        logger.error(f"Error scraping content from {config.url}: {e}")
        return f"Error: Failed to scrape content: {str(e)}"

@mcp.tool
async def scrape_nrp_documentation(
    documentation_path: str = "/documentation",
    extract_yaml: bool = True,
    store_resources: bool = True
) -> str:
    """
    Specialized tool for scraping NRP.ai documentation with YAML processing.
    """
    try:
        base_url = "https://nrp.ai"
        full_url = f"{base_url}{documentation_path}"

        # Configure scraping for NRP.ai
        config = ScrapingConfig(
            url=full_url,
            content_type=ContentType.DOCUMENTATION,
            extract_yaml=extract_yaml,
            follow_links=True,
            max_depth=2,
            cache_duration=1800  # 30 minutes cache
        )

        # Use the main scraping tool
        result = await scrape_content(config)

        # Additional NRP-specific processing
        if store_resources and extract_yaml:
            # Query stored YAML resources
            conn = sqlite3.connect(CACHE_DB)
            try:
                cursor = conn.execute("""
                    SELECT name, resource_type, yaml_content
                    FROM yaml_resources
                    WHERE source_url LIKE ?
                    ORDER BY extracted_at DESC
                """, (f"{base_url}%",))

                nrp_resources = cursor.fetchall()

                return f"NRP.ai Documentation Scraping Complete\n" \
                       f"URL: {full_url}\n" \
                       f"YAML Resources Found: {len(nrp_resources)}\n" \
                       f"Resources: {[r[0] for r in nrp_resources[:5]]}\n" \
                       f"Base result: {result}"

            finally:
                conn.close()

        return result

    except Exception as e:
        logger.error(f"Error scraping NRP documentation: {e}")
        return f"Error: Failed to scrape NRP documentation: {str(e)}"

@mcp.tool
async def search_content(
    query: str,
    content_types: Optional[List[ContentType]] = None,
    limit: int = 10
) -> str:
    """
    Search through stored content with filtering capabilities.
    """
    try:
        conn = sqlite3.connect(CACHE_DB)

        # Build dynamic query
        sql = """
            SELECT url, content, content_type, scraped_at, metadata
            FROM scraped_content
            WHERE content LIKE ?
        """
        params = [f"%{query}%"]

        # Apply filters
        if content_types:
            placeholders = ','.join(['?' for _ in content_types])
            sql += f" AND content_type IN ({placeholders})"
            params.extend([ct.value for ct in content_types])

        sql += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return f"No results found for query: '{query}'"

        result_text = f"Found {len(results)} results for query: '{query}'\n\n"
        for row in results:
            preview = row[1][:200] + "..." if len(row[1]) > 200 else row[1]
            result_text += f"- {row[0]} ({row[2]}) - {row[3][:19]}\n"
            result_text += f"  Preview: {preview}\n\n"

        return result_text

    except Exception as e:
        logger.error(f"Error searching content: {e}")
        return f"Error: Search failed: {str(e)}"

@mcp.tool
async def get_yaml_resources(
    resource_type: Optional[str] = None,
    name_pattern: Optional[str] = None,
    source_url_pattern: Optional[str] = None
) -> str:
    """
    Search and retrieve stored YAML resources with filtering.
    """
    try:
        conn = sqlite3.connect(CACHE_DB)

        sql = "SELECT name, resource_type, yaml_content, source_url, extracted_at, validated FROM yaml_resources WHERE 1=1"
        params = []

        if resource_type:
            sql += " AND resource_type = ?"
            params.append(resource_type)

        if name_pattern:
            sql += " AND name LIKE ?"
            params.append(f"%{name_pattern}%")

        if source_url_pattern:
            sql += " AND source_url LIKE ?"
            params.append(f"%{source_url_pattern}%")

        sql += " ORDER BY extracted_at DESC"

        cursor = conn.execute(sql, params)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return "No YAML resources found matching the criteria"

        result_text = f"Found {len(results)} YAML resources\n\n"
        for row in results:
            result_text += f"- {row[0]} ({row[1]}) from {row[3] or 'unknown'}\n"
            result_text += f"  Validated: {'✓' if row[5] else '✗'} | Extracted: {row[4][:19]}\n"
            result_text += f"  YAML Preview: {row[2][:100]}...\n\n"

        return result_text

    except Exception as e:
        logger.error(f"Error retrieving YAML resources: {e}")
        return f"Error: Failed to retrieve YAML resources: {str(e)}"

# ======================== RESOURCES ========================

@mcp.resource("infogent://cache/stats")
def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache and storage statistics"""
    conn = sqlite3.connect(CACHE_DB)
    try:
        # Content statistics
        content_stats = conn.execute("""
            SELECT content_type, COUNT(*), SUM(LENGTH(content))
            FROM scraped_content
            GROUP BY content_type
        """).fetchall()

        # YAML statistics
        yaml_stats = conn.execute("""
            SELECT resource_type, COUNT(*), SUM(validated)
            FROM yaml_resources
            GROUP BY resource_type
        """).fetchall()

        # Recent activity
        recent_content = conn.execute("""
            SELECT COUNT(*) FROM scraped_content
            WHERE scraped_at > datetime('now', '-1 hour')
        """).fetchone()[0]

        return {
            "content_statistics": [
                {"type": row[0], "count": row[1], "total_size": row[2]}
                for row in content_stats
            ],
            "yaml_statistics": [
                {"resource_type": row[0], "count": row[1], "validated": row[2]}
                for row in yaml_stats
            ],
            "recent_activity": {
                "content_scraped_last_hour": recent_content
            },
            "database_path": str(CACHE_DB),
            "storage_directory": str(STORAGE_DIR)
        }
    finally:
        conn.close()

@mcp.resource("infogent://architecture/overview")
def get_architecture_overview() -> Dict[str, Any]:
    """Get overview of the infogent architecture components"""
    return {
        "architecture": "Navigator-Extractor-Aggregator",
        "components": {
            "navigator": {
                "description": "Discovers and maps content sources",
                "capabilities": ["Link discovery", "Content mapping", "Depth-limited crawling"]
            },
            "extractor": {
                "description": "Processes and extracts structured content",
                "capabilities": ["Content extraction", "YAML parsing", "Selector-based extraction"]
            },
            "aggregator": {
                "description": "Organizes and stores processed content",
                "capabilities": ["Content storage", "Metadata management", "Caching strategies"]
            }
        },
        "storage": {
            "database": "SQLite with content and YAML tables",
            "caching": "Time-based with configurable TTL",
            "indexing": "URL-based with hash verification"
        },
        "integration": {
            "kubernetes": "Full CRUD operations with validation",
            "nrp_ai": "Documentation scraping and YAML extraction",
            "fastmcp": "Advanced tools with async support"
        }
    }

if __name__ == "__main__":
    # Run the simplified advanced server on HTTP transport
    print("Starting Simplified Advanced K8s Infogent FastMCP Server...")
    print(f"Namespace: {CURRENT_NAMESPACE}")
    print(f"Storage Directory: {STORAGE_DIR}")
    print(f"Database: {CACHE_DB}")
    mcp.run(transport="http", host="localhost", port=8004)