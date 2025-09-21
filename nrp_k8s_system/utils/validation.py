#!/usr/bin/env python3
"""
Common validation utilities for NRP K8s System
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

def is_valid_k8s_name(name: str) -> bool:
    """Validate Kubernetes resource name."""
    if not name or len(name) > 253:
        return False
    # K8s names must be lowercase alphanumeric, hyphens, dots
    pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
    return bool(re.match(pattern, name))

def is_valid_namespace(namespace: str) -> bool:
    """Validate Kubernetes namespace name."""
    if not namespace or len(namespace) > 63:
        return False
    # Namespace names are more restrictive
    pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    return bool(re.match(pattern, namespace))

def validate_json_structure(data: Union[str, dict], required_keys: List[str] = None) -> bool:
    """Validate JSON structure and required keys."""
    try:
        if isinstance(data, str):
            parsed = json.loads(data)
        else:
            parsed = data

        if required_keys:
            return all(key in parsed for key in required_keys)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def sanitize_input(user_input: str, max_length: int = 1000) -> str:
    """Sanitize user input for safety."""
    if not user_input:
        return ""

    # Remove potential command injection characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>']
    sanitized = user_input
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # Limit length
    return sanitized[:max_length].strip()

def validate_yaml_keys(yaml_data: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """Validate YAML data has required keys. Returns missing keys."""
    if not isinstance(yaml_data, dict):
        return required_keys

    missing = []
    for key in required_keys:
        if key not in yaml_data:
            missing.append(key)
    return missing

def is_safe_path(path: Union[str, Path]) -> bool:
    """Check if path is safe (no directory traversal)."""
    try:
        path_obj = Path(path).resolve()
        # Check for directory traversal attempts
        if '..' in str(path_obj):
            return False
        return True
    except (OSError, ValueError):
        return False