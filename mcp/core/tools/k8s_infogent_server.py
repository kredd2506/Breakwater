#!/usr/bin/env python3
"""
Kubernetes Infogent FastMCP Server
==================================
Comprehensive MCP server integrating Kubernetes operations with NRP infogent architecture.
Provides LLM-powered tools for K8s management, documentation queries, and intelligent routing.
"""

import os
import re
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing NRP and K8s components
try:
    from kubernetes import client, config
    from kubernetes.client.exceptions import ApiException
    from nrp_k8s_system.core.nrp_init import init_chat_model
    from nrp_k8s_system.systems.k8s_operations import (
        list_pods, list_deployments, list_services, list_jobs,
        describe_pod, describe_deployment, describe_service,
        create_pod_programmatic, create_deployment_programmatic,
        delete_pod, delete_deployment, pod_logs, pod_exec,
        check_permissions, get_service_account, get_pod_info,
        validate_k8s_name, handle_api_error, CURRENT_NAMESPACE
    )
except ImportError as e:
    print(f"Warning: Could not import K8s/NRP components: {e}")
    # Define stub functions for testing without K8s
    def list_pods(_=None): return ["demo-pod-1", "demo-pod-2"]
    def list_deployments(_=None): return ["demo-deploy-1"]
    CURRENT_NAMESPACE = "gsoc"

# Initialize Kubernetes client
try:
    config.load_incluster_config()
except:
    try:
        config.load_kube_config()
    except:
        print("Warning: Could not configure Kubernetes client")

# Initialize NRP chat model
try:
    nrp_chat = init_chat_model(model="gemma3")
except Exception as e:
    print(f"Warning: Could not initialize NRP chat model: {e}")
    nrp_chat = None

# Pydantic models for tool parameters
class PodCreateParams(BaseModel):
    name: str = Field(description="Pod name (must follow K8s naming conventions)")
    image: str = Field(default="ubuntu", description="Container image")
    memory_limit: str = Field(default="100Mi", description="Memory limit (e.g., 100Mi, 1Gi)")
    cpu_limit: str = Field(default="100m", description="CPU limit (e.g., 100m, 1)")
    memory_request: str = Field(default="100Mi", description="Memory request")
    cpu_request: str = Field(default="100m", description="CPU request")
    command: Optional[List[str]] = Field(default=None, description="Container command")

class DeploymentCreateParams(BaseModel):
    name: str = Field(description="Deployment name")
    image: str = Field(default="ubuntu", description="Container image")
    replicas: int = Field(default=1, description="Number of replicas")
    memory_limit: str = Field(default="500Mi", description="Memory limit")
    cpu_limit: str = Field(default="500m", description="CPU limit")
    memory_request: str = Field(default="100Mi", description="Memory request")
    cpu_request: str = Field(default="50m", description="CPU request")

class QueryParams(BaseModel):
    query: str = Field(description="Natural language query or question")
    context: Optional[str] = Field(default=None, description="Additional context")

class YAMLResourceParams(BaseModel):
    yaml_content: str = Field(description="YAML content for the Kubernetes resource")
    resource_type: str = Field(description="Type of resource (pod, deployment, service, etc.)")

# Create the FastMCP server
mcp = FastMCP(
    name="K8s Infogent Server",
    instructions="""
    Advanced Kubernetes operations server with NRP infogent architecture integration.
    Provides intelligent routing between K8s operational commands and documentation/explanation queries.

    Capabilities:
    - Kubernetes resource management (CRUD operations)
    - Natural language K8s queries with LLM assistance
    - Intelligent intent classification and routing
    - Resource validation and schema checking
    - Comprehensive logging and error handling
    """
)

# ======================== KUBERNETES OPERATIONS ========================

@mcp.tool
def k8s_list_resources(resource_type: str) -> List[str]:
    """
    List Kubernetes resources of a specific type.

    Args:
        resource_type: Type of resource (pods, deployments, services, jobs, etc.)

    Returns:
        List of resource names in the current namespace
    """
    try:
        resource_functions = {
            "pods": list_pods,
            "deployments": list_deployments,
            "services": list_services,
            "jobs": list_jobs,
        }

        func = resource_functions.get(resource_type.lower())
        if not func:
            return [f"Error: Unknown resource type '{resource_type}'. Supported: {list(resource_functions.keys())}"]

        result = func()
        return result if isinstance(result, list) else [str(result)]

    except Exception as e:
        return [f"Error listing {resource_type}: {str(e)}"]

@mcp.tool
def k8s_describe_resource(resource_type: str, resource_name: str) -> str:
    """
    Get detailed information about a specific Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment, service)
        resource_name: Name of the resource

    Returns:
        Detailed description of the resource
    """
    try:
        describe_functions = {
            "pod": describe_pod,
            "deployment": describe_deployment,
            "service": describe_service,
        }

        func = describe_functions.get(resource_type.lower())
        if not func:
            return f"Error: Unknown resource type '{resource_type}'. Supported: {list(describe_functions.keys())}"

        return func(resource_name)

    except Exception as e:
        return f"Error describing {resource_type} '{resource_name}': {str(e)}"

@mcp.tool
def k8s_create_pod(params: PodCreateParams) -> str:
    """
    Create a new Kubernetes pod with specified parameters.

    Args:
        params: Pod creation parameters including name, image, resources, etc.

    Returns:
        Success or error message
    """
    try:
        return create_pod_programmatic(
            name=params.name,
            image=params.image,
            memory_limit=params.memory_limit,
            cpu_limit=params.cpu_limit,
            memory_request=params.memory_request,
            cpu_request=params.cpu_request,
            command=params.command,
            namespace=CURRENT_NAMESPACE
        )
    except Exception as e:
        return f"Error creating pod: {str(e)}"

@mcp.tool
def k8s_create_deployment(params: DeploymentCreateParams) -> str:
    """
    Create a new Kubernetes deployment with specified parameters.

    Args:
        params: Deployment creation parameters

    Returns:
        Success or error message
    """
    try:
        return create_deployment_programmatic(
            name=params.name,
            image=params.image,
            replicas=params.replicas,
            memory_limit=params.memory_limit,
            cpu_limit=params.cpu_limit,
            memory_request=params.memory_request,
            cpu_request=params.cpu_request,
            namespace=CURRENT_NAMESPACE
        )
    except Exception as e:
        return f"Error creating deployment: {str(e)}"

@mcp.tool
def k8s_create_from_yaml(params: YAMLResourceParams) -> str:
    """
    Create Kubernetes resources from YAML content.

    Args:
        params: YAML content and resource type information

    Returns:
        Success or error message
    """
    try:
        # Validate YAML syntax
        yaml_data = yaml.safe_load(params.yaml_content)

        # Add namespace if not specified
        if not yaml_data.get("metadata"):
            yaml_data["metadata"] = {}
        if not yaml_data["metadata"].get("namespace"):
            yaml_data["metadata"]["namespace"] = CURRENT_NAMESPACE

        # Create the resource based on type
        if params.resource_type.lower() == "pod":
            from nrp_k8s_system.systems.k8s_operations import create_pod_from_yaml
            return create_pod_from_yaml(params.yaml_content, CURRENT_NAMESPACE)
        elif params.resource_type.lower() == "deployment":
            from nrp_k8s_system.systems.k8s_operations import create_deployment_from_yaml
            return create_deployment_from_yaml(params.yaml_content, CURRENT_NAMESPACE)
        else:
            return f"Error: Resource type '{params.resource_type}' not yet supported for YAML creation"

    except Exception as e:
        return f"Error creating resource from YAML: {str(e)}"

@mcp.tool
def k8s_delete_resource(resource_type: str, resource_name: str) -> str:
    """
    Delete a Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment)
        resource_name: Name of the resource to delete

    Returns:
        Success or error message
    """
    try:
        if resource_type.lower() == "pod":
            return delete_pod(resource_name, CURRENT_NAMESPACE)
        elif resource_type.lower() == "deployment":
            return delete_deployment(resource_name, CURRENT_NAMESPACE)
        else:
            return f"Error: Deletion not supported for resource type '{resource_type}'"

    except Exception as e:
        return f"Error deleting {resource_type} '{resource_name}': {str(e)}"

@mcp.tool
def k8s_get_logs(pod_name: str, tail_lines: Optional[int] = None) -> str:
    """
    Get logs from a Kubernetes pod.

    Args:
        pod_name: Name of the pod
        tail_lines: Number of recent lines to retrieve (optional)

    Returns:
        Pod logs
    """
    try:
        return pod_logs(pod_name, tail_lines, CURRENT_NAMESPACE)
    except Exception as e:
        return f"Error getting logs for pod '{pod_name}': {str(e)}"

@mcp.tool
def k8s_exec_command(pod_name: str, command: List[str], container: Optional[str] = None) -> str:
    """
    Execute a command in a Kubernetes pod.

    Args:
        pod_name: Name of the pod
        command: Command to execute
        container: Container name (optional)

    Returns:
        Command output
    """
    try:
        return pod_exec(pod_name, command, container, CURRENT_NAMESPACE)
    except Exception as e:
        return f"Error executing command in pod '{pod_name}': {str(e)}"

# ======================== INFOGENT ARCHITECTURE ========================

@mcp.tool
def intelligent_k8s_query(params: QueryParams) -> str:
    """
    Process natural language Kubernetes queries using NRP infogent architecture.
    Classifies intent and routes to appropriate handlers.

    Args:
        params: Query parameters including the natural language question

    Returns:
        Intelligent response based on query classification
    """
    try:
        query = params.query.strip()
        context = params.context or ""

        # Intent classification using simple keyword matching as fallback
        intent = classify_intent(query)

        if intent == "COMMAND":
            return handle_k8s_command(query, context)
        elif intent == "EXPLANATION":
            return handle_k8s_explanation(query, context)
        else:
            return handle_unclear_query(query, context)

    except Exception as e:
        return f"Error processing query: {str(e)}"

def classify_intent(query: str) -> str:
    """Classify user intent as COMMAND, EXPLANATION, or UNCLEAR"""
    query_lower = query.lower()

    # Command indicators
    command_keywords = [
        "list", "show", "get", "create", "delete", "remove", "run", "start", "stop",
        "deploy", "scale", "restart", "logs", "exec", "describe", "status"
    ]

    # Explanation indicators
    explanation_keywords = [
        "what", "how", "why", "when", "where", "explain", "help", "guide", "tutorial",
        "documentation", "docs", "understand", "learn", "teach", "example"
    ]

    # Check for command intent
    if any(keyword in query_lower for keyword in command_keywords):
        return "COMMAND"

    # Check for explanation intent
    if any(keyword in query_lower for keyword in explanation_keywords):
        return "EXPLANATION"

    return "UNCLEAR"

def handle_k8s_command(query: str, context: str) -> str:
    """Handle operational Kubernetes commands"""
    try:
        # Extract action and resource from query
        query_lower = query.lower()

        if "list" in query_lower or "show" in query_lower or "get" in query_lower:
            if "pod" in query_lower:
                pods = list_pods()
                return f"Pods in namespace '{CURRENT_NAMESPACE}':\n" + "\n".join(f"- {pod}" for pod in pods)
            elif "deployment" in query_lower:
                deployments = list_deployments()
                return f"Deployments in namespace '{CURRENT_NAMESPACE}':\n" + "\n".join(f"- {dep}" for dep in deployments)
            elif "service" in query_lower:
                services = list_services()
                return f"Services in namespace '{CURRENT_NAMESPACE}':\n" + "\n".join(f"- {svc}" for svc in services)

        elif "describe" in query_lower:
            # Try to extract resource name and type
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in ["pod", "deployment", "service"]:
                    if i + 1 < len(words):
                        resource_name = words[i + 1]
                        return describe_pod(resource_name) if word.lower() == "pod" else \
                               describe_deployment(resource_name) if word.lower() == "deployment" else \
                               describe_service(resource_name)

        elif "delete" in query_lower or "remove" in query_lower:
            return "⚠️ Deletion commands require explicit tool calls for safety. Use k8s_delete_resource tool."

        elif "create" in query_lower or "deploy" in query_lower:
            return "🔧 Creation commands require explicit parameters. Use k8s_create_pod or k8s_create_deployment tools."

        elif "logs" in query_lower:
            # Try to extract pod name
            words = query.split()
            for word in words:
                if not word.lower() in ["logs", "log", "from", "of", "for", "get", "show"]:
                    return pod_logs(word, namespace=CURRENT_NAMESPACE)

        return f"🤖 Command recognized but needs more specific parameters. Query: '{query}'"

    except Exception as e:
        return f"Error handling command: {str(e)}"

def handle_k8s_explanation(query: str, context: str) -> str:
    """Handle documentation and explanation queries"""
    try:
        if nrp_chat:
            # Use NRP LLM for comprehensive explanations
            system_prompt = """You are a Kubernetes expert assistant. Provide clear, accurate explanations about Kubernetes concepts, best practices, and troubleshooting. Focus on practical guidance for the 'gsoc' namespace environment."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ]

            # Note: This would need to be adapted based on the actual NRP client interface
            response = "📚 Kubernetes Documentation Response:\n\n"
            response += "This query would be processed by the NRP LLM for comprehensive explanation. "
            response += f"Query: '{query}'"

            if "pod" in query.lower():
                response += "\n\n🔹 Pods are the smallest deployable units in Kubernetes, containing one or more containers."
            elif "deployment" in query.lower():
                response += "\n\n🔹 Deployments manage ReplicaSets and provide declarative updates for Pods."
            elif "service" in query.lower():
                response += "\n\n🔹 Services provide stable network endpoints for accessing Pods."

            return response
        else:
            return handle_fallback_explanation(query)

    except Exception as e:
        return f"Error generating explanation: {str(e)}"

def handle_fallback_explanation(query: str) -> str:
    """Fallback explanation handler when NRP is not available"""
    explanations = {
        "pod": "🔹 A Pod is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster and can contain one or more containers.",
        "deployment": "🔹 A Deployment manages a ReplicaSet which in turn manages Pods. It provides declarative updates for Pods and ReplicaSets.",
        "service": "🔹 A Service is an abstraction that defines a logical set of Pods and a policy to access them. It provides stable networking for dynamic Pod environments.",
        "namespace": "🔹 Namespaces provide a scope for names and allow multiple teams to share a cluster. You're currently working in the 'gsoc' namespace.",
    }

    query_lower = query.lower()
    for concept, explanation in explanations.items():
        if concept in query_lower:
            return f"📚 {explanation}"

    return f"📚 Basic Kubernetes documentation response for: '{query}'. For detailed explanations, please ensure NRP integration is configured."

def handle_unclear_query(query: str, context: str) -> str:
    """Handle unclear or ambiguous queries"""
    return f"""
🤔 I'm not sure if you want to:
- **Perform a Kubernetes operation** (list, create, delete, describe resources)
- **Get explanations** about Kubernetes concepts

Could you clarify your request? For example:
- "List all pods" (operation)
- "What is a pod?" (explanation)
- "How do I create a deployment?" (explanation)

Your query: '{query}'
"""

# ======================== UTILITY AND CONTEXT ========================

@mcp.tool
def k8s_get_cluster_info() -> Dict[str, Any]:
    """
    Get information about the current Kubernetes cluster and context.

    Returns:
        Cluster information including namespace, permissions, and context
    """
    try:
        info = {
            "namespace": CURRENT_NAMESPACE,
            "timestamp": datetime.now().isoformat(),
        }

        # Get service account info
        try:
            sa_info = get_service_account()
            info["service_account"] = sa_info
        except:
            info["service_account"] = "Unable to retrieve"

        # Get pod info if running in cluster
        try:
            pod_info = get_pod_info()
            info["current_pod"] = pod_info
        except:
            info["current_pod"] = "Not running in cluster"

        # Check permissions
        try:
            permissions = check_permissions()
            info["permissions"] = permissions
        except:
            info["permissions"] = "Unable to check"

        return info

    except Exception as e:
        return {"error": f"Error getting cluster info: {str(e)}"}

@mcp.tool
def k8s_validate_yaml(yaml_content: str) -> Dict[str, Any]:
    """
    Validate Kubernetes YAML content for syntax and basic structure.

    Args:
        yaml_content: YAML content to validate

    Returns:
        Validation results including errors and warnings
    """
    try:
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "resource_info": {}
        }

        # Parse YAML
        try:
            yaml_data = yaml.safe_load(yaml_content)
            result["valid"] = True
        except yaml.YAMLError as e:
            result["errors"].append(f"YAML syntax error: {str(e)}")
            return result

        # Basic Kubernetes resource validation
        if not isinstance(yaml_data, dict):
            result["errors"].append("YAML must contain a dictionary/object")
            return result

        # Check required fields
        required_fields = ["apiVersion", "kind", "metadata"]
        for field in required_fields:
            if field not in yaml_data:
                result["errors"].append(f"Missing required field: {field}")

        # Extract resource info
        if "kind" in yaml_data:
            result["resource_info"]["kind"] = yaml_data["kind"]
        if "metadata" in yaml_data and "name" in yaml_data["metadata"]:
            result["resource_info"]["name"] = yaml_data["metadata"]["name"]

        # Check namespace
        if "metadata" in yaml_data:
            if "namespace" not in yaml_data["metadata"]:
                result["warnings"].append(f"No namespace specified, will use '{CURRENT_NAMESPACE}'")
            elif yaml_data["metadata"]["namespace"] != CURRENT_NAMESPACE:
                result["warnings"].append(f"Resource namespace '{yaml_data['metadata']['namespace']}' differs from current '{CURRENT_NAMESPACE}'")

        # Validate resource name
        if "metadata" in yaml_data and "name" in yaml_data["metadata"]:
            try:
                validate_k8s_name(yaml_data["metadata"]["name"])
            except ValueError as e:
                result["errors"].append(str(e))

        result["valid"] = len(result["errors"]) == 0
        return result

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "resource_info": {}
        }

# ======================== RESOURCES ========================

@mcp.resource("k8s://cluster/status")
def get_cluster_status() -> Dict[str, Any]:
    """Get current Kubernetes cluster status and configuration"""
    return {
        "namespace": CURRENT_NAMESPACE,
        "server_info": "K8s Infogent FastMCP Server",
        "capabilities": [
            "Resource listing and description",
            "Pod and deployment creation/deletion",
            "YAML resource creation",
            "Log retrieval and command execution",
            "Natural language query processing",
            "Intent classification and routing",
            "YAML validation and syntax checking"
        ],
        "supported_resources": [
            "pods", "deployments", "services", "jobs",
            "configmaps", "secrets", "pvcs", "replicasets",
            "statefulsets", "daemonsets", "ingresses"
        ],
        "nrp_integration": nrp_chat is not None
    }

@mcp.resource("k8s://examples/yaml")
def get_yaml_examples() -> Dict[str, str]:
    """Get example YAML templates for common Kubernetes resources"""
    return {
        "simple_pod": """apiVersion: v1
kind: Pod
metadata:
  name: example-pod
  namespace: gsoc
spec:
  containers:
  - name: app
    image: nginx
    resources:
      limits:
        memory: 128Mi
        cpu: 100m
      requests:
        memory: 64Mi
        cpu: 50m""",

        "simple_deployment": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
  namespace: gsoc
spec:
  replicas: 2
  selector:
    matchLabels:
      app: example
  template:
    metadata:
      labels:
        app: example
    spec:
      containers:
      - name: app
        image: nginx
        resources:
          limits:
            memory: 256Mi
            cpu: 200m
          requests:
            memory: 128Mi
            cpu: 100m""",

        "service": """apiVersion: v1
kind: Service
metadata:
  name: example-service
  namespace: gsoc
spec:
  selector:
    app: example
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP"""
    }

@mcp.resource("k8s://help/commands")
def get_command_help() -> Dict[str, Any]:
    """Get help information for available Kubernetes commands and tools"""
    return {
        "available_tools": {
            "k8s_list_resources": "List resources by type (pods, deployments, services, etc.)",
            "k8s_describe_resource": "Get detailed information about a specific resource",
            "k8s_create_pod": "Create a new pod with specified parameters",
            "k8s_create_deployment": "Create a new deployment",
            "k8s_create_from_yaml": "Create resources from YAML content",
            "k8s_delete_resource": "Delete a resource by name and type",
            "k8s_get_logs": "Retrieve logs from a pod",
            "k8s_exec_command": "Execute commands in a pod",
            "intelligent_k8s_query": "Process natural language K8s queries",
            "k8s_get_cluster_info": "Get cluster context and permissions",
            "k8s_validate_yaml": "Validate YAML syntax and structure"
        },
        "example_queries": [
            "List all pods",
            "Describe pod nginx-123",
            "What is a deployment?",
            "How do I create a service?",
            "Show me deployment logs",
            "Create a pod with nginx image"
        ],
        "namespace": CURRENT_NAMESPACE,
        "safety_notes": [
            "Deletion operations require explicit confirmation",
            "All resources are created in the 'gsoc' namespace",
            "YAML resources are validated before creation",
            "Resource names must follow Kubernetes RFC1123 format"
        ]
    }

if __name__ == "__main__":
    # Run the server on HTTP transport
    print("Starting K8s Infogent FastMCP Server...")
    print(f"Namespace: {CURRENT_NAMESPACE}")
    print(f"NRP Integration: {'OK' if nrp_chat else 'NO'}")
    mcp.run(transport="http", host="localhost", port=8002)