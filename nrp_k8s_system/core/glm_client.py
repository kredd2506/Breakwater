#!/usr/bin/env python3
"""
GLM-V Client Configuration Module
================================

Provides GLM-V (65,536 tokens, tool calling, multimodal) client setup
for enhanced intent classification and tool calling capabilities.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from openai import OpenAI
from langchain_openai import ChatOpenAI


@dataclass
class GLMConfig:
    """Configuration for GLM-V model."""
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    model: str = "glm-4v-plus"
    api_key: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.3  # Lower temperature for more consistent intent classification
    timeout: int = 60


class GLMVClient:
    """
    GLM-V client for advanced intent classification with tool calling.

    Features:
    - Tool calling capabilities for command discovery
    - Multimodal support (vision, video)
    - 65,536 token context window
    - GPT-4o level multimodal performance
    """

    def __init__(self, config: Optional[GLMConfig] = None):
        self.config = config or self._load_config()
        self.client = self._init_client()

    def _load_config(self) -> GLMConfig:
        """Load GLM-V configuration from environment."""
        # Use your existing environment variables
        api_key = os.getenv("nrp_key_2")
        base_url = os.getenv("nrp_base_url", "https://llm.nrp-nautilus.io/v1")
        model = os.getenv("nrp_model2")

        return GLMConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=int(os.getenv("GLM_MAX_TOKENS", "8192")),
            temperature=float(os.getenv("GLM_TEMPERATURE", "0.3"))  # Default for intent classification
        )

    def _init_client(self) -> ChatOpenAI:
        """Initialize GLM-V client using LangChain OpenAI wrapper."""
        if not self.config.api_key:
            raise ValueError("nrp_key_2 environment variable is required for GLM-V")

        return ChatOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout
        )

    def get_native_client(self) -> OpenAI:
        """Get native OpenAI client for direct tool calling."""
        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )

    def is_available(self) -> bool:
        """Check if GLM-V client is properly configured."""
        return bool(self.config.api_key)

    def test_connection(self) -> bool:
        """Test connection to GLM-V API."""
        try:
            response = self.client.invoke("Test connection")
            return bool(response)
        except Exception as e:
            print(f"[!] GLM-V connection test failed: {e}")
            return False


def init_glm_client() -> Optional[GLMVClient]:
    """
    Initialize GLM-V client with error handling.

    Returns:
        GLMVClient instance if configured, None otherwise
    """
    try:
        client = GLMVClient()
        if not client.is_available():
            print("[!] GLM-V not configured (missing GLM_API_KEY)")
            return None
        return client
    except Exception as e:
        print(f"[!] Failed to initialize GLM-V client: {e}")
        return None


# Tool definitions for GLM-V function calling
K8S_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_k8s_resources",
            "description": "List Kubernetes resources (pods, services, deployments, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["pods", "services", "deployments", "jobs", "configmaps", "secrets", "pvcs"],
                        "description": "Type of Kubernetes resource to list"
                    },
                    "namespace": {
                        "type": "string",
                        "default": "gsoc",
                        "description": "Kubernetes namespace to query"
                    }
                },
                "required": ["resource_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_k8s_resource",
            "description": "Get detailed information about a specific Kubernetes resource",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["pod", "service", "deployment", "job", "configmap", "secret", "pvc"],
                        "description": "Type of Kubernetes resource"
                    },
                    "resource_name": {
                        "type": "string",
                        "description": "Name of the specific resource"
                    },
                    "namespace": {
                        "type": "string",
                        "default": "gsoc",
                        "description": "Kubernetes namespace"
                    }
                },
                "required": ["resource_type", "resource_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Retrieve logs from a Kubernetes pod",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod to get logs from"
                    },
                    "namespace": {
                        "type": "string",
                        "default": "gsoc",
                        "description": "Kubernetes namespace"
                    },
                    "lines": {
                        "type": "integer",
                        "default": 100,
                        "description": "Number of recent log lines to retrieve"
                    }
                },
                "required": ["pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_nrp_docs",
            "description": "Search NRP/Nautilus documentation for explanations and guidance",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for documentation"
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["gpu", "storage", "networking", "security", "best-practices", "troubleshooting"],
                        "description": "Documentation topic category"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


CLARIFICATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "request_clarification",
            "description": "Request clarification from user when intent is unclear",
            "parameters": {
                "type": "object",
                "properties": {
                    "clarification_type": {
                        "type": "string",
                        "enum": ["ambiguous_command", "missing_resource_name", "unclear_intent", "multiple_possibilities"],
                        "description": "Type of clarification needed"
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Suggested clarifications or examples"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for the clarification request"
                    }
                },
                "required": ["clarification_type", "suggestions"]
            }
        }
    }
]