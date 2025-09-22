#!/usr/bin/env python3
"""
Command Handler Module for NRP K8s System
=========================================

Handles execution of Kubernetes commands by routing to appropriate operations.
Integrates with k8s_operations and YAML template systems.
"""

from typing import Tuple, Optional
from ..systems import k8s_operations
from ..systems.nautilus_docs_scraper import get_yaml_examples


def handle_k8s_command(user_input: str) -> Tuple[str, bool]:
    """
    Execute K8s operations using enhanced tool calling system.

    Args:
        user_input: User command string

    Returns:
        Tuple of (result_message, success_flag)
    """
    try:
        print("[*] Executing K8s command...")
        user_input_lower = user_input.lower()

        # Handle YAML template commands first
        if _is_yaml_command(user_input_lower):
            return _handle_yaml_commands(user_input_lower)

        # Handle list/get/show commands
        if _is_list_command(user_input_lower):
            return _handle_list_commands(user_input_lower)

        # Handle describe commands
        if _is_describe_command(user_input_lower):
            return _handle_describe_commands(user_input_lower)

        # Handle logs command
        if "logs" in user_input_lower:
            return _handle_logs_command(user_input)

        # Handle create/apply commands
        if any(cmd in user_input_lower for cmd in ["create", "apply"]):
            return _handle_create_commands(user_input)

        # Default: try K8s tool caller for complex operations
        return _handle_complex_k8s_operation(user_input)

    except Exception as e:
        error_msg = f"Error executing K8s command: {str(e)}"
        print(f"[!] {error_msg}")
        return error_msg, False


def _is_yaml_command(user_input: str) -> bool:
    """Check if command is related to YAML templates."""
    return "yaml" in user_input and ("show" in user_input or "list" in user_input)


def _is_list_command(user_input: str) -> bool:
    """Check if command is a list/get/show operation."""
    return any(cmd in user_input for cmd in ["list", "get", "show"]) and "yaml" not in user_input


def _is_describe_command(user_input: str) -> bool:
    """Check if command is a describe operation."""
    return "describe" in user_input


def _handle_yaml_commands(user_input: str) -> Tuple[str, bool]:
    """Handle YAML template related commands."""
    if "examples" in user_input:
        return _show_yaml_examples(user_input)
    elif "templates" in user_input:
        return _list_yaml_templates()
    else:
        return "Use 'show yaml examples' or 'list yaml templates' to see available templates.", True


def _show_yaml_examples(user_input: str) -> Tuple[str, bool]:
    """Show YAML examples, optionally filtered by category."""
    # Extract category if specified
    category = None
    words = user_input.split()
    if len(words) > 3:  # "show yaml examples <category>"
        category = words[3]

    examples = get_yaml_examples(category=category)
    if not examples:
        return "No YAML examples found. Try running the scraper to collect examples.", True

    result = f"Available YAML examples ({len(examples)} found):\n\n"
    for i, example in enumerate(examples[:5], 1):  # Show first 5
        result += f"{i}. {example.title}\n"
        result += f"   Category: {example.category} | Type: {example.resource_type} | Complexity: {example.complexity}\n"
        result += f"   Description: {example.description}\n"
        result += f"   Tags: {', '.join(example.tags)}\n"
        result += f"   Source: {example.source_url}\n\n"

    if len(examples) > 5:
        result += f"... and {len(examples) - 5} more examples available.\n"

    return result, True


def _list_yaml_templates() -> Tuple[str, bool]:
    """List YAML templates grouped by category."""
    examples = get_yaml_examples()
    if not examples:
        return "No YAML templates available. Run the scraper to collect examples.", True

    # Group by category
    categories = {}
    for example in examples:
        if example.category not in categories:
            categories[example.category] = []
        categories[example.category].append(example)

    result = "YAML Templates by Category:\n\n"
    for category, cat_examples in categories.items():
        result += f"[{category.upper()}]:\n"
        for example in cat_examples:
            result += f"  - {example.title} ({example.resource_type}) - {example.complexity}\n"
        result += "\n"

    return result, True


def _handle_list_commands(user_input: str) -> Tuple[str, bool]:
    """Handle list/get/show commands for K8s resources."""
    if "pod" in user_input:
        result = k8s_operations.list_pods()
        return f"Pods in namespace 'gsoc':\n{result}", True
    elif "service" in user_input:
        result = k8s_operations.list_services()
        return f"Services in namespace 'gsoc':\n{result}", True
    elif "deployment" in user_input:
        result = k8s_operations.list_deployments()
        return f"Deployments in namespace 'gsoc':\n{result}", True
    elif "job" in user_input:
        result = k8s_operations.list_jobs()
        return f"Jobs in namespace 'gsoc':\n{result}", True
    elif "configmap" in user_input:
        result = k8s_operations.list_configmaps()
        return f"ConfigMaps in namespace 'gsoc':\n{result}", True
    elif "secret" in user_input:
        result = k8s_operations.list_secrets()
        return f"Secrets in namespace 'gsoc':\n{result}", True
    elif "pvc" in user_input or "volume" in user_input:
        result = k8s_operations.list_pvcs()
        return f"PVCs in namespace 'gsoc':\n{result}", True
    else:
        # General list command
        result = k8s_operations.list_all_resources()
        return f"All resources in namespace 'gsoc':\n{result}", True


def _handle_describe_commands(user_input: str) -> Tuple[str, bool]:
    """Handle describe commands for K8s resources."""
    words = user_input.split()
    if len(words) < 2:
        return "Please specify resource type and name for describe command.", False

    # Try to extract resource type and name
    resource_type = None
    resource_name = None

    for i, word in enumerate(words):
        if word.lower() == "describe" and i + 1 < len(words):
            resource_type = words[i + 1]
            if i + 2 < len(words):
                resource_name = words[i + 2]
            break

    if not resource_type:
        return "Please specify resource type to describe.", False

    try:
        if resource_name:
            result = k8s_operations.describe_resource(resource_type, resource_name)
        else:
            result = k8s_operations.describe_resource(resource_type)
        return f"Description of {resource_type}:\n{result}", True
    except Exception as e:
        return f"Error describing {resource_type}: {str(e)}", False


def _handle_logs_command(user_input: str) -> Tuple[str, bool]:
    """Handle logs command for pods."""
    words = user_input.split()
    pod_name = None

    # Extract pod name from command
    for i, word in enumerate(words):
        if word.lower() == "logs" and i + 1 < len(words):
            pod_name = words[i + 1]
            break

    if not pod_name:
        return "Please specify pod name for logs command.", False

    try:
        result = k8s_operations.get_pod_logs(pod_name)
        return f"Logs for pod '{pod_name}':\n{result}", True
    except Exception as e:
        return f"Error getting logs for pod '{pod_name}': {str(e)}", False


def _handle_create_commands(user_input: str) -> Tuple[str, bool]:
    """Handle create/apply commands."""
    # For now, return guidance on how to create resources
    return ("To create resources, use YAML templates. Try 'show yaml examples' to see available templates, "
            "or use the builder for interactive resource creation."), True


def _handle_complex_k8s_operation(user_input: str) -> Tuple[str, bool]:
    """Handle complex operations using K8s tool caller."""
    try:
        from ..systems.enhanced_k8s_tools import K8sToolCaller
        tool_caller = K8sToolCaller()
        result = tool_caller.execute_k8s_operation(user_input)
        return result, True
    except Exception as e:
        return f"Error executing K8s operation: {str(e)}", False


def get_supported_commands() -> list:
    """Get list of supported K8s commands."""
    return [
        "list pods/services/deployments/jobs/configmaps/secrets/pvcs",
        "get <resource>",
        "show <resource>",
        "describe <resource> [name]",
        "logs <pod_name>",
        "show yaml examples [category]",
        "list yaml templates"
    ]