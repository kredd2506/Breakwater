#!/usr/bin/env python3
"""
Enhanced Ultimate NRP.ai Resources Server
=========================================
Enhanced version with proper extraction of:
- Caution and note sections
- A100 GPU request examples
- Special instructions and warnings
- YAML configurations with context
"""

import os
import re
import sys
import json
import sqlite3
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse
from fastmcp import FastMCP
from bs4 import BeautifulSoup

# Import our existing components
from nrp_crawler_and_indexer import NRPDocumentationCrawler
from enhanced_content_extractor import EnhancedNRPContentExtractor

# Setup
STORAGE_DIR = Path(__file__).parent / "ultimate_nrp_resources"
STORAGE_DIR.mkdir(exist_ok=True)
CRAWLER_DB = Path(__file__).parent / "nrp_crawled_data" / "nrp_crawled_docs.db"

# Initialize FastMCP
mcp = FastMCP("Enhanced Ultimate NRP.ai Resources Server")

class EnhancedNRPManager:
    def __init__(self):
        self.crawler_db = CRAWLER_DB
        self.content_extractor = EnhancedNRPContentExtractor(self.crawler_db)

    async def get_live_gpu_content(self) -> Dict[str, Any]:
        """Get live GPU pods content with enhanced extraction"""
        url = "https://nrp.ai/documentation/userdocs/running/gpu-pods/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self.extract_gpu_content(content, url)
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    def extract_gpu_content(self, content: str, url: str) -> Dict[str, Any]:
        """Extract GPU-specific content with special formatting"""
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()

        extracted = {
            'url': url,
            'title': 'GPU Pods | NRP Nautilus',
            'extraction_timestamp': datetime.now().isoformat(),
            'content_length': len(content),
            'special_sections': {
                'a100_examples': [],
                'gpu_resource_types': [],
                'yaml_configurations': [],
                'cautions_and_notes': [],
                'request_instructions': [],
                'gpu_type_table': []
            }
        }

        # Extract A100 specific examples
        a100_patterns = [
            r'(A100[^.]*?nvidia\.com/a100[^.]*?)',
            r'(Using A100s[^.]*?reservation[^.]*?)',
            r'(modifying.*?A100.*?yaml.*?apiVersion[^}]*?nvidia\.com/a100[^}]*?)',
        ]

        for pattern in a100_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 20:
                    extracted['special_sections']['a100_examples'].append({
                        'text': match.strip(),
                        'type': 'a100_example'
                    })

        # Extract GPU resource types table
        gpu_type_pattern = r'(GPU Type.*?resource.*?(?:A40|A100|RTX|Grace Hopper)[^.]*?nvidia\.com/[^.]*?)'
        gpu_matches = re.findall(gpu_type_pattern, text_content, re.IGNORECASE | re.DOTALL)
        for match in gpu_matches:
            extracted['special_sections']['gpu_type_table'].append({
                'text': match.strip(),
                'type': 'gpu_table'
            })

        # Extract specific GPU resource examples
        gpu_resource_patterns = [
            r'(nvidia\.com/gpu:\s*\d+)',
            r'(nvidia\.com/a100:\s*\d+)',
            r'(nvidia\.com/a40:\s*\d+)',
            r'(nvidia\.com/rtx[^:]*?:\s*\d+)',
            r'(nvidia\.com/gh200:\s*\d+)'
        ]

        for pattern in gpu_resource_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                extracted['special_sections']['gpu_resource_types'].append({
                    'resource': match.strip(),
                    'type': 'gpu_resource'
                })

        # Extract YAML configurations
        yaml_patterns = [
            r'```ya?ml\s*([\s\S]*?)```',
            r'(apiVersion:\s*v1\s*kind:\s*Pod[\s\S]*?nvidia\.com/[^:]*?:\s*\d+[\s\S]*?)(?=\n\s*[A-Z]|\n\s*$)',
        ]

        for pattern in yaml_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                yaml_content = match.strip()
                if 'nvidia.com' in yaml_content and len(yaml_content) > 50:
                    # Determine GPU type from YAML
                    gpu_type = 'general'
                    if 'nvidia.com/a100' in yaml_content:
                        gpu_type = 'A100'
                    elif 'nvidia.com/a40' in yaml_content:
                        gpu_type = 'A40'
                    elif 'nvidia.com/rtx' in yaml_content:
                        gpu_type = 'RTX'
                    elif 'nvidia.com/gh200' in yaml_content:
                        gpu_type = 'Grace Hopper'

                    extracted['special_sections']['yaml_configurations'].append({
                        'yaml': yaml_content,
                        'gpu_type': gpu_type,
                        'type': 'yaml_config'
                    })

        # Extract request instructions
        instruction_patterns = [
            r'(To request.*?(?:GPU|A100|RTX)[^.]*?\.)',
            r'(You have to request.*?resource[^.]*?\.)',
            r'(For.*?(?:A100|GPU).*?make sure[^.]*?\.)',
        ]

        for pattern in instruction_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 20:
                    extracted['special_sections']['request_instructions'].append({
                        'instruction': match.strip(),
                        'type': 'instruction'
                    })

        # Extract cautions and notes
        caution_patterns = [
            r'(Note:.*?[.!])',
            r'(Caution:.*?[.!])',
            r'(Important:.*?[.!])',
            r'(Warning:.*?[.!])',
        ]

        for pattern in caution_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                extracted['special_sections']['cautions_and_notes'].append({
                    'text': match.strip(),
                    'type': 'caution_note'
                })

        return extracted

# Initialize the enhanced manager
enhanced_manager = EnhancedNRPManager()

# Enhanced GPU Pods Resource
@mcp.resource("nrp://enhanced/gpu-pods")
async def get_enhanced_gpu_pods() -> Dict[str, Any]:
    """Enhanced GPU pods documentation with special sections properly extracted"""

    # Get live content with enhanced extraction
    live_content = await enhanced_manager.get_live_gpu_content()

    if 'error' in live_content:
        return {
            'title': 'GPU Pods Documentation',
            'status': 'error',
            'error': live_content['error'],
            'fallback': 'Try using cached content from crawled database'
        }

    # Format the response with proper sections
    return {
        'title': live_content['title'],
        'url': live_content['url'],
        'content_length': live_content['content_length'],
        'last_updated': live_content['extraction_timestamp'],
        'status': 'live_content_extracted',

        # A100 Examples Section
        'a100_gpu_examples': {
            'count': len(live_content['special_sections']['a100_examples']),
            'examples': live_content['special_sections']['a100_examples'],
            'description': 'Specific examples for requesting A100 GPUs with reservations'
        },

        # GPU Resource Types
        'gpu_resource_types': {
            'count': len(live_content['special_sections']['gpu_resource_types']),
            'resources': live_content['special_sections']['gpu_resource_types'],
            'description': 'Available GPU resource specifications for different GPU types'
        },

        # YAML Configurations
        'yaml_configurations': {
            'count': len(live_content['special_sections']['yaml_configurations']),
            'configs': live_content['special_sections']['yaml_configurations'],
            'description': 'Complete YAML configurations for GPU pod requests'
        },

        # Instructions and Guidelines
        'request_instructions': {
            'count': len(live_content['special_sections']['request_instructions']),
            'instructions': live_content['special_sections']['request_instructions'],
            'description': 'Step-by-step instructions for requesting specific GPU types'
        },

        # Cautions and Important Notes
        'cautions_and_notes': {
            'count': len(live_content['special_sections']['cautions_and_notes']),
            'notes': live_content['special_sections']['cautions_and_notes'],
            'description': 'Important cautions, notes, and warnings for GPU usage'
        },

        # GPU Type Reference Table
        'gpu_type_table': {
            'count': len(live_content['special_sections']['gpu_type_table']),
            'table_data': live_content['special_sections']['gpu_type_table'],
            'description': 'Reference table of GPU types and their resource identifiers'
        }
    }

# Specific A100 Resource
@mcp.resource("nrp://gpu/a100-examples")
async def get_a100_examples() -> Dict[str, Any]:
    """Specific A100 GPU request examples and instructions"""

    gpu_content = await enhanced_manager.get_live_gpu_content()

    if 'error' in gpu_content:
        return {'error': gpu_content['error']}

    a100_examples = gpu_content['special_sections']['a100_examples']
    yaml_configs = [config for config in gpu_content['special_sections']['yaml_configurations']
                   if config['gpu_type'] == 'A100']

    return {
        'title': 'A100 GPU Request Examples',
        'description': 'Complete guide for requesting A100 GPUs on NRP Nautilus',
        'reservation_required': True,
        'resource_identifier': 'nvidia.com/a100',

        'examples': {
            'count': len(a100_examples),
            'detailed_examples': a100_examples
        },

        'yaml_configurations': {
            'count': len(yaml_configs),
            'configs': yaml_configs
        },

        'key_points': [
            'A100 GPUs require reservations',
            'Use nvidia.com/a100 instead of nvidia.com/gpu',
            'Specify both limits and requests in your YAML',
            'Consider using Grace Hopper variants for ARM support'
        ]
    }

# Enhanced Cautions and Notes Resource
@mcp.resource("nrp://special/cautions-notes")
async def get_all_cautions_notes() -> Dict[str, Any]:
    """All cautions, notes, and important warnings from NRP documentation"""

    # Get from multiple sources
    gpu_content = await enhanced_manager.get_live_gpu_content()

    all_cautions = []

    if 'special_sections' in gpu_content:
        all_cautions.extend(gpu_content['special_sections']['cautions_and_notes'])
        all_cautions.extend(gpu_content['special_sections']['request_instructions'])

    return {
        'title': 'NRP Documentation - Cautions and Important Notes',
        'total_items': len(all_cautions),
        'categories': {
            'gpu_related': [item for item in all_cautions if 'gpu' in item['text'].lower() or 'a100' in item['text'].lower()],
            'general_instructions': [item for item in all_cautions if item['type'] == 'instruction'],
            'cautions_warnings': [item for item in all_cautions if item['type'] == 'caution_note']
        },
        'all_items': all_cautions,
        'extraction_source': 'live_documentation'
    }

# Tool to refresh GPU content
@mcp.tool()
async def refresh_gpu_documentation() -> str:
    """Refresh GPU documentation with latest content including A100 examples"""
    try:
        gpu_content = await enhanced_manager.get_live_gpu_content()

        if 'error' in gpu_content:
            return f"Failed to refresh: {gpu_content['error']}"

        stats = {
            'a100_examples': len(gpu_content['special_sections']['a100_examples']),
            'yaml_configs': len(gpu_content['special_sections']['yaml_configurations']),
            'instructions': len(gpu_content['special_sections']['request_instructions']),
            'cautions': len(gpu_content['special_sections']['cautions_and_notes'])
        }

        return f"GPU documentation refreshed successfully. Found: {stats['a100_examples']} A100 examples, {stats['yaml_configs']} YAML configs, {stats['instructions']} instructions, {stats['cautions']} cautions/notes."

    except Exception as e:
        return f"Refresh failed: {str(e)}"

if __name__ == "__main__":
    print("Starting Enhanced Ultimate NRP.ai Resources Server...")
    print(f"Crawler Database: {CRAWLER_DB}")
    print(f"Database exists: {CRAWLER_DB.exists()}")
    print()
    print("Enhanced Resource Categories:")
    print("- nrp://enhanced/gpu-pods - GPU pods with A100 examples and cautions")
    print("- nrp://gpu/a100-examples - Specific A100 GPU request examples")
    print("- nrp://special/cautions-notes - All cautions and important notes")
    print()

    mcp.run(transport="http", port=8008)