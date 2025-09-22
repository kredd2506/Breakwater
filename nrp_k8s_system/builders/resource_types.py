#!/usr/bin/env python3
"""
Resource Types and Base Classes for K8s Builder
===============================================

Defines Kubernetes resource types, enums, and base data structures
used throughout the builder system.
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass, field


class ResourceType(Enum):
    """Supported Kubernetes resource types."""
    NAMESPACE = "Namespace"
    SERVICE_ACCOUNT = "ServiceAccount"
    CONFIG_MAP = "ConfigMap"
    SECRET = "Secret"
    PVC = "PersistentVolumeClaim"
    DEPLOYMENT = "Deployment"
    STATEFUL_SET = "StatefulSet"
    JOB = "Job"
    CRON_JOB = "CronJob"
    DAEMON_SET = "DaemonSet"
    SERVICE = "Service"
    INGRESS = "Ingress"
    HPA = "HorizontalPodAutoscaler"
    PDB = "PodDisruptionBudget"
    NETWORK_POLICY = "NetworkPolicy"
    SERVICE_MONITOR = "ServiceMonitor"


class BuilderStep(Enum):
    """Steps in the manifest building process."""
    REQUIREMENTS_GATHERING = "requirements_gathering"
    POLICY_VALIDATION = "policy_validation"
    RESOURCE_PLANNING = "resource_planning"
    PARALLEL_GENERATION = "parallel_generation"
    VALIDATION_AND_REVIEW = "validation_and_review"
    OUTPUT_GENERATION = "output_generation"


class ComplexityLevel(Enum):
    """Complexity levels for generated manifests."""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ValidationLevel(Enum):
    """Validation strictness levels."""
    BASIC = "basic"
    STRICT = "strict"
    ENTERPRISE = "enterprise"


@dataclass
class KubernetesSpec:
    """Comprehensive Kubernetes specification following kube_builder.txt design."""

    # Application metadata
    app: Dict[str, Any] = field(default_factory=dict)

    # RBAC configuration
    rbac: Dict[str, Any] = field(default_factory=dict)

    # Configuration and secrets
    config: Dict[str, Any] = field(default_factory=dict)

    # Storage configuration
    storage: Dict[str, Any] = field(default_factory=dict)

    # Workload configuration
    workload: Dict[str, Any] = field(default_factory=dict)

    # Service configuration
    service: Dict[str, Any] = field(default_factory=dict)

    # Ingress configuration
    ingress: Dict[str, Any] = field(default_factory=dict)

    # Autoscaling configuration
    autoscaling: Dict[str, Any] = field(default_factory=dict)

    # Availability configuration
    availability: Dict[str, Any] = field(default_factory=dict)

    # Network configuration
    network: Dict[str, Any] = field(default_factory=dict)

    # Monitoring configuration
    monitoring: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildContext:
    """Context information for the build process."""
    namespace: str = "gsoc"
    complexity_level: ComplexityLevel = ComplexityLevel.INTERMEDIATE
    validation_level: ValidationLevel = ValidationLevel.STRICT
    enable_monitoring: bool = True
    enable_security: bool = True
    resource_quotas: Dict[str, str] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of manifest generation."""
    success: bool
    yaml_content: str = ""
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyViolation:
    """Represents a policy violation found during validation."""
    severity: str  # "error", "warning", "info"
    message: str
    resource_type: str
    field_path: str = ""
    suggestion: str = ""


def get_resource_type_hierarchy() -> Dict[str, list]:
    """Get resource type hierarchy for dependency ordering."""
    return {
        "foundation": [
            ResourceType.NAMESPACE,
            ResourceType.SERVICE_ACCOUNT
        ],
        "configuration": [
            ResourceType.CONFIG_MAP,
            ResourceType.SECRET
        ],
        "storage": [
            ResourceType.PVC
        ],
        "workloads": [
            ResourceType.DEPLOYMENT,
            ResourceType.STATEFUL_SET,
            ResourceType.JOB,
            ResourceType.CRON_JOB,
            ResourceType.DAEMON_SET
        ],
        "networking": [
            ResourceType.SERVICE,
            ResourceType.INGRESS,
            ResourceType.NETWORK_POLICY
        ],
        "management": [
            ResourceType.HPA,
            ResourceType.PDB,
            ResourceType.SERVICE_MONITOR
        ]
    }


def get_default_resource_limits() -> Dict[str, Dict[str, str]]:
    """Get default resource limits for different resource types."""
    return {
        "cpu_intensive": {
            "cpu": "2000m",
            "memory": "4Gi"
        },
        "memory_intensive": {
            "cpu": "500m",
            "memory": "8Gi"
        },
        "gpu_workload": {
            "cpu": "4000m",
            "memory": "16Gi",
            "nvidia.com/gpu": "1"
        },
        "lightweight": {
            "cpu": "100m",
            "memory": "128Mi"
        }
    }