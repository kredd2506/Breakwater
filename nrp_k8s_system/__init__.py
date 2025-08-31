"""
NRP K8s System
===============

Intelligent NRP + Kubernetes routing and management system.

This package provides:
- Intelligent routing between K8s commands and documentation queries
- NRP LLM integration for comprehensive guidance
- Kubernetes operations and cluster management
- Web-based information extraction and search
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .intelligent_router import intelligent_route, interactive_mode
from .core.nrp_init import init_chat_model

__all__ = ["intelligent_route", "interactive_mode", "init_chat_model"]