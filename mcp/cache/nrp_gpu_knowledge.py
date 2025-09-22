#!/usr/bin/env python3
"""
NRP GPU Knowledge Base
=====================
Comprehensive knowledge base for NRP Nautilus GPU requests and configurations.
This contains the exact specifications and examples from the official NRP documentation.
"""

# GPU Resource Types and Specifications
NRP_GPU_RESOURCES = {
    "standard": {
        "resource_name": "nvidia.com/gpu",
        "description": "Generic GPU request (any available GPU type)",
        "example": """
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    nvidia.com/gpu: 1"""
    },
    "a100": {
        "resource_name": "nvidia.com/a100",
        "memory": "80GB",
        "description": "A100 SXM4 80GB GPU",
        "example": """
resources:
  limits:
    nvidia.com/a100: 1
  requests:
    nvidia.com/a100: 1"""
    },
    "a40": {
        "resource_name": "nvidia.com/a40",
        "memory": "48GB",
        "description": "A40 48GB GPU",
        "example": """
resources:
  limits:
    nvidia.com/a40: 1
  requests:
    nvidia.com/a40: 1"""
    },
    "rtxa6000": {
        "resource_name": "nvidia.com/rtxa6000",
        "memory": "48GB",
        "description": "RTX A6000 48GB GPU",
        "example": """
resources:
  limits:
    nvidia.com/rtxa6000: 1
  requests:
    nvidia.com/rtxa6000: 1"""
    },
    "rtx8000": {
        "resource_name": "nvidia.com/rtx8000",
        "memory": "48GB",
        "description": "Quadro RTX 8000 48GB GPU",
        "example": """
resources:
  limits:
    nvidia.com/rtx8000: 1
  requests:
    nvidia.com/rtx8000: 1"""
    },
    "gh200": {
        "resource_name": "nvidia.com/gh200",
        "memory": "96GB",
        "description": "Grace Hopper GH200 96GB GPU (ARM architecture required)",
        "example": """
resources:
  limits:
    nvidia.com/gh200: 1
  requests:
    nvidia.com/gh200: 1""",
        "special_requirements": "Requires ARM-compatible Docker images"
    },
    "mig-small": {
        "resource_name": "nvidia.com/mig-small",
        "memory": "10GB",
        "description": "A100 MIG 1g.10gb GPU slice",
        "example": """
resources:
  limits:
    nvidia.com/mig-small: 1
  requests:
    nvidia.com/mig-small: 1"""
    }
}

# GPU Memory Specifications
GPU_MEMORY_SPECS = {
    "8GB": ["GeForce GTX 1070", "GeForce GTX 1080"],
    "12GB": ["GTX 1080-Ti", "RTX 2080-Ti"],
    "16GB": ["Tesla T4"],
    "24GB": ["A10", "RTX 3090", "RTX 4090"],
    "32GB": ["Tesla V100"],
    "48GB": ["A40", "L40", "RTX A6000", "Quadro RTX 8000"],
    "80GB": ["A100 SXM4"],
    "96GB": ["Grace Hopper GH200"]
}

# NRP-Specific Constraints and Limits
NRP_CONSTRAINTS = {
    "max_gpus_per_pod": 2,
    "max_gpus_per_job": 8,
    "special_scheduling": "4/8 GPU jobs get dedicated node scheduling",
    "cleanup_requirement": "Always delete pods after computation to free GPUs for other users"
}

# Complete Pod Examples for A100 GPU
A100_POD_EXAMPLES = {
    "basic_a100_pod": """
apiVersion: v1
kind: Pod
metadata:
  name: a100-gpu-pod
  namespace: {namespace}
spec:
  containers:
  - name: gpu-container
    image: nvidia/cuda:11.8-devel-ubuntu20.04
    resources:
      limits:
        nvidia.com/a100: 1
        memory: 16Gi
        cpu: 4
      requests:
        nvidia.com/a100: 1
        memory: 8Gi
        cpu: 2
    command: ["sleep", "3600"]
  restartPolicy: Never
""",

    "a100_with_shared_memory": """
apiVersion: v1
kind: Pod
metadata:
  name: a100-shm-pod
  namespace: {namespace}
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
    volumeMounts:
    - name: shm
      mountPath: /dev/shm
    command: ["sleep", "3600"]
  volumes:
  - name: shm
    emptyDir:
      medium: Memory
      sizeLimit: 2Gi
  restartPolicy: Never
""",

    "a100_job_example": """
apiVersion: batch/v1
kind: Job
metadata:
  name: a100-training-job
  namespace: {namespace}
spec:
  template:
    spec:
      containers:
      - name: training-container
        image: pytorch/pytorch:latest
        resources:
          limits:
            nvidia.com/a100: 1
            memory: 64Gi
            cpu: 16
          requests:
            nvidia.com/a100: 1
            memory: 32Gi
            cpu: 8
        command: ["python", "train.py"]
      restartPolicy: Never
  backoffLimit: 3
"""
}

# Best Practices for NRP GPU Usage
NRP_BEST_PRACTICES = [
    "Use Jobs instead of Pods when possible for better resource scheduling",
    "Always specify both limits and requests for GPUs",
    "Delete pods immediately after computation to free GPUs",
    "Use specific GPU types (nvidia.com/a100) instead of generic (nvidia.com/gpu) when you need specific hardware",
    "For Grace Hopper nodes, ensure your Docker images support ARM architecture",
    "Add shared memory volumes for workloads that need more than 64MB shared memory",
    "Monitor GPU utilization to ensure efficient usage",
    "Consider using MIG instances (nvidia.com/mig-small) for smaller workloads"
]

def get_gpu_request_example(gpu_type: str, namespace: str = "your-namespace") -> str:
    """Get a specific GPU request example"""
    if gpu_type.lower() in NRP_GPU_RESOURCES:
        gpu_info = NRP_GPU_RESOURCES[gpu_type.lower()]
        return f"""
To request a {gpu_info['description']}, use this resource specification:

```yaml
{gpu_info['example']}
```

Resource name: `{gpu_info['resource_name']}`
Memory: {gpu_info.get('memory', 'Variable')}
"""
    return "GPU type not found in NRP documentation."

def get_a100_complete_example(namespace: str = "your-namespace") -> str:
    """Get complete A100 pod example with NRP-specific details"""
    return f"""
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
{A100_POD_EXAMPLES['basic_a100_pod'].format(namespace=namespace)}
```

## Important Notes
- Maximum 2 GPUs per pod on NRP
- A100 has 80GB memory
- Always delete pod after use
- Use nvidia.com/a100 (not nvidia.com/gpu) for guaranteed A100 access

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/#requesting-special-gpus
"""

def search_nrp_knowledge(query: str) -> str:
    """Search NRP knowledge base for relevant information"""
    query_lower = query.lower()

    # A100 specific queries
    if "a100" in query_lower and ("request" in query_lower or "how" in query_lower):
        return get_a100_complete_example()

    # General GPU request queries
    if "gpu" in query_lower and "request" in query_lower:
        gpu_list = "\n".join([f"- {gpu}: {info['resource_name']}" for gpu, info in NRP_GPU_RESOURCES.items()])
        return f"""
# GPU Request Options on NRP Nautilus

Available GPU types:
{gpu_list}

For A100 specifically: nvidia.com/a100
For any GPU: nvidia.com/gpu

Example A100 request:
```yaml
resources:
  limits:
    nvidia.com/a100: 1
  requests:
    nvidia.com/a100: 1
```

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/
"""

    # Memory queries
    if "memory" in query_lower and "gpu" in query_lower:
        memory_info = "\n".join([f"- {mem}: {', '.join(gpus)}" for mem, gpus in GPU_MEMORY_SPECS.items()])
        return f"""
# GPU Memory Specifications on NRP

{memory_info}

For A100: 80GB memory
Recommended CPU/Memory ratios:
- A100: 8-16 CPU cores, 16-64GB RAM

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/
"""

    # Constraints and limits
    if "limit" in query_lower or "constraint" in query_lower:
        return f"""
# NRP GPU Constraints and Limits

- Maximum GPUs per pod: {NRP_CONSTRAINTS['max_gpus_per_pod']}
- Maximum GPUs per job: {NRP_CONSTRAINTS['max_gpus_per_job']}
- {NRP_CONSTRAINTS['special_scheduling']}
- {NRP_CONSTRAINTS['cleanup_requirement']}

Best Practices:
{chr(10).join(['- ' + practice for practice in NRP_BEST_PRACTICES])}

Source: https://nrp.ai/documentation/userdocs/running/gpu-pods/
"""

    return "No specific NRP documentation found for this query."