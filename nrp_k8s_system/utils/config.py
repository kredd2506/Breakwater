#!/usr/bin/env python3
"""
Configuration management for NRP K8s System
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Package paths
PACKAGE_DIR = Path(__file__).parent.parent
CACHE_DIR = PACKAGE_DIR / "cache"
ROUTER_CACHE_DIR = CACHE_DIR / "router_cache"
BUILDER_CACHE_DIR = CACHE_DIR / "builder_cache"
SCRAPER_CACHE_DIR = CACHE_DIR / "scraper_cache"

# Timeouts
TIMEOUT_SECONDS = 300
LLM_TIMEOUT = 60
WEB_TIMEOUT = 30

# Cache settings
CACHE_EXPIRY_HOURS = 24
MAX_CACHE_SIZE_MB = 100

def ensure_cache_dirs():
    """Ensure all cache directories exist."""
    for cache_dir in [CACHE_DIR, ROUTER_CACHE_DIR, BUILDER_CACHE_DIR, SCRAPER_CACHE_DIR]:
        cache_dir.mkdir(parents=True, exist_ok=True)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.getenv(key, default)

class Config:
    """Centralized configuration class."""

    @classmethod
    def setup(cls):
        """Setup configuration and ensure directories exist."""
        ensure_cache_dirs()

    @classmethod
    def get_cache_dir(cls, component: str) -> Path:
        """Get cache directory for specific component."""
        cache_map = {
            'router': ROUTER_CACHE_DIR,
            'builder': BUILDER_CACHE_DIR,
            'scraper': SCRAPER_CACHE_DIR
        }
        return cache_map.get(component, CACHE_DIR)