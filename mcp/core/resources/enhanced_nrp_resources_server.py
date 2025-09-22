#!/usr/bin/env python3
"""
Enhanced NRP.ai Resources FastMCP Server
========================================
Implementing ALL FastMCP resource concepts including:
- Static resources with metadata
- Dynamic resources with lazy loading
- Resource templates with parameterized URIs
- Wildcard parameters and default values
- Async/sync resource generation
- Custom resource keys and annotations
- Error handling and notifications
- Comprehensive YAML examples from NRP/Nautilus
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
from typing import Dict, Any, List, Optional, Union, Tuple
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
STORAGE_DIR = Path(__file__).parent / "enhanced_nrp_resources"
STORAGE_DIR.mkdir(exist_ok=True)
CACHE_DB = STORAGE_DIR / "enhanced_nrp_cache.db"

def init_enhanced_database():
    """Initialize enhanced SQLite database for advanced resource caching"""
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nrp_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_key TEXT UNIQUE NOT NULL,
            content_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            tags TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            cache_ttl INTEGER DEFAULT 3600
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS yaml_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT UNIQUE NOT NULL,
            template_type TEXT NOT NULL,
            template_content TEXT NOT NULL,
            parameters TEXT,
            description TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS resource_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_uri TEXT NOT NULL,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            client_info TEXT,
            parameters TEXT
        )
    """)

    conn.commit()
    conn.close()

# Initialize database
init_enhanced_database()

# Comprehensive NRP/Nautilus YAML templates
NRP_YAML_TEMPLATES = {
    "basic-pod": {
        "type": "pod",
        "description": "Basic Nautilus pod with resource requests",
        "parameters": ["name", "image", "cpu", "memory"],
        "template": """apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: gsoc
spec:
  containers:
  - name: {name}
    image: {image}
    resources:
      requests:
        cpu: {cpu}
        memory: {memory}
      limits:
        cpu: {cpu}
        memory: {memory}
  restartPolicy: Never"""
    },

    "gpu-pod": {
        "type": "pod",
        "description": "GPU-enabled pod for ML workloads on Nautilus",
        "parameters": ["name", "image", "gpu_type", "gpu_count"],
        "template": """apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: gsoc
spec:
  containers:
  - name: {name}
    image: {image}
    resources:
      requests:
        nvidia.com/{gpu_type}: {gpu_count}
        cpu: 4
        memory: 16Gi
      limits:
        nvidia.com/{gpu_type}: {gpu_count}
        cpu: 8
        memory: 32Gi
  restartPolicy: Never
  nodeSelector:
    gpu-type: {gpu_type}"""
    },

    "persistent-volume": {
        "type": "storage",
        "description": "Persistent volume claim for Nautilus storage",
        "parameters": ["name", "size", "storage_class"],
        "template": """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {name}
  namespace: gsoc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: {size}
  storageClassName: {storage_class}"""
    },

    "deployment": {
        "type": "deployment",
        "description": "Scalable deployment for Nautilus cluster",
        "parameters": ["name", "image", "replicas", "cpu", "memory"],
        "template": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: gsoc
spec:
  replicas: {replicas}
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
        image: {image}
        resources:
          requests:
            cpu: {cpu}
            memory: {memory}
          limits:
            cpu: {cpu}
            memory: {memory}
        ports:
        - containerPort: 8080"""
    },

    "service": {
        "type": "service",
        "description": "Service to expose deployment on Nautilus",
        "parameters": ["name", "port", "target_port"],
        "template": """apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: gsoc
spec:
  selector:
    app: {name}
  ports:
  - port: {port}
    targetPort: {target_port}
    protocol: TCP
  type: ClusterIP"""
    },

    "ingress": {
        "type": "ingress",
        "description": "Ingress for external access on Nautilus",
        "parameters": ["name", "host", "service_name", "service_port"],
        "template": """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}
  namespace: gsoc
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - {host}
    secretName: {name}-tls
  rules:
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {service_name}
            port:
              number: {service_port}"""
    }
}

# Initialize FastMCP
mcp = FastMCP("Enhanced NRP.ai Resources Server")

def log_resource_access(resource_uri: str, parameters: Optional[Dict] = None):
    """Log resource access for analytics"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        conn.execute(
            "INSERT INTO resource_access_log (resource_uri, parameters) VALUES (?, ?)",
            (resource_uri, json.dumps(parameters or {}))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log access: {e}")

def cache_content(key: str, content: Any, content_type: str = "json", ttl: int = 3600, tags: List[str] = None):
    """Cache content with metadata"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        metadata = {"cached_at": datetime.now().isoformat(), "ttl": ttl}
        conn.execute("""
            INSERT OR REPLACE INTO nrp_content
            (resource_key, content_type, content, metadata, tags, cache_ttl)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, content_type, json.dumps(content) if content_type == "json" else str(content),
              json.dumps(metadata), json.dumps(tags or []), ttl))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to cache content: {e}")

def get_cached_content(key: str) -> Optional[Any]:
    """Get cached content if not expired"""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.execute(
            "SELECT content, content_type, metadata, cache_ttl FROM nrp_content WHERE resource_key = ?",
            (key,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            content, content_type, metadata_str, ttl = row
            metadata = json.loads(metadata_str)
            cached_at = datetime.fromisoformat(metadata["cached_at"])

            if datetime.now() - cached_at < timedelta(seconds=ttl):
                return json.loads(content) if content_type == "json" else content
        return None
    except Exception as e:
        logger.error(f"Failed to get cached content: {e}")
        return None

# 1. STATIC RESOURCES with metadata and tags
@mcp.resource("nrp://server/info")
def get_server_info() -> Dict[str, Any]:
    """Server information with comprehensive metadata"""
    log_resource_access("nrp://server/info")

    info = {
        "name": "Enhanced NRP.ai Resources Server",
        "version": "2.0.0",
        "description": "Advanced FastMCP resource server with comprehensive NRP/Nautilus integration",
        "capabilities": [
            "static_resources",
            "dynamic_resources",
            "resource_templates",
            "wildcard_parameters",
            "async_generation",
            "caching",
            "yaml_templates",
            "k8s_resources",
            "analytics"
        ],
        "supported_formats": ["json", "yaml", "text", "binary"],
        "cache_stats": get_cache_statistics(),
        "uptime": datetime.now().isoformat(),
        "tags": ["nrp", "nautilus", "kubernetes", "resources", "templates"]
    }

    cache_content("server_info", info, tags=["static", "server"])
    return info

@mcp.resource("nrp://templates/catalog")
def get_templates_catalog() -> Dict[str, Any]:
    """Comprehensive catalog of all available templates"""
    log_resource_access("nrp://templates/catalog")

    catalog = {
        "total_templates": len(NRP_YAML_TEMPLATES),
        "templates": {}
    }

    for name, template in NRP_YAML_TEMPLATES.items():
        catalog["templates"][name] = {
            "name": name,
            "type": template["type"],
            "description": template["description"],
            "parameters": template["parameters"],
            "uri": f"nrp://template/{name}",
            "generate_uri": f"nrp://generate/{template['type']}/{name}"
        }

    cache_content("templates_catalog", catalog, tags=["static", "templates"])
    return catalog

# 2. DYNAMIC RESOURCES with lazy loading
@mcp.resource("nrp://docs/{path}")
async def get_documentation_content(path: str) -> Dict[str, Any]:
    """Dynamic documentation fetching with enhanced caching"""
    log_resource_access(f"nrp://docs/{path}", {"path": path})

    # Check cache first
    cache_key = f"docs_{path.replace('/', '_')}"
    cached = get_cached_content(cache_key)
    if cached:
        return cached

    # Fetch fresh content
    try:
        url = f"https://nrp.ai{path}" if not path.startswith('http') else path
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()

                    # Extract title
                    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                    title = title_match.group(1) if title_match else f"Documentation: {path}"

                    # Extract YAML blocks
                    yaml_blocks = re.findall(r'```ya?ml\s*([\s\S]*?)```', content, re.IGNORECASE)
                    k8s_blocks = re.findall(r'(apiVersion:\s*[\w/]+\s*\nkind:\s*\w+[\s\S]*?)(?=\n\s*(?:apiVersion|---|$))', content)

                    result = {
                        "path": path,
                        "title": title,
                        "content": content[:2000],  # Truncate for display
                        "full_content_length": len(content),
                        "yaml_blocks": len(yaml_blocks + k8s_blocks),
                        "yaml_examples": yaml_blocks + k8s_blocks,
                        "last_fetched": datetime.now().isoformat(),
                        "source_url": url,
                        "status": "success"
                    }

                    # Cache for 30 minutes
                    cache_content(cache_key, result, ttl=1800, tags=["dynamic", "docs", path])
                    return result
                else:
                    return {
                        "path": path,
                        "title": f"Error {response.status}",
                        "content": f"Failed to fetch content: HTTP {response.status}",
                        "status": "error",
                        "error_code": response.status
                    }
    except Exception as e:
        return {
            "path": path,
            "title": "Fetch Error",
            "content": f"Error fetching content: {str(e)}",
            "status": "error",
            "error_message": str(e)
        }

# 3. RESOURCE TEMPLATES with wildcard parameters
@mcp.resource("nrp://template/{template_name}")
def get_template_definition(template_name: str) -> Dict[str, Any]:
    """Get specific template definition with metadata"""
    log_resource_access(f"nrp://template/{template_name}", {"template_name": template_name})

    if template_name not in NRP_YAML_TEMPLATES:
        return {
            "error": "Template not found",
            "template_name": template_name,
            "available_templates": list(NRP_YAML_TEMPLATES.keys())
        }

    template = NRP_YAML_TEMPLATES[template_name]

    result = {
        "name": template_name,
        "type": template["type"],
        "description": template["description"],
        "parameters": template["parameters"],
        "template_content": template["template"],
        "example_parameters": get_example_parameters(template_name),
        "usage": f"Use nrp://generate/{template['type']}/{template_name} to generate with parameters",
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "parameter_count": len(template["parameters"]),
            "template_lines": len(template["template"].split('\n'))
        }
    }

    cache_content(f"template_{template_name}", result, tags=["static", "template", template["type"]])
    return result

# 4. PARAMETERIZED RESOURCES with default values
@mcp.resource("nrp://generate/{resource_type}/{template_name}")
def generate_resource_from_template(resource_type: str, template_name: str) -> str:
    """Generate K8s resource from template with parameter substitution"""
    log_resource_access(f"nrp://generate/{resource_type}/{template_name}", {
        "resource_type": resource_type,
        "template_name": template_name
    })

    if template_name not in NRP_YAML_TEMPLATES:
        return f"# Template '{template_name}' not found\n# Available: {', '.join(NRP_YAML_TEMPLATES.keys())}"

    template = NRP_YAML_TEMPLATES[template_name]

    # Use example parameters as defaults
    params = get_example_parameters(template_name)

    try:
        generated = template["template"].format(**params)

        # Cache generated template
        cache_key = f"generated_{resource_type}_{template_name}"
        cache_content(cache_key, generated, content_type="yaml", tags=["generated", resource_type, template_name])

        return generated
    except KeyError as e:
        return f"# Missing parameter: {e}\n# Required parameters: {template['parameters']}"

def get_example_parameters(template_name: str) -> Dict[str, str]:
    """Get example parameters for template"""
    examples = {
        "basic-pod": {
            "name": "my-nautilus-pod",
            "image": "nginx:latest",
            "cpu": "1",
            "memory": "2Gi"
        },
        "gpu-pod": {
            "name": "ml-training-pod",
            "image": "pytorch/pytorch:latest",
            "gpu_type": "gpu",
            "gpu_count": "1"
        },
        "persistent-volume": {
            "name": "my-storage",
            "size": "10Gi",
            "storage_class": "rook-cephfs"
        },
        "deployment": {
            "name": "web-app",
            "image": "nginx:latest",
            "replicas": "3",
            "cpu": "500m",
            "memory": "1Gi"
        },
        "service": {
            "name": "web-service",
            "port": "80",
            "target_port": "8080"
        },
        "ingress": {
            "name": "web-ingress",
            "host": "myapp.nrp-nautilus.io",
            "service_name": "web-service",
            "service_port": "80"
        }
    }
    return examples.get(template_name, {})

# 5. SEARCH RESOURCES with flexible parameters
@mcp.resource("nrp://search/{query}")
async def search_resources(query: str) -> Dict[str, Any]:
    """Advanced search across all resources and templates"""
    log_resource_access(f"nrp://search/{query}", {"query": query})

    results = {
        "query": query,
        "total_results": 0,
        "templates": [],
        "documentation": [],
        "cached_content": []
    }

    # Search templates
    for name, template in NRP_YAML_TEMPLATES.items():
        if (query.lower() in name.lower() or
            query.lower() in template["description"].lower() or
            query.lower() in template["type"].lower()):
            results["templates"].append({
                "name": name,
                "type": template["type"],
                "description": template["description"],
                "relevance": calculate_relevance(query, name, template)
            })

    # Search cached documentation
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.execute(
            "SELECT resource_key, content FROM nrp_content WHERE content LIKE ? AND tags LIKE ?",
            (f"%{query}%", "%docs%")
        )
        for row in cursor:
            key, content = row
            results["cached_content"].append({
                "key": key,
                "preview": content[:200] + "..." if len(content) > 200 else content
            })
        conn.close()
    except Exception as e:
        logger.error(f"Search error: {e}")

    results["total_results"] = len(results["templates"]) + len(results["documentation"]) + len(results["cached_content"])

    cache_content(f"search_{query}", results, ttl=600, tags=["search", "dynamic"])
    return results

def calculate_relevance(query: str, name: str, template: Dict) -> float:
    """Calculate search relevance score"""
    score = 0.0
    query_lower = query.lower()

    if query_lower in name.lower():
        score += 1.0
    if query_lower in template["description"].lower():
        score += 0.7
    if query_lower in template["type"].lower():
        score += 0.5

    return score

# 6. ANALYTICS AND CACHE RESOURCES
@mcp.resource("nrp://analytics/usage")
def get_usage_analytics() -> Dict[str, Any]:
    """Resource usage analytics"""
    log_resource_access("nrp://analytics/usage")

    try:
        conn = sqlite3.connect(CACHE_DB)

        # Get access counts
        cursor = conn.execute("""
            SELECT resource_uri, COUNT(*) as access_count
            FROM resource_access_log
            GROUP BY resource_uri
            ORDER BY access_count DESC
            LIMIT 10
        """)
        top_resources = [{"uri": row[0], "count": row[1]} for row in cursor]

        # Get recent activity
        cursor = conn.execute("""
            SELECT resource_uri, access_time
            FROM resource_access_log
            ORDER BY access_time DESC
            LIMIT 20
        """)
        recent_activity = [{"uri": row[0], "time": row[1]} for row in cursor]

        conn.close()

        return {
            "top_resources": top_resources,
            "recent_activity": recent_activity,
            "cache_statistics": get_cache_statistics(),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    try:
        conn = sqlite3.connect(CACHE_DB)

        # Content stats
        cursor = conn.execute("SELECT COUNT(*), content_type FROM nrp_content GROUP BY content_type")
        content_stats = {row[1]: row[0] for row in cursor}

        # Total cache size
        cursor = conn.execute("SELECT SUM(LENGTH(content)) FROM nrp_content")
        total_size = cursor.fetchone()[0] or 0

        # Access stats
        cursor = conn.execute("SELECT COUNT(*) FROM resource_access_log")
        total_accesses = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "content_by_type": content_stats,
            "total_entries": sum(content_stats.values()),
            "total_size_bytes": total_size,
            "total_accesses": total_accesses,
            "database_path": str(CACHE_DB)
        }
    except Exception as e:
        return {"error": str(e)}

# 7. TOOLS for resource management
@mcp.tool()
async def refresh_template_cache() -> str:
    """Refresh all cached templates and documentation"""
    try:
        # Clear old cache entries
        conn = sqlite3.connect(CACHE_DB)
        conn.execute("DELETE FROM nrp_content WHERE tags LIKE '%dynamic%'")
        conn.commit()
        conn.close()

        # Refresh key documentation
        docs_to_refresh = ["/documentation", "/user-guide", "/examples"]
        refreshed = 0

        for doc_path in docs_to_refresh:
            try:
                await get_documentation_content(doc_path)
                refreshed += 1
            except Exception as e:
                logger.error(f"Failed to refresh {doc_path}: {e}")

        return f"Successfully refreshed {refreshed} documentation pages and cleared dynamic cache"
    except Exception as e:
        return f"Error refreshing cache: {str(e)}"

@mcp.tool()
def clear_analytics_data(older_than_hours: int = 24) -> str:
    """Clear analytics data older than specified hours"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.execute(
            "DELETE FROM resource_access_log WHERE access_time < ?",
            (cutoff_time.isoformat(),)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return f"Cleared {deleted_count} analytics entries older than {older_than_hours} hours"
    except Exception as e:
        return f"Error clearing analytics: {str(e)}"

if __name__ == "__main__":
    print("Starting Enhanced NRP.ai Resources FastMCP Server...")
    print(f"Storage Directory: {STORAGE_DIR}")
    print(f"Database: {CACHE_DB}")
    print()
    print("Available Resource Types:")
    print("- Static: nrp://server/info, nrp://templates/catalog")
    print("- Dynamic: nrp://docs/{path}, nrp://search/{query}")
    print("- Templates: nrp://template/{name}, nrp://generate/{type}/{name}")
    print("- Analytics: nrp://analytics/usage")
    print()

    # Populate initial templates in database
    try:
        conn = sqlite3.connect(CACHE_DB)
        for name, template in NRP_YAML_TEMPLATES.items():
            conn.execute("""
                INSERT OR REPLACE INTO yaml_templates
                (template_name, template_type, template_content, parameters, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, template["type"], template["template"],
                  json.dumps(template["parameters"]), template["description"]))
        conn.commit()
        conn.close()
        print(f"Initialized {len(NRP_YAML_TEMPLATES)} YAML templates in database")
    except Exception as e:
        print(f"Warning: Failed to initialize templates: {e}")

    mcp.run(transport="http", port=8006)