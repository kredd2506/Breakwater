#!/usr/bin/env python3
"""
NRP Anchor-Based Knowledge Base
==============================
Comprehensive knowledge base for NRP Nautilus with exact anchor links and hashtags.
This contains precise links to specific documentation sections for accurate retrieval.
"""

# Complete mapping of NRP documentation with exact anchor links
NRP_DOCUMENTATION_ANCHORS = {
    # GPU Pods Documentation
    "gpu_pods": {
        "base_url": "https://nrp.ai/documentation/userdocs/running/gpu-pods/",
        "sections": {
            "overview": "#_top",
            "running_gpu_pods": "#running-gpu-pods",
            "requesting_special_gpus": "#requesting-special-gpus",
            "requesting_many_gpus": "#requesting-many-gpus",
            "choosing_gpu_type": "#choosing-gpu-type",
            "selecting_cuda_version": "#selecting-cuda-version",
            "adding_shared_memory": "#adding-shared-memory-shm"
        }
    },

    # Getting Started Documentation
    "getting_started": {
        "base_url": "https://nrp.ai/documentation/userdocs/start/getting-started/",
        "sections": {
            "overview": "#_top",
            "get_access_and_login": "#get-access-and-log-in",
            "get_access_deprecated": "#get-access-and-log-in-deprecated",
            "kubectl_access": "#cluster-access-via-kubectl",
            "updating_namespace": "#updating-namespace-membership",
            "use_cluster": "#use-the-cluster",
            "gui_tools": "#gui-tools-for-kubernetes"
        }
    },

    # Cluster Policies Documentation
    "policies": {
        "base_url": "https://nrp.ai/documentation/userdocs/start/policies/",
        "sections": {
            "overview": "#_top",
            "acceptable_use": "#acceptable-use-policy",
            "resource_allocation": "#resource-allocation",
            "usage_violations": "#resource-usage-violations",
            "interactive_use": "#interactive-use-6-hours-max-runtime",
            "batch_jobs": "#batch-jobs",
            "long_idle_pods": "#long-running-idle-pods",
            "workload_purging": "#workloads-purging-2-weeks-max-runtime",
            "requesting_gpus": "#requesting-gpus",
            "data_purging": "#data-purging"
        }
    },

    # Storage Tutorial Documentation
    "storage": {
        "base_url": "https://nrp.ai/documentation/userdocs/tutorial/storage/",
        "sections": {
            "overview": "#_top",
            "prerequisites": "#prerequisites",
            "learning_objectives": "#learning-objectives",
            "storage_types": "#storage-types",
            "create_emptydir": "#create-an-emptydir",
            "start_deployment": "#start-the-deployment",
            "creating_pvc": "#creating-a-persistent-volume-claim",
            "exploring_storage_classes": "#exploring-storageclasses",
            "cleaning_up": "#cleaning-up",
            "end": "#end"
        }
    },

    # Jobs Tutorial Documentation
    "jobs": {
        "base_url": "https://nrp.ai/documentation/userdocs/tutorial/jobs/",
        "sections": {
            "overview": "#_top",
            "prerequisites": "#prerequisites",
            "learning_objectives": "#learning-objectives",
            "the_end": "#the-end"
        }
    },

    # Monitoring Documentation
    "monitoring": {
        "base_url": "https://nrp.ai/documentation/userdocs/running/monitoring/",
        "sections": {
            "overview": "#_top"
        }
    }
}

# Topic-to-anchor mapping for intelligent query routing
TOPIC_ANCHOR_MAPPING = {
    # GPU-related queries
    "gpu": {
        "request": ("gpu_pods", "requesting_special_gpus"),
        "choose": ("gpu_pods", "choosing_gpu_type"),
        "a100": ("gpu_pods", "requesting_special_gpus"),
        "rtx": ("gpu_pods", "choosing_gpu_type"),
        "cuda": ("gpu_pods", "selecting_cuda_version"),
        "memory": ("gpu_pods", "adding_shared_memory"),
        "many": ("gpu_pods", "requesting_many_gpus")
    },

    # Getting started queries
    "start": {
        "access": ("getting_started", "get_access_and_login"),
        "login": ("getting_started", "get_access_and_login"),
        "kubectl": ("getting_started", "kubectl_access"),
        "namespace": ("getting_started", "updating_namespace"),
        "gui": ("getting_started", "gui_tools"),
        "tools": ("getting_started", "gui_tools")
    },

    # Policy queries
    "policy": {
        "resource": ("policies", "resource_allocation"),
        "limit": ("policies", "resource_allocation"),
        "violation": ("policies", "usage_violations"),
        "interactive": ("policies", "interactive_use"),
        "batch": ("policies", "batch_jobs"),
        "idle": ("policies", "long_idle_pods"),
        "purge": ("policies", "workload_purging"),
        "data": ("policies", "data_purging"),
        "aup": ("policies", "acceptable_use")
    },

    # Storage queries
    "storage": {
        "persistent": ("storage", "creating_pvc"),
        "pvc": ("storage", "creating_pvc"),
        "volume": ("storage", "storage_types"),
        "mount": ("storage", "storage_types"),
        "emptydir": ("storage", "create_emptydir"),
        "class": ("storage", "exploring_storage_classes")
    },

    # Job queries
    "job": {
        "batch": ("jobs", "overview"),
        "create": ("jobs", "learning_objectives"),
        "run": ("jobs", "overview"),
        "objective": ("jobs", "learning_objectives")
    },

    # Monitoring queries
    "monitor": {
        "resource": ("monitoring", "overview"),
        "dashboard": ("monitoring", "overview"),
        "grafana": ("monitoring", "overview")
    }
}

# Knowledge content with exact anchor references
NRP_ANCHOR_KNOWLEDGE = {
    # GPU Documentation Content
    "gpu_request_a100": {
        "title": "How to Request A100 GPU on NRP Nautilus",
        "content": """
# How to Request A100 GPU on NRP Nautilus

## Resource Specification
```yaml
resources:
  limits:
    nvidia.com/a100: 1  # Request specific A100 GPU
    memory: 32Gi         # Recommended memory
    cpu: 8               # Recommended CPU
  requests:
    nvidia.com/a100: 1  # Same as limits for GPU
    memory: 16Gi         # Minimum memory
    cpu: 4               # Minimum CPU
```

## Complete Pod Example
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a100-gpu-pod
  namespace: your-namespace
spec:
  containers:
  - name: gpu-container
    image: nvidia/cuda:11.8-devel-ubuntu20.04
    resources:
      limits:
        nvidia.com/a100: 1
        memory: 32Gi
        cpu: 8
      requests:
        nvidia.com/a100: 1
        memory: 16Gi
        cpu: 4
    command: ["sleep", "3600"]
  restartPolicy: Never
```

## Important Notes
- Maximum 2 GPUs per pod on NRP
- A100 has 80GB memory
- Always delete pod after use
- Use nvidia.com/a100 (not nvidia.com/gpu) for guaranteed A100 access

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/#requesting-special-gpus
""",
        "anchor": ("gpu_pods", "requesting_special_gpus")
    },

    "gpu_choosing_type": {
        "title": "Choosing GPU Type on NRP Nautilus",
        "content": """
# Choosing GPU Type on NRP Nautilus

## Available GPU Types
- **nvidia.com/gpu**: Any available GPU (generic request)
- **nvidia.com/a100**: A100 SXM4 80GB GPU (requires special access)
- **nvidia.com/a40**: A40 48GB GPU
- **nvidia.com/rtxa6000**: RTX A6000 48GB GPU
- **nvidia.com/rtx8000**: Quadro RTX 8000 48GB GPU
- **nvidia.com/gh200**: Grace Hopper GH200 96GB GPU (ARM required)
- **nvidia.com/mig-small**: A100 MIG 1g.10gb GPU slice

## Choosing the Right GPU
1. For ML inference: A40, RTX A6000, or RTX 8000
2. For large model training: A100 (requires approval)
3. For smaller workloads: MIG instances
4. For ARM-based workloads: GH200

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/#choosing-gpu-type
""",
        "anchor": ("gpu_pods", "choosing_gpu_type")
    },

    "kubectl_setup": {
        "title": "Setting Up kubectl for NRP Nautilus",
        "content": """
# Setting Up kubectl for NRP Nautilus

## Installation Steps
1. Install kubectl on your system
2. Install kubelogin plugin for authentication
3. Download the config file from NRP portal
4. Save config to ~/.kube/config

## Configuration Commands
```bash
# Check available contexts
kubectl config get-contexts

# Set Nautilus context
kubectl config use-context nautilus

# Verify access
kubectl get pods -n <your-namespace>
```

## Authentication Notes
- WSL users may need additional console authentication
- Tokens may need periodic renewal
- Use Matrix for troubleshooting access issues

Source: https://nrp.ai/documentation/userdocs/start/getting-started/#cluster-access-via-kubectl
""",
        "anchor": ("getting_started", "kubectl_access")
    },

    "resource_policies": {
        "title": "NRP Resource Allocation Policies",
        "content": """
# NRP Resource Allocation Policies

## Core Requirements
- Resource `limits` must be within 20% of `requests`
- For large deployments: `limit` = `request`
- Memory violations result in pod termination
- CPU violations can impact node performance

## Utilization Rules
- Maximum 4 pods violating utilization thresholds
- GPU utilization must exceed 40%
- CPU utilization: 20-200% of requested
- Memory utilization: 20-150% of requested

## Runtime Limits
- Interactive pods: 6 hours maximum
- Deployments: Auto-deleted after 2 weeks
- Jobs: No runtime limit but must complete meaningful work

Source: https://nrp.ai/documentation/userdocs/start/policies/#resource-allocation
""",
        "anchor": ("policies", "resource_allocation")
    },

    "storage_pvc": {
        "title": "Creating Persistent Volume Claims on NRP",
        "content": """
# Creating Persistent Volume Claims on NRP

## Basic PVC Example
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-storage
spec:
  storageClassName: rook-ceph-block
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

## Mounting to Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
spec:
  containers:
  - name: app
    image: ubuntu:20.04
    volumeMounts:
    - name: data-volume
      mountPath: /data
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: my-storage
```

## Available Storage Classes
- **rook-ceph-block**: Standard persistent block storage
- **rook-ceph-fs**: Shared filesystem storage

Source: https://nrp.ai/documentation/userdocs/tutorial/storage/#creating-a-persistent-volume-claim
""",
        "anchor": ("storage", "creating_pvc")
    }
}

def get_anchor_url(doc_type: str, section: str) -> str:
    """Get the complete URL with anchor for a specific documentation section"""
    if doc_type in NRP_DOCUMENTATION_ANCHORS:
        base_url = NRP_DOCUMENTATION_ANCHORS[doc_type]["base_url"]
        if section in NRP_DOCUMENTATION_ANCHORS[doc_type]["sections"]:
            anchor = NRP_DOCUMENTATION_ANCHORS[doc_type]["sections"][section]
            return f"{base_url}{anchor}"
    return "https://nrp.ai/documentation/"

def find_best_anchor_match(query: str) -> tuple:
    """Find the best anchor match for a given query"""
    query_lower = query.lower()

    # Check for direct topic matches
    for topic, subtopics in TOPIC_ANCHOR_MAPPING.items():
        if topic in query_lower:
            for keyword, (doc_type, section) in subtopics.items():
                if keyword in query_lower:
                    return (doc_type, section)
            # Return first match if no specific keyword found
            first_key = list(subtopics.keys())[0]
            return subtopics[first_key]

    # Check for specific keywords across all topics
    for topic, subtopics in TOPIC_ANCHOR_MAPPING.items():
        for keyword, (doc_type, section) in subtopics.items():
            if keyword in query_lower:
                return (doc_type, section)

    return None

def search_anchor_knowledge(query: str) -> str:
    """Search NRP knowledge base using anchor-based routing"""
    query_lower = query.lower()

    # GPU-specific queries
    if any(term in query_lower for term in ["a100", "gpu request", "nvidia.com"]):
        content = NRP_ANCHOR_KNOWLEDGE["gpu_request_a100"]["content"]
        return f"NRP Nautilus Documentation:\n{content}"

    if any(term in query_lower for term in ["gpu type", "choosing gpu", "which gpu"]):
        content = NRP_ANCHOR_KNOWLEDGE["gpu_choosing_type"]["content"]
        return f"NRP Nautilus Documentation:\n{content}"

    # kubectl setup queries
    if any(term in query_lower for term in ["kubectl", "config", "setup", "install"]):
        content = NRP_ANCHOR_KNOWLEDGE["kubectl_setup"]["content"]
        return f"NRP Nautilus Documentation:\n{content}"

    # Policy queries
    if any(term in query_lower for term in ["policy", "limit", "resource", "allocation"]):
        content = NRP_ANCHOR_KNOWLEDGE["resource_policies"]["content"]
        return f"NRP Nautilus Documentation:\n{content}"

    # Storage queries
    if any(term in query_lower for term in ["storage", "pvc", "persistent", "volume"]):
        content = NRP_ANCHOR_KNOWLEDGE["storage_pvc"]["content"]
        return f"NRP Nautilus Documentation:\n{content}"

    # Try to find best anchor match
    anchor_match = find_best_anchor_match(query)
    if anchor_match:
        doc_type, section = anchor_match
        url = get_anchor_url(doc_type, section)
        return f"""
# NRP Documentation Reference

Your query matches: **{section.replace('_', ' ').title()}**

For detailed information, visit:
{url}

This link will take you directly to the relevant section of the NRP documentation.

General NRP Documentation: https://nrp.ai/documentation/userdocs/
"""

    return "No specific NRP anchor documentation found for this query."

def get_all_anchor_urls() -> dict:
    """Get all available anchor URLs for reference"""
    all_urls = {}
    for doc_type, doc_info in NRP_DOCUMENTATION_ANCHORS.items():
        all_urls[doc_type] = {}
        for section, anchor in doc_info["sections"].items():
            all_urls[doc_type][section] = f"{doc_info['base_url']}{anchor}"
    return all_urls

def get_anchor_quick_reference() -> str:
    """Get quick reference with important anchor links"""
    return """
# NRP Documentation Quick Reference with Anchor Links

## GPU Resources
- Request A100 GPU: https://nrp.ai/documentation/userdocs/running/gpu-pods/#requesting-special-gpus
- Choose GPU type: https://nrp.ai/documentation/userdocs/running/gpu-pods/#choosing-gpu-type
- CUDA versions: https://nrp.ai/documentation/userdocs/running/gpu-pods/#selecting-cuda-version

## Getting Started
- Login & Access: https://nrp.ai/documentation/userdocs/start/getting-started/#get-access-and-log-in
- kubectl Setup: https://nrp.ai/documentation/userdocs/start/getting-started/#cluster-access-via-kubectl
- GUI Tools: https://nrp.ai/documentation/userdocs/start/getting-started/#gui-tools-for-kubernetes

## Policies & Limits
- Resource Allocation: https://nrp.ai/documentation/userdocs/start/policies/#resource-allocation
- Usage Violations: https://nrp.ai/documentation/userdocs/start/policies/#resource-usage-violations
- Interactive Limits: https://nrp.ai/documentation/userdocs/start/policies/#interactive-use-6-hours-max-runtime

## Storage
- Creating PVCs: https://nrp.ai/documentation/userdocs/tutorial/storage/#creating-a-persistent-volume-claim
- Storage Classes: https://nrp.ai/documentation/userdocs/tutorial/storage/#exploring-storageclasses
- EmptyDir: https://nrp.ai/documentation/userdocs/tutorial/storage/#create-an-emptydir

## Jobs & Batch Processing
- Batch Jobs: https://nrp.ai/documentation/userdocs/tutorial/jobs/#_top
- Job Policies: https://nrp.ai/documentation/userdocs/start/policies/#batch-jobs

Source: Comprehensive NRP Documentation with exact anchor links
"""