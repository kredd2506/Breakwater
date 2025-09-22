#!/usr/bin/env python3
"""
NRP.ai Prompts FastMCP Server
============================
Comprehensive prompt templates for NRP/Nautilus operations including:
- GPU resource request prompts
- Storage configuration prompts
- FPGA deployment prompts
- Kubernetes troubleshooting prompts
- A100 GPU specific prompts
- Ceph S3 configuration prompts
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from fastmcp import FastMCP
from fastmcp.prompts import Message

# Add imports for our existing systems
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_ultimate_server import EnhancedNRPManager

# Initialize FastMCP
mcp = FastMCP("NRP.ai Prompts Server")

# Initialize our enhanced manager for content access
nrp_manager = EnhancedNRPManager()

# 1. GPU RESOURCE PROMPTS

@mcp.prompt("nrp-gpu-request")
def gpu_request_prompt(
    gpu_type: str = "general",
    gpu_count: int = 1,
    memory_gb: int = 16,
    cpu_cores: int = 4,
    namespace: str = "gsoc"
) -> List[Message]:
    """Generate GPU resource request YAML and instructions for NRP Nautilus"""

    # Determine the correct GPU resource identifier
    gpu_resource_map = {
        "general": "nvidia.com/gpu",
        "a100": "nvidia.com/a100",
        "a40": "nvidia.com/a40",
        "rtx6000": "nvidia.com/rtxa6000",
        "rtx8000": "nvidia.com/rtx8000",
        "grace_hopper": "nvidia.com/gh200"
    }

    gpu_resource = gpu_resource_map.get(gpu_type.lower(), "nvidia.com/gpu")

    # Special instructions for A100
    a100_note = ""
    if gpu_type.lower() == "a100":
        a100_note = """
⚠️ **IMPORTANT NOTE FOR A100 GPUs:**
- A100 GPUs require reservations on NRP Nautilus
- You must request the specific resource 'nvidia.com/a100'
- Contact your cluster administrator for A100 reservations
- Consider Grace Hopper (nvidia.com/gh200) for ARM workloads
"""

    yaml_template = f"""apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-{gpu_type}
  namespace: {namespace}
spec:
  containers:
  - name: gpu-container
    image: tensorflow/tensorflow:latest-gpu
    command: ["sleep", "infinity"]
    resources:
      requests:
        {gpu_resource}: {gpu_count}
        cpu: {cpu_cores}
        memory: {memory_gb}Gi
      limits:
        {gpu_resource}: {gpu_count}
        cpu: {cpu_cores}
        memory: {memory_gb}Gi
  restartPolicy: Never"""

    return [
        Message(
            role="user",
            content=f"""Please help me create a GPU pod configuration for NRP Nautilus with the following requirements:
- GPU Type: {gpu_type}
- GPU Count: {gpu_count}
- Memory: {memory_gb}GB
- CPU Cores: {cpu_cores}
- Namespace: {namespace}

Provide the YAML configuration and any important notes or warnings."""
        ),
        Message(
            role="assistant",
            content=f"""I'll help you create a GPU pod configuration for NRP Nautilus. Here's the complete setup:

## GPU Pod Configuration

```yaml
{yaml_template}
```

## Deployment Instructions

1. **Save the YAML** to a file (e.g., `gpu-pod-{gpu_type}.yaml`)
2. **Apply to cluster**: `kubectl apply -f gpu-pod-{gpu_type}.yaml`
3. **Check status**: `kubectl get pods -n {namespace}`
4. **Access container**: `kubectl exec -it gpu-pod-{gpu_type} -n {namespace} -- bash`

## Resource Details

- **GPU Resource**: `{gpu_resource}`
- **Total GPUs**: {gpu_count}
- **Memory Allocation**: {memory_gb}GB
- **CPU Allocation**: {cpu_cores} cores
- **Namespace**: {namespace}

{a100_note}

## Verification Commands

```bash
# Check GPU availability in pod
kubectl exec gpu-pod-{gpu_type} -n {namespace} -- nvidia-smi

# View pod resource usage
kubectl top pod gpu-pod-{gpu_type} -n {namespace}

# Check pod logs
kubectl logs gpu-pod-{gpu_type} -n {namespace}
```

## Troubleshooting

- If pod stays in Pending: Check GPU availability with `kubectl describe nodes`
- For scheduling issues: Verify resource quotas and node selectors
- For A100 access: Ensure you have proper reservations

The configuration follows NRP Nautilus best practices for GPU resource allocation."""
        )
    ]

@mcp.prompt("nrp-a100-specific")
def a100_specific_prompt(
    workload_type: str = "ml_training",
    memory_gb: int = 32,
    cpu_cores: int = 8,
    namespace: str = "gsoc"
) -> List[Message]:
    """Generate A100-specific prompts with reservation requirements"""

    workload_configs = {
        "ml_training": {
            "image": "pytorch/pytorch:latest",
            "command": '["python", "/workspace/train.py"]'
        },
        "inference": {
            "image": "tensorflow/serving:latest-gpu",
            "command": '["tensorflow_model_server", "--port=8500"]'
        },
        "data_processing": {
            "image": "nvidia/cuda:12.4.1-cudnn-dev",
            "command": '["python", "/workspace/process.py"]'
        }
    }

    config = workload_configs.get(workload_type, workload_configs["ml_training"])

    yaml_content = f"""apiVersion: v1
kind: Pod
metadata:
  name: a100-{workload_type}
  namespace: {namespace}
  labels:
    gpu-type: a100
    workload: {workload_type}
spec:
  containers:
  - name: a100-container
    image: {config["image"]}
    command: {config["command"]}
    resources:
      requests:
        nvidia.com/a100: 1
        cpu: {cpu_cores}
        memory: {memory_gb}Gi
      limits:
        nvidia.com/a100: 1
        cpu: {cpu_cores}
        memory: {memory_gb}Gi
    volumeMounts:
    - name: workspace
      mountPath: /workspace
  volumes:
  - name: workspace
    emptyDir: {{}}
  restartPolicy: Never
  nodeSelector:
    gpu-type: a100"""

    return [
        Message(
            role="user",
            content=f"""I need to deploy a {workload_type} workload on A100 GPUs in NRP Nautilus. Please provide the configuration and all the important requirements and steps."""
        ),
        Message(
            role="assistant",
            content=f"""I'll help you deploy a {workload_type} workload on A100 GPUs. Here's everything you need:

## 🚨 A100 Requirements

**CRITICAL:** A100 GPUs require advance reservations on NRP Nautilus. You must:
1. Contact your cluster administrator or submit a reservation request
2. Specify your use case and time requirements
3. Wait for approval before deploying

## A100 Pod Configuration

```yaml
{yaml_content}
```

## Pre-Deployment Checklist

- [ ] **Reservation confirmed** for A100 access
- [ ] **Namespace access** verified for `{namespace}`
- [ ] **Image compatibility** confirmed for A100 architecture
- [ ] **Storage requirements** planned (if needed)

## Deployment Steps

1. **Verify A100 availability**:
   ```bash
   kubectl get nodes -l gpu-type=a100
   kubectl describe nodes -l gpu-type=a100
   ```

2. **Deploy the pod**:
   ```bash
   kubectl apply -f a100-{workload_type}.yaml
   ```

3. **Monitor deployment**:
   ```bash
   kubectl get pods -n {namespace} -w
   kubectl describe pod a100-{workload_type} -n {namespace}
   ```

## A100 Specific Features

- **80GB HBM2e memory** - Ideal for large models
- **NVLINK connectivity** - High bandwidth between GPUs
- **Multi-Instance GPU (MIG)** - Can be partitioned for smaller workloads
- **Tensor cores** - Optimized for AI/ML workloads

## Monitoring and Optimization

```bash
# Check GPU utilization
kubectl exec a100-{workload_type} -n {namespace} -- nvidia-smi

# Monitor GPU memory usage
kubectl exec a100-{workload_type} -n {namespace} -- nvidia-smi -q -d MEMORY

# Check MIG status (if enabled)
kubectl exec a100-{workload_type} -n {namespace} -- nvidia-smi -L
```

## Troubleshooting A100 Issues

- **Pod Pending**: Likely no A100 reservation or nodes unavailable
- **CUDA errors**: Verify image supports CUDA 11.x/12.x for A100
- **Memory issues**: A100 has 80GB - adjust batch sizes accordingly
- **Performance**: Enable Tensor cores in your application for optimal performance

This configuration follows NRP Nautilus A100 deployment best practices."""
        )
    ]

@mcp.prompt("nrp-storage-config")
def storage_config_prompt(
    storage_type: str = "ceph_rbd",
    size: str = "10Gi",
    access_mode: str = "ReadWriteOnce",
    namespace: str = "gsoc"
) -> List[Message]:
    """Generate storage configuration prompts for NRP Nautilus"""

    storage_configs = {
        "ceph_rbd": {
            "class": "rook-ceph-block",
            "description": "High-performance block storage",
            "use_case": "Databases, file systems, single pod access"
        },
        "ceph_fs": {
            "class": "rook-cephfs",
            "description": "Shared filesystem storage",
            "use_case": "Multi-pod access, shared data processing"
        },
        "ceph_s3": {
            "class": "ceph-s3",
            "description": "Object storage compatible with S3 API",
            "use_case": "Large datasets, backup, archival"
        }
    }

    config = storage_configs.get(storage_type, storage_configs["ceph_rbd"])

    pvc_yaml = f"""apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {storage_type}-storage
  namespace: {namespace}
spec:
  accessModes:
  - {access_mode}
  resources:
    requests:
      storage: {size}
  storageClassName: {config["class"]}"""

    pod_yaml = f"""apiVersion: v1
kind: Pod
metadata:
  name: storage-test-pod
  namespace: {namespace}
spec:
  containers:
  - name: test-container
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: storage-volume
      mountPath: /data
  volumes:
  - name: storage-volume
    persistentVolumeClaim:
      claimName: {storage_type}-storage
  restartPolicy: Never"""

    return [
        Message(
            role="user",
            content=f"""I need to set up {storage_type} storage on NRP Nautilus with {size} capacity. Please provide the configuration and usage instructions."""
        ),
        Message(
            role="assistant",
            content=f"""I'll help you set up {storage_type} storage on NRP Nautilus. Here's the complete configuration:

## Storage Configuration Overview

- **Storage Type**: {config["description"]}
- **Use Case**: {config["use_case"]}
- **Size**: {size}
- **Access Mode**: {access_mode}
- **Storage Class**: {config["class"]}

## 1. Persistent Volume Claim

```yaml
{pvc_yaml}
```

## 2. Pod with Storage Mount

```yaml
{pod_yaml}
```

## Deployment Instructions

1. **Create the PVC**:
   ```bash
   kubectl apply -f pvc-{storage_type}.yaml
   ```

2. **Verify PVC status**:
   ```bash
   kubectl get pvc -n {namespace}
   kubectl describe pvc {storage_type}-storage -n {namespace}
   ```

3. **Deploy pod with storage**:
   ```bash
   kubectl apply -f pod-with-storage.yaml
   ```

4. **Test storage access**:
   ```bash
   kubectl exec storage-test-pod -n {namespace} -- df -h /data
   kubectl exec storage-test-pod -n {namespace} -- touch /data/test-file
   ```

## Storage Type Specific Notes

### Ceph RBD (Block Storage)
- High performance, low latency
- Single pod access only
- Ideal for databases and applications requiring fast I/O

### Ceph FS (Filesystem)
- Shared access across multiple pods
- POSIX-compliant filesystem
- Great for collaborative workloads

### Ceph S3 (Object Storage)
- S3-compatible API access
- Ideal for large datasets and backups
- Requires S3 client tools or libraries

## Monitoring Storage Usage

```bash
# Check PVC usage
kubectl get pvc -n {namespace}

# View storage details
kubectl describe pv $(kubectl get pvc {storage_type}-storage -n {namespace} -o jsonpath='{{.spec.volumeName}}')

# Monitor Ceph cluster health
kubectl get cephcluster -n rook-ceph
```

## Best Practices

- **Size carefully**: Storage expansion may require admin intervention
- **Backup important data**: Use additional backup strategies
- **Monitor usage**: Set up alerts for storage capacity
- **Access patterns**: Choose storage type based on your access needs

This configuration follows NRP Nautilus storage best practices and Ceph recommendations."""
        )
    ]

@mcp.prompt("nrp-fpga-deployment")
def fpga_deployment_prompt(
    fpga_type: str = "esnet_smartnic",
    application: str = "network_processing",
    namespace: str = "gsoc"
) -> List[Message]:
    """Generate FPGA deployment prompts for NRP Nautilus"""

    fpga_configs = {
        "esnet_smartnic": {
            "resource": "esnet.gov/smartnic-fpga",
            "image": "esnet/smartnic-dev:latest",
            "description": "ESnet SmartNIC FPGA for network acceleration"
        },
        "xilinx_u280": {
            "resource": "xilinx.com/u280-fpga",
            "image": "xilinx/vitis:latest",
            "description": "Xilinx U280 FPGA for compute acceleration"
        }
    }

    config = fpga_configs.get(fpga_type, fpga_configs["esnet_smartnic"])

    fpga_yaml = f"""apiVersion: v1
kind: Pod
metadata:
  name: fpga-{application}
  namespace: {namespace}
  labels:
    fpga-type: {fpga_type}
    application: {application}
spec:
  containers:
  - name: fpga-container
    image: {config["image"]}
    command: ["sleep", "infinity"]
    resources:
      requests:
        {config["resource"]}: 1
        cpu: 4
        memory: 16Gi
      limits:
        {config["resource"]}: 1
        cpu: 8
        memory: 32Gi
    volumeMounts:
    - name: fpga-dev
      mountPath: /dev
    - name: workspace
      mountPath: /workspace
    securityContext:
      privileged: true
  volumes:
  - name: fpga-dev
    hostPath:
      path: /dev
  - name: workspace
    emptyDir: {{}}
  restartPolicy: Never
  nodeSelector:
    fpga-type: {fpga_type}"""

    return [
        Message(
            role="user",
            content=f"""I need to deploy an FPGA-based {application} application using {fpga_type} on NRP Nautilus. Please provide the configuration and development guidance."""
        ),
        Message(
            role="assistant",
            content=f"""I'll help you deploy an FPGA application on NRP Nautilus. Here's the complete setup for {fpga_type}:

## FPGA Configuration Overview

- **FPGA Type**: {config["description"]}
- **Resource**: {config["resource"]}
- **Application**: {application}
- **Development Image**: {config["image"]}

## FPGA Pod Configuration

```yaml
{fpga_yaml}
```

## Pre-Deployment Requirements

### 1. FPGA Access Permissions
```bash
# Verify FPGA node availability
kubectl get nodes -l fpga-type={fpga_type}

# Check FPGA resource allocation
kubectl describe nodes -l fpga-type={fpga_type}
```

### 2. Development Environment Setup
- Ensure FPGA development tools are available
- Verify bitstream files and IP cores
- Prepare application code and build scripts

## Deployment Steps

1. **Deploy FPGA pod**:
   ```bash
   kubectl apply -f fpga-{application}.yaml
   ```

2. **Verify FPGA access**:
   ```bash
   kubectl exec fpga-{application} -n {namespace} -- ls -la /dev | grep fpga
   ```

3. **Check FPGA status**:
   ```bash
   kubectl exec fpga-{application} -n {namespace} -- lspci | grep -i fpga
   ```

## FPGA Development Workflow

### For ESnet SmartNIC:
```bash
# Enter development environment
kubectl exec -it fpga-{application} -n {namespace} -- bash

# Compile FPGA design
cd /workspace
make build-fpga

# Program FPGA
make program-fpga

# Test functionality
make test-fpga
```

### For Xilinx FPGAs:
```bash
# Set up Vitis environment
source /opt/xilinx/vitis/2023.1/settings64.sh

# Build hardware kernel
v++ -c -t hw --platform xilinx_u280_xdma -k my_kernel my_kernel.cpp

# Link kernel
v++ -l -t hw --platform xilinx_u280_xdma my_kernel.xo

# Run on hardware
./app.exe my_kernel.xclbin
```

## Monitoring and Debugging

```bash
# Monitor FPGA utilization
kubectl exec fpga-{application} -n {namespace} -- fpga-stat

# Check FPGA temperature and power
kubectl exec fpga-{application} -n {namespace} -- fpga-sensors

# View kernel logs
kubectl logs fpga-{application} -n {namespace}

# Debug FPGA issues
kubectl exec fpga-{application} -n {namespace} -- dmesg | grep -i fpga
```

## FPGA Security Considerations

- **Privileged access** required for FPGA device access
- **Host device mounting** needed for FPGA communication
- **Network isolation** recommended for production deployments
- **Bitstream validation** essential for security

## Performance Optimization

- **CPU affinity**: Pin processes to NUMA-local CPUs
- **Memory allocation**: Use hugepages for better performance
- **Network tuning**: Optimize for high-bandwidth applications
- **Power management**: Monitor thermal limits

This configuration provides a secure, performant FPGA development environment on NRP Nautilus."""
        )
    ]

@mcp.prompt("nrp-troubleshooting")
def troubleshooting_prompt(
    issue_type: str = "pod_pending",
    resource_type: str = "gpu",
    namespace: str = "gsoc"
) -> List[Message]:
    """Generate troubleshooting prompts for common NRP Nautilus issues"""

    troubleshooting_guides = {
        "pod_pending": {
            "title": "Pod Stuck in Pending State",
            "common_causes": [
                "Insufficient resources (CPU, memory, GPU)",
                "Node selector constraints not met",
                "Resource quotas exceeded",
                "Storage provisioning issues",
                "Scheduling constraints"
            ]
        },
        "gpu_not_detected": {
            "title": "GPU Not Detected in Pod",
            "common_causes": [
                "Incorrect GPU resource specification",
                "GPU drivers not loaded",
                "Wrong container image",
                "Node scheduling issues"
            ]
        },
        "storage_mount_failed": {
            "title": "Storage Mount Failed",
            "common_causes": [
                "PVC not bound",
                "Storage class issues",
                "Ceph cluster problems",
                "Permissions issues"
            ]
        }
    }

    guide = troubleshooting_guides.get(issue_type, troubleshooting_guides["pod_pending"])

    diagnostic_commands = f"""# Basic pod diagnostics
kubectl get pods -n {namespace}
kubectl describe pod <pod-name> -n {namespace}
kubectl logs <pod-name> -n {namespace}

# Resource-specific checks
kubectl get nodes -l {resource_type}=available
kubectl describe nodes -l {resource_type}=available

# Cluster resource status
kubectl top nodes
kubectl get resourcequota -n {namespace}

# Events and logs
kubectl get events -n {namespace} --sort-by='.lastTimestamp'
kubectl logs -n kube-system -l app=nvidia-device-plugin"""

    return [
        Message(
            role="user",
            content=f"""I'm having issues with {issue_type} related to {resource_type} resources in namespace {namespace} on NRP Nautilus. Can you help me troubleshoot this?"""
        ),
        Message(
            role="assistant",
            content=f"""I'll help you troubleshoot the {guide["title"]} issue on NRP Nautilus. Let's work through this systematically:

## Issue: {guide["title"]}

### Common Causes:
{chr(10).join(f"- {cause}" for cause in guide["common_causes"])}

## Step-by-Step Troubleshooting

### 1. Basic Diagnostics
```bash
{diagnostic_commands}
```

### 2. Resource-Specific Checks

#### For GPU Issues:
```bash
# Check GPU resource availability
kubectl get nodes -o yaml | grep -A 5 "nvidia.com/gpu"

# Verify GPU device plugin
kubectl get pods -n kube-system | grep nvidia

# Check GPU node status
kubectl describe nodes | grep -A 10 "Allocated resources"
```

#### For Storage Issues:
```bash
# Check PVC status
kubectl get pvc -n {namespace}

# Verify storage classes
kubectl get storageclass

# Check Ceph cluster health
kubectl get cephcluster -n rook-ceph
```

#### For FPGA Issues:
```bash
# Check FPGA nodes
kubectl get nodes -l fpga-type

# Verify FPGA resources
kubectl describe nodes -l fpga-type | grep -A 5 "fpga"
```

### 3. Common Solutions

#### For Pending Pods:
1. **Check resource requests vs availability**:
   ```bash
   kubectl describe nodes | grep -A 5 "Non-terminated Pods"
   ```

2. **Verify node selectors**:
   ```bash
   kubectl get nodes --show-labels | grep {resource_type}
   ```

3. **Check resource quotas**:
   ```bash
   kubectl describe resourcequota -n {namespace}
   ```

#### For Resource Access Issues:
1. **Restart device plugins**:
   ```bash
   kubectl delete pods -n kube-system -l name=nvidia-device-plugin-daemonset
   ```

2. **Check node conditions**:
   ```bash
   kubectl describe nodes | grep -A 10 "Conditions"
   ```

### 4. Advanced Debugging

```bash
# Check scheduler logs
kubectl logs -n kube-system -l component=kube-scheduler

# Verify API server connectivity
kubectl cluster-info

# Check node resource allocation
kubectl top nodes --sort-by=cpu
kubectl top nodes --sort-by=memory
```

### 5. Prevention Strategies

- **Resource planning**: Always check available resources before deployment
- **Monitoring**: Set up alerts for resource utilization
- **Testing**: Use small test pods to verify configurations
- **Documentation**: Keep track of working configurations

## Next Steps

1. Run the diagnostic commands above
2. Check the specific error messages in pod events
3. Verify your YAML configuration matches working examples
4. If issues persist, contact NRP Nautilus support with diagnostic output

Would you like me to help you interpret any specific error messages or dive deeper into any particular aspect of the troubleshooting?"""
        )
    ]

@mcp.prompt("nrp-best-practices")
def best_practices_prompt(
    category: str = "general",
    use_case: str = "research"
) -> List[Message]:
    """Generate best practices prompts for NRP Nautilus usage"""

    return [
        Message(
            role="user",
            content=f"""What are the best practices for {category} usage on NRP Nautilus for {use_case} workloads?"""
        ),
        Message(
            role="assistant",
            content=f"""Here are the comprehensive best practices for {category} usage on NRP Nautilus:

## General NRP Nautilus Best Practices

### 1. Resource Management
- **Right-size requests**: Only request resources you actually need
- **Set limits**: Always define resource limits to prevent resource hogging
- **Use namespaces**: Organize workloads by project or team
- **Monitor usage**: Regularly check resource utilization

### 2. Security Practices
- **Principle of least privilege**: Use minimal required permissions
- **Secure images**: Use official images from trusted registries
- **Network policies**: Implement proper network isolation
- **Secrets management**: Use Kubernetes secrets for sensitive data

### 3. Performance Optimization
- **Node affinity**: Use node selectors for specific hardware requirements
- **Pod anti-affinity**: Distribute pods across nodes for high availability
- **Resource quotas**: Set appropriate quotas to ensure fair resource sharing
- **Horizontal scaling**: Design applications for horizontal scaling

### 4. Cost Optimization
- **Efficient scheduling**: Use spot instances and preemptible nodes when appropriate
- **Auto-scaling**: Implement cluster and pod autoscaling
- **Resource cleanup**: Regular cleanup of unused resources
- **Batch processing**: Use Jobs for batch workloads instead of long-running pods

## Category-Specific Best Practices

### GPU Workloads
```yaml
# Example optimized GPU configuration
resources:
  requests:
    nvidia.com/gpu: 1
    cpu: 4
    memory: 16Gi
  limits:
    nvidia.com/gpu: 1
    cpu: 8
    memory: 32Gi
```

- **GPU sharing**: Use MIG for smaller workloads
- **Memory management**: Monitor GPU memory usage
- **CUDA optimization**: Use appropriate CUDA versions
- **Batch size tuning**: Optimize batch sizes for GPU memory

### Storage Best Practices
- **Choose appropriate storage**: RBD for performance, CephFS for sharing
- **Size appropriately**: Storage expansion can be complex
- **Backup strategy**: Implement regular backups
- **Access patterns**: Match storage type to access patterns

### Networking
- **Service mesh**: Consider Istio for complex microservices
- **Load balancing**: Use appropriate load balancing strategies
- **Ingress**: Secure external access with proper ingress configuration
- **DNS**: Use cluster DNS for service discovery

## Monitoring and Observability

### Logging
```yaml
# Example logging sidecar
- name: logging-sidecar
  image: fluent/fluent-bit:latest
  volumeMounts:
  - name: logs
    mountPath: /var/log
```

### Metrics
- **Prometheus**: Use for metrics collection
- **Grafana**: Visualization and alerting
- **Custom metrics**: Implement application-specific metrics
- **SLI/SLO**: Define service level indicators and objectives

## Development Workflow

### 1. Local Development
```bash
# Use kind for local testing
kind create cluster --config=kind-config.yaml
kubectl apply -f your-manifests/
```

### 2. CI/CD Pipeline
- **GitOps**: Use ArgoCD or Flux for deployment
- **Testing**: Implement comprehensive testing strategies
- **Security scanning**: Scan images for vulnerabilities
- **Progressive deployment**: Use blue-green or canary deployments

### 3. Environment Management
- **Separate environments**: Dev, staging, production isolation
- **Configuration management**: Use ConfigMaps and Secrets
- **Version control**: Track all configurations in Git
- **Rollback strategy**: Plan for quick rollbacks

## Troubleshooting Guidelines

### Debugging Process
1. **Check pod status**: `kubectl get pods`
2. **Examine events**: `kubectl describe pod <name>`
3. **Review logs**: `kubectl logs <pod-name>`
4. **Resource analysis**: `kubectl top pods`
5. **Network connectivity**: Test service endpoints

### Common Issues
- **ImagePullBackOff**: Check image registry access
- **CrashLoopBackOff**: Review application logs and configuration
- **Pending pods**: Verify resource availability
- **Service connectivity**: Check service and endpoint configuration

## Research-Specific Recommendations

### Data Management
- **Data lifecycle**: Plan for data ingestion, processing, and archival
- **Reproducibility**: Version datasets and models
- **Collaboration**: Use shared storage for team access
- **Compliance**: Follow institutional data policies

### Experimentation
- **Experiment tracking**: Use MLflow or similar tools
- **Hyperparameter tuning**: Leverage Kubernetes Jobs for parallel tuning
- **Model versioning**: Implement proper model lifecycle management
- **Resource scheduling**: Use batch queues for long-running experiments

These practices will help you build reliable, efficient, and secure applications on NRP Nautilus."""
        )
    ]

if __name__ == "__main__":
    print("Starting NRP.ai Prompts FastMCP Server...")
    print()
    print("Available Prompts:")
    print("- nrp-gpu-request - GPU resource request configurations")
    print("- nrp-a100-specific - A100 GPU specific deployments")
    print("- nrp-storage-config - Storage configuration prompts")
    print("- nrp-fpga-deployment - FPGA deployment configurations")
    print("- nrp-troubleshooting - Troubleshooting guidance")
    print("- nrp-best-practices - Best practices for NRP Nautilus")
    print()

    mcp.run(transport="http", port=8009)