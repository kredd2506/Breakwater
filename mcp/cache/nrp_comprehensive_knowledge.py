#!/usr/bin/env python3
"""
NRP Comprehensive Knowledge Base
===============================
Comprehensive knowledge base for NRP Nautilus covering all key documentation areas.
This contains exact specifications and examples from the official NRP documentation.
"""

# Getting Started Information
NRP_GETTING_STARTED = {
    "account_setup": {
        "portal_url": "https://nrp.ai",
        "login_methods": ["CILogon (institutional)", "Microsoft", "Google", "GitHub", "ORCID"],
        "namespace_access": {
            "students": "Request access from research supervisor",
            "faculty": "Request namespace admin status via Matrix",
            "admin_privileges": ["Create multiple namespaces", "Invite users to namespaces"]
        }
    },
    "kubectl_setup": {
        "prerequisites": ["Install kubectl", "Install kubelogin plugin"],
        "config_steps": [
            "Download config file to ~/.kube/config",
            "kubectl config get-contexts",
            "kubectl config use-context nautilus",
            "kubectl get pods -n <YOUR_NAMESPACE>"
        ],
        "verification": "kubectl get pods -n <YOUR_NAMESPACE>"
    },
    "required_reading": [
        "NRP Acceptable Use Policy",
        "Cluster Policies",
        "Using Nautilus guide"
    ],
    "warnings": [
        "Containers are stateless",
        "Data is lost on container restart",
        "Avoid force-deleting pods",
        "Do not run indefinite sleep commands"
    ]
}

# Cluster Policies and Limits
NRP_CLUSTER_POLICIES = {
    "resource_requirements": {
        "limits_vs_requests": "Resource limits must be within 20% of requests",
        "large_deployments": "For large pod/job deployments, limit = request",
        "memory_enforcement": "Pods exceeding memory limits will be killed",
        "cpu_enforcement": "CPU limit exceedance can impact entire node performance"
    },
    "utilization_rules": {
        "max_violations": 4,
        "gpu_utilization": ">40% utilization required",
        "cpu_utilization": "20-200% of requested",
        "memory_utilization": "20-150% of requested",
        "exception": "Pods with 1 CPU core and 2GB memory"
    },
    "runtime_limits": {
        "interactive_pods": {
            "max_runtime": "6 hours",
            "max_resources": "2 GPUs, 32GB RAM, 16 CPU cores"
        },
        "deployments": "Automatically deleted after 2 weeks",
        "batch_jobs": "Must use Kubernetes Job controller"
    },
    "prohibited_practices": [
        "No 'sleep infinity' in Jobs",
        "Users running Jobs with sleep commands will be banned",
        "Avoid resource waste; underutilized namespaces risk banning"
    ],
    "data_management": [
        "Purge unused data regularly",
        "Volumes not accessed for 6 months may be deleted",
        "Not for archival storage"
    ]
}

# Storage Information
NRP_STORAGE = {
    "storage_types": {
        "local_storage": {
            "description": "Directly attached to nodes",
            "characteristics": ["Fast", "Not portable"]
        },
        "persistent_volumes": {
            "description": "Cluster-wide storage resources",
            "abbreviation": "PV"
        },
        "persistent_volume_claims": {
            "description": "Storage requests by applications",
            "abbreviation": "PVC"
        },
        "object_storage": {
            "description": "Integration with systems like Amazon S3"
        }
    },
    "emptydir_volume": {
        "description": "Temporary storage within a pod",
        "lifecycle": "Exists only while pod is running",
        "data_persistence": "Data is deleted when pod is removed"
    },
    "pvc_example": """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-vol
spec:
  storageClassName: rook-ceph-block
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi""",
    "storage_classes": {
        "purpose": "Provide abstraction for storage provisioning",
        "availability": "Different classes available based on cluster configuration",
        "default_behavior": "Default class used if none specified"
    },
    "best_practices": [
        "Choose appropriate storage based on application needs",
        "Optimize resource requirements",
        "Consider compute node location relative to storage class"
    ]
}

# Jobs and Batch Processing
NRP_JOBS = {
    "definition": "A Kubernetes Job is a workload designed to run a finite number of tasks to completion",
    "use_cases": ["Data processing", "Analysis", "Updates", "Backups", "Periodic work"],
    "characteristics": [
        "Jobs differ from Pods: A Job is a higher-level abstraction that manages a Pod",
        "Jobs ensure Pods run to completion and can be scaled up or down",
        "Jobs have a backoffLimit that determines how many times a failed Pod will be restarted"
    ],
    "job_management": [
        "Jobs can be configured with resource limits for memory and CPU",
        "Completed jobs and their pods remain accessible for a default of 1 week",
        "You can view job logs using kubectl logs <pod-name>"
    ],
    "nautilus_specific": "On Nautilus, jobs are not limited in runtime and must have a meaningful command",
    "job_example": """apiVersion: batch/v1
kind: Job
metadata:
  name: pi
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
  backoffLimit: 4"""
}

# Networking and Services
NRP_NETWORKING = {
    "service_types": {
        "ClusterIP": "Internal cluster communication",
        "NodePort": "External access via node ports",
        "LoadBalancer": "External load balancer (if available)",
        "ExternalName": "DNS CNAME record"
    },
    "ingress": {
        "purpose": "HTTP/HTTPS routing to services",
        "requirements": "Requires ingress controller"
    },
    "network_policies": {
        "purpose": "Control traffic between pods",
        "default_behavior": "All traffic allowed by default"
    }
}

# Common Pod Configurations
NRP_POD_EXAMPLES = {
    "basic_pod": """apiVersion: v1
kind: Pod
metadata:
  name: basic-pod
  namespace: {namespace}
spec:
  containers:
  - name: main-container
    image: ubuntu:20.04
    resources:
      limits:
        memory: 2Gi
        cpu: 1
      requests:
        memory: 1Gi
        cpu: 500m
    command: ["sleep", "3600"]
  restartPolicy: Never""",

    "storage_pod": """apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: {namespace}
spec:
  containers:
  - name: main-container
    image: ubuntu:20.04
    volumeMounts:
    - name: data-volume
      mountPath: /data
    resources:
      limits:
        memory: 2Gi
        cpu: 1
      requests:
        memory: 1Gi
        cpu: 500m
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: my-pvc
  restartPolicy: Never""",

    "job_with_resources": """apiVersion: batch/v1
kind: Job
metadata:
  name: processing-job
  namespace: {namespace}
spec:
  template:
    spec:
      containers:
      - name: processor
        image: python:3.9
        resources:
          limits:
            memory: 4Gi
            cpu: 2
          requests:
            memory: 2Gi
            cpu: 1
        command: ["python", "process_data.py"]
      restartPolicy: Never
  backoffLimit: 3"""
}

# Best Practices
NRP_BEST_PRACTICES = {
    "resource_management": [
        "Always specify both limits and requests",
        "Keep limits within 20% of requests",
        "Monitor resource utilization regularly",
        "Delete unused resources promptly"
    ],
    "pod_design": [
        "Use Jobs for finite tasks",
        "Use Deployments for long-running services",
        "Avoid indefinite sleep commands",
        "Design for stateless operation"
    ],
    "storage": [
        "Use appropriate storage class for your needs",
        "Clean up unused data regularly",
        "Consider data location and performance requirements"
    ],
    "security": [
        "Follow least privilege principle",
        "Use resource quotas appropriately",
        "Regular security updates for images"
    ]
}

def search_comprehensive_nrp_knowledge(query: str) -> str:
    """Search comprehensive NRP knowledge base for relevant information"""
    query_lower = query.lower()

    # Getting started queries
    if any(word in query_lower for word in ["start", "begin", "setup", "account", "kubectl"]):
        return f"""
# Getting Started with NRP Nautilus

## Account Setup
- Portal: {NRP_GETTING_STARTED['account_setup']['portal_url']}
- Login methods: {', '.join(NRP_GETTING_STARTED['account_setup']['login_methods'])}

## Kubectl Configuration
Prerequisites: {', '.join(NRP_GETTING_STARTED['kubectl_setup']['prerequisites'])}

Setup steps:
{chr(10).join(['- ' + step for step in NRP_GETTING_STARTED['kubectl_setup']['config_steps']])}

## Important Warnings
{chr(10).join(['- ' + warning for warning in NRP_GETTING_STARTED['warnings']])}

Source: https://nrp.ai/documentation/userdocs/start/getting-started/
"""

    # Policy queries
    if any(word in query_lower for word in ["policy", "policies", "limit", "rule", "constraint"]):
        return f"""
# NRP Cluster Policies

## Resource Requirements
- {NRP_CLUSTER_POLICIES['resource_requirements']['limits_vs_requests']}
- {NRP_CLUSTER_POLICIES['resource_requirements']['large_deployments']}
- {NRP_CLUSTER_POLICIES['resource_requirements']['memory_enforcement']}

## Utilization Rules
- Maximum {NRP_CLUSTER_POLICIES['utilization_rules']['max_violations']} pods violating rules
- GPU: {NRP_CLUSTER_POLICIES['utilization_rules']['gpu_utilization']}
- CPU: {NRP_CLUSTER_POLICIES['utilization_rules']['cpu_utilization']}
- Memory: {NRP_CLUSTER_POLICIES['utilization_rules']['memory_utilization']}

## Runtime Limits
- Interactive Pods: {NRP_CLUSTER_POLICIES['runtime_limits']['interactive_pods']['max_runtime']}, max {NRP_CLUSTER_POLICIES['runtime_limits']['interactive_pods']['max_resources']}
- Deployments: {NRP_CLUSTER_POLICIES['runtime_limits']['deployments']}

## Prohibited Practices
{chr(10).join(['- ' + practice for practice in NRP_CLUSTER_POLICIES['prohibited_practices']])}

Source: https://nrp.ai/documentation/userdocs/start/policies/
"""

    # Storage queries
    if any(word in query_lower for word in ["storage", "volume", "pvc", "persistent", "mount"]):
        return f"""
# NRP Storage Guide

## Storage Types
- **Local Storage**: {NRP_STORAGE['storage_types']['local_storage']['description']} - {', '.join(NRP_STORAGE['storage_types']['local_storage']['characteristics'])}
- **Persistent Volumes (PV)**: {NRP_STORAGE['storage_types']['persistent_volumes']['description']}
- **Persistent Volume Claims (PVC)**: {NRP_STORAGE['storage_types']['persistent_volume_claims']['description']}
- **Object Storage**: {NRP_STORAGE['storage_types']['object_storage']['description']}

## PVC Example
```yaml
{NRP_STORAGE['pvc_example']}
```

## Best Practices
{chr(10).join(['- ' + practice for practice in NRP_STORAGE['best_practices']])}

Source: https://nrp.ai/documentation/userdocs/tutorial/storage/
"""

    # Job queries
    if any(word in query_lower for word in ["job", "batch", "processing", "task"]):
        return f"""
# NRP Kubernetes Jobs

## Definition
{NRP_JOBS['definition']}

## Use Cases
{chr(10).join(['- ' + case for case in NRP_JOBS['use_cases']])}

## Key Characteristics
{chr(10).join(['- ' + char for char in NRP_JOBS['characteristics']])}

## Nautilus-Specific
{NRP_JOBS['nautilus_specific']}

## Example Job
```yaml
{NRP_JOBS['job_example']}
```

Source: https://nrp.ai/documentation/userdocs/tutorial/jobs/
"""

    # Pod queries
    if any(word in query_lower for word in ["pod", "container", "deploy", "create"]):
        return f"""
# NRP Pod Configuration

## Basic Pod Example
```yaml
{NRP_POD_EXAMPLES['basic_pod']}
```

## Pod with Storage
```yaml
{NRP_POD_EXAMPLES['storage_pod']}
```

## Best Practices for Pods
{chr(10).join(['- ' + practice for practice in NRP_BEST_PRACTICES['pod_design']])}

## Resource Management
{chr(10).join(['- ' + practice for practice in NRP_BEST_PRACTICES['resource_management']])}

Source: https://nrp.ai/documentation/userdocs/
"""

    # Networking queries
    if any(word in query_lower for word in ["network", "service", "ingress", "expose"]):
        return f"""
# NRP Networking

## Service Types
{chr(10).join([f'- **{k}**: {v}' for k, v in NRP_NETWORKING['service_types'].items()])}

## Ingress
- Purpose: {NRP_NETWORKING['ingress']['purpose']}
- Requirements: {NRP_NETWORKING['ingress']['requirements']}

## Network Policies
- Purpose: {NRP_NETWORKING['network_policies']['purpose']}
- Default: {NRP_NETWORKING['network_policies']['default_behavior']}

Source: https://nrp.ai/documentation/userdocs/
"""

    return "No specific NRP documentation found for this query. Please check https://nrp.ai/documentation/ for complete documentation."

def get_nrp_quick_reference() -> str:
    """Get a quick reference guide for common NRP operations"""
    return """
# NRP Nautilus Quick Reference

## Common Commands
```bash
# Check namespace access
kubectl get pods -n <namespace>

# Create a pod
kubectl apply -f pod.yaml

# Get pod logs
kubectl logs <pod-name> -n <namespace>

# Delete a pod
kubectl delete pod <pod-name> -n <namespace>

# Get pod status
kubectl describe pod <pod-name> -n <namespace>
```

## Resource Limits Guidelines
- Memory limits must be within 20% of requests
- GPU utilization must exceed 40%
- Interactive pods limited to 6 hours runtime
- Deployments auto-deleted after 2 weeks

## Storage Quick Start
1. Create PVC with appropriate storage class
2. Mount PVC to pod using volumeMounts
3. Use rook-ceph-block for standard persistent storage

## Common Storage Classes
- rook-ceph-block: Standard persistent block storage
- rook-ceph-fs: Shared filesystem storage

Source: https://nrp.ai/documentation/
"""