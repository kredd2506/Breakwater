#!/usr/bin/env python3
"""
Kubernetes ReAct Agent - Terminal Interface
A simple agent that helps you interact with Kubernetes using natural language.
Designed to run inside a Kubernetes pod in the 'gsoc' namespace.
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import List, Optional
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.stream import stream
from kubernetes.utils import create_from_yaml
from openai import OpenAI

# Initialize Kubernetes client
try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except config.ConfigException:
        print("Error: Could not configure Kubernetes client")
        sys.exit(1)

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()
networking_v1 = client.NetworkingV1Api()
auth_v1 = client.AuthorizationV1Api()

# Initialize OpenAI client
nrp = "sk-CXgJeeKIUtEf5AjCsaM_QQ"  # Permanently set NRP variable key

openai_client = OpenAI(
    api_key=nrp,
    base_url="https://llm.nrp-nautilus.io/"
)

# Hardcoded namespace
CURRENT_NAMESPACE = "gsoc"

# YAML Templates for pod and deployment creation
POD_TEMPLATE_YAML = """apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: {namespace}
spec:
  containers:
  - name: {container_name}
    image: {image}
    resources:
      limits:
        memory: {memory_limit}
        cpu: {cpu_limit}
      requests:
        memory: {memory_request}
        cpu: {cpu_request}
    command: {command}
"""

DEPLOYMENT_TEMPLATE_YAML = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    k8s-app: {name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      k8s-app: {name}
  template:
    metadata:
      labels:
        k8s-app: {name}
    spec:
      containers:
      - name: {container_name}
        image: {image}
        resources:
           limits:
             memory: {memory_limit}
             cpu: {cpu_limit}
           requests:
             memory: {memory_request}
             cpu: {cpu_request}
        command: {command}
"""

# Default templates for quick pod/deployment creation
DEFAULT_POD_YAML = """apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: gsoc
spec:
  containers:
  - name: mypod
    image: ubuntu
    resources:
      limits:
        memory: 100Mi
        cpu: 100m
      requests:
        memory: 100Mi
        cpu: 100m
    command: ["sh", "-c", "echo 'Im a new pod' && sleep infinity"]
"""

DEFAULT_DEPLOYMENT_YAML = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-dep
  namespace: gsoc
  labels:
    k8s-app: test-dep
spec:
  replicas: 1
  selector:
    matchLabels:
      k8s-app: test-dep
  template:
    metadata:
      labels:
        k8s-app: test-dep
    spec:
      containers:
      - name: mypod
        image: ubuntu
        resources:
           limits:
             memory: 500Mi
             cpu: 500m
           requests:
             memory: 100Mi
             cpu: 50m
        command: ["sh", "-c", "sleep infinity"]
"""

class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        completion = openai_client.chat.completions.create(
            model="gemma3", 
            temperature=0,
            messages=self.messages
        )
        return completion.choices[0].message.content

# System prompt for the agent
PROMPT = """
You are a Kubernetes assistant. You operate in a loop of:
Thought → Action → PAUSE → Observation
At the end of this loop, you output a final Answer.
---
**Instructions:**
- Use **Thought** to explain your reasoning based on the user's request.
- Use **Action** to call one of the tools listed below. Each Action must be followed by **PAUSE** so the system can run the tool.
- The result of the action will be passed back to you as an **Observation**.
- After processing the Observation, continue the loop.
- Stop when you have gathered enough information, and provide an **Answer**.
---
**Namespace Information:**
- You are operating in the 'gsoc' namespace. All operations will be performed in this namespace.
- There is no need to set the namespace.
---
**When to Use `describe_*` Tools:**
- If the user mentions a specific name (e.g., "ubuntu"), check for matching resources using `list_*` tools.
- If a match is found, use the appropriate `describe_*` tool for detailed information.
- If multiple resources match the name, describe each one.
- Only use `describe_*` if you're confident about the target resource name.
---
**Available Actions:**
list_pods:
list_deployments:
list_services:
list_jobs:
list_configmaps:
list_secrets:
list_pvcs:
list_replicasets:
list_statefulsets:
list_daemonsets:
list_events:
list_ingresses:
list_nodes:
Each of the above lists the corresponding resources.
describe_pod:
describe_deployment:
describe_job:
describe_service:
describe_configmap:
describe_secret:
describe_pvc:
describe_replicaset:
describe_statefulset:
describe_daemonset:
describe_ingress:
describe_node:
Each of the above describes the specified resource.
create_pod:
Create a pod programmatically. Takes parameter string like: "name=my-pod image=nginx memory_limit=256Mi"
create_pod_yaml:
Create a pod from YAML content. Takes YAML string as parameter.
create_deployment:
Create a deployment programmatically. Takes parameter string like: "name=my-deploy image=nginx replicas=2"
create_deployment_yaml:
Create a deployment from YAML content. Takes YAML string as parameter.
delete_pod:
Delete a pod by name. Takes pod name as parameter.
delete_deployment:
Delete a deployment by name. Takes deployment name as parameter.
pod_logs:
Get logs from a pod. Takes pod name as parameter, optionally with tail_lines.
pod_exec:
Execute command in a pod. Takes format: "pod_name command1 command2"
check_permissions:
Check what permissions the current service account has in the current namespace.
get_service_account:
Get information about the current service account.
get_pod_info:
Get information about the current pod.
---
**Example 1:**
Question: What pods are running?
Thought: I need to list the pods in the gsoc namespace.
Action: list_pods:
PAUSE
(Observation: ['coredns-abc123', 'kube-proxy-xyz789'])
Answer: The pods currently running in gsoc are: coredns-abc123, kube-proxy-xyz789.
---
**Example 2:**
Question: What is happening with ubuntu?
Thought: The user asked about something named 'ubuntu'. I will first list pods to see if any match.
Action: list_pods:
PAUSE
(Observation: ['ubuntu-runner-xyz', 'nginx'])
Thought: A pod named 'ubuntu-runner-xyz' matches. I will describe it.
Action: describe_pod: ubuntu-runner-xyz
PAUSE
(Observation: 📋 Pod 'ubuntu-runner-xyz' phase: Running, node: node-123)
Answer: The pod 'ubuntu-runner-xyz' is currently running on node node-123.
---
**Example 3:**
Question: Why can't I list pods?
Thought: The user is having trouble listing pods. I should check the permissions for the current service account.
Action: check_permissions:
PAUSE
(Observation: [ERROR] Permission denied: User "system:serviceaccount:gsoc:default" cannot list resource "pods" in API group "" in the namespace "gsoc")
Thought: The service account doesn't have permission to list pods in the gsoc namespace. I should get more information about the service account and suggest a solution.
Action: get_service_account:
PAUSE
(Observation: Current service account: system:serviceaccount:gsoc:default)
Answer: You don't have permission to list pods in the gsoc namespace. The service account "system:serviceaccount:gsoc:default" lacks the necessary RBAC permissions. You may need to create a Role and RoleBinding to grant the required permissions.
---
"""

# Namespace functions
def get_namespace():
    """Retrieve the currently set namespace."""
    return CURRENT_NAMESPACE

# Kubernetes resource functions
def validate_k8s_name(name):
    """Validate that the name follows Kubernetes RFC1123 naming convention."""
    pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    if not re.match(pattern, name):
        raise ValueError(f"[ERROR] Invalid Kubernetes resource name: '{name}'. Must match RFC1123 format.")
    return name

# Helper function to handle API errors
def handle_api_error(e):
    """Handle Kubernetes API errors and return user-friendly messages."""
    if e.status == 403:
        return f"[ERROR] Permission denied: {e.reason}"
    elif e.status == 404:
        return f"[ERROR] Resource not found: {e.reason}"
    else:
        return f"[ERROR] API error ({e.status}): {e.reason}"

# List functions
def list_pods(_=None):
    try:
        namespace = get_namespace()
        pods = v1.list_namespaced_pod(namespace=namespace)
        return [pod.metadata.name for pod in pods.items]
    except ApiException as e:
        return handle_api_error(e)

def list_deployments(_=None):
    try:
        namespace = get_namespace()
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        return [d.metadata.name for d in deployments.items]
    except ApiException as e:
        return handle_api_error(e)

def list_services(_=None):
    try:
        namespace = get_namespace()
        services = v1.list_namespaced_service(namespace=namespace)
        return [s.metadata.name for s in services.items]
    except ApiException as e:
        return handle_api_error(e)

def list_jobs(_=None):
    try:
        namespace = get_namespace()
        jobs = batch_v1.list_namespaced_job(namespace=namespace)
        return [j.metadata.name for j in jobs.items]
    except ApiException as e:
        return handle_api_error(e)

def list_configmaps(_=None):
    try:
        namespace = get_namespace()
        cms = v1.list_namespaced_config_map(namespace=namespace)
        return [cm.metadata.name for cm in cms.items]
    except ApiException as e:
        return handle_api_error(e)

def list_secrets(_=None):
    try:
        namespace = get_namespace()
        secrets = v1.list_namespaced_secret(namespace=namespace)
        return [s.metadata.name for s in secrets.items]
    except ApiException as e:
        return handle_api_error(e)

def list_pvcs(_=None):
    try:
        namespace = get_namespace()
        pvcs = v1.list_namespaced_persistent_volume_claim(namespace=namespace)
        return [p.metadata.name for p in pvcs.items]
    except ApiException as e:
        return handle_api_error(e)

def list_replicasets(_=None):
    try:
        namespace = get_namespace()
        rsets = apps_v1.list_namespaced_replica_set(namespace=namespace)
        return [r.metadata.name for r in rsets.items]
    except ApiException as e:
        return handle_api_error(e)

def list_statefulsets(_=None):
    try:
        namespace = get_namespace()
        ssets = apps_v1.list_namespaced_stateful_set(namespace=namespace)
        return [s.metadata.name for s in ssets.items]
    except ApiException as e:
        return handle_api_error(e)

def list_daemonsets(_=None):
    try:
        namespace = get_namespace()
        dsets = apps_v1.list_namespaced_daemon_set(namespace=namespace)
        return [d.metadata.name for d in dsets.items]
    except ApiException as e:
        return handle_api_error(e)

def list_ingresses(_=None):
    try:
        namespace = get_namespace()
        ingresses = networking_v1.list_namespaced_ingress(namespace=namespace)
        return [i.metadata.name for i in ingresses.items]
    except ApiException as e:
        return handle_api_error(e)

def list_events(_=None):
    try:
        namespace = get_namespace()
        events = v1.list_namespaced_event(namespace=namespace)
        return [f"{e.last_timestamp}: {e.message}" for e in events.items]
    except ApiException as e:
        return handle_api_error(e)

def list_nodes(_=None):
    try:
        nodes = v1.list_node()
        return [n.metadata.name for n in nodes.items]
    except ApiException as e:
        return handle_api_error(e)

# Describe functions
def describe_pod(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        pod = v1.read_namespaced_pod(name=name, namespace=namespace)
        
        # Enhanced pod description with more details
        description = [f"Pod '{name}' Details:"]
        description.append(f"  Phase: {pod.status.phase}")
        description.append(f"  Node: {pod.spec.node_name or 'Not assigned'}")
        description.append(f"  Namespace: {namespace}")
        
        # Pod IP and host IP
        if pod.status.pod_ip:
            description.append(f"  Pod IP: {pod.status.pod_ip}")
        if pod.status.host_ip:
            description.append(f"  Host IP: {pod.status.host_ip}")
        
        # Container information
        if pod.spec.containers:
            description.append(f"  Containers ({len(pod.spec.containers)}):")
            for container in pod.spec.containers:
                description.append(f"    - {container.name}: {container.image}")
        
        # Resource requests/limits
        if pod.spec.containers and pod.spec.containers[0].resources:
            res = pod.spec.containers[0].resources
            if res.requests:
                description.append(f"  Resource Requests: {dict(res.requests)}")
            if res.limits:
                description.append(f"  Resource Limits: {dict(res.limits)}")
        
        # Creation timestamp
        if pod.metadata.creation_timestamp:
            description.append(f"  Created: {pod.metadata.creation_timestamp}")
        
        return "\n".join(description)
        
    except ApiException as e:
        return handle_api_error(e)

def describe_deployment(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        
        # Enhanced deployment description
        description = [f"Deployment '{name}' Details:"]
        description.append(f"  Namespace: {namespace}")
        description.append(f"  Replicas: {dep.status.replicas or 0}")
        description.append(f"  Ready Replicas: {dep.status.ready_replicas or 0}")
        description.append(f"  Available Replicas: {dep.status.available_replicas or 0}")
        description.append(f"  Updated Replicas: {dep.status.updated_replicas or 0}")
        
        # Strategy
        if dep.spec.strategy:
            description.append(f"  Strategy: {dep.spec.strategy.type}")
        
        # Selector
        if dep.spec.selector and dep.spec.selector.match_labels:
            labels = ", ".join([f"{k}={v}" for k, v in dep.spec.selector.match_labels.items()])
            description.append(f"  Selector: {labels}")
        
        # Template info
        if dep.spec.template.spec.containers:
            container = dep.spec.template.spec.containers[0]
            description.append(f"  Image: {container.image}")
        
        # Creation timestamp
        if dep.metadata.creation_timestamp:
            description.append(f"  Created: {dep.metadata.creation_timestamp}")
        
        return "\n".join(description)
        
    except ApiException as e:
        return handle_api_error(e)

def describe_service(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        svc = v1.read_namespaced_service(name=name, namespace=namespace)
        
        # Enhanced service description
        description = [f"Service '{name}' Details:"]
        description.append(f"  Namespace: {namespace}")
        description.append(f"  Type: {svc.spec.type}")
        description.append(f"  Cluster IP: {svc.spec.cluster_ip}")
        
        # External IP
        if svc.spec.external_i_ps:
            description.append(f"  External IPs: {', '.join(svc.spec.external_i_ps)}")
        
        # Load balancer ingress
        if svc.status.load_balancer and svc.status.load_balancer.ingress:
            ingress_ips = [ing.ip for ing in svc.status.load_balancer.ingress if ing.ip]
            ingress_hosts = [ing.hostname for ing in svc.status.load_balancer.ingress if ing.hostname]
            if ingress_ips:
                description.append(f"  Load Balancer IPs: {', '.join(ingress_ips)}")
            if ingress_hosts:
                description.append(f"  Load Balancer Hosts: {', '.join(ingress_hosts)}")
        
        # Ports
        if svc.spec.ports:
            description.append("  Ports:")
            for port in svc.spec.ports:
                port_info = f"    - {port.port}"
                if port.target_port:
                    port_info += f"→{port.target_port}"
                if port.protocol:
                    port_info += f" ({port.protocol})"
                if port.name:
                    port_info += f" [{port.name}]"
                description.append(port_info)
        
        # Selector
        if svc.spec.selector:
            labels = ", ".join([f"{k}={v}" for k, v in svc.spec.selector.items()])
            description.append(f"  Selector: {labels}")
        
        # Creation timestamp
        if svc.metadata.creation_timestamp:
            description.append(f"  Created: {svc.metadata.creation_timestamp}")
        
        return "\n".join(description)
        
    except ApiException as e:
        return handle_api_error(e)

def describe_job(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        job = batch_v1.read_namespaced_job(name=name, namespace=namespace)
        return f"⚙️ Job '{name}' completions: {job.status.succeeded or 0}, active: {job.status.active or 0}"
    except ApiException as e:
        return handle_api_error(e)

def describe_configmap(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        cm = v1.read_namespaced_config_map(name=name, namespace=namespace)
        keys = list(cm.data.keys()) if cm.data else []
        return f"🗂️ ConfigMap '{name}' has keys: {keys}"
    except ApiException as e:
        return handle_api_error(e)

def describe_secret(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        sec = v1.read_namespaced_secret(name=name, namespace=namespace)
        keys = list(sec.data.keys()) if sec.data else []
        return f"🔒 Secret '{name}' contains {len(keys)} keys (values hidden)"
    except ApiException as e:
        return handle_api_error(e)

def describe_pvc(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        pvc = v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        return f"💾 PVC '{name}' status: {pvc.status.phase}, capacity: {pvc.status.capacity.get('storage')}"
    except ApiException as e:
        return handle_api_error(e)

def describe_replicaset(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        rs = apps_v1.read_namespaced_replica_set(name=name, namespace=namespace)
        return f"📎 ReplicaSet '{name}' replicas: {rs.status.replicas}, ready: {rs.status.ready_replicas}"
    except ApiException as e:
        return handle_api_error(e)

def describe_statefulset(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        ss = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
        return f"📘 StatefulSet '{name}' replicas: {ss.status.replicas}, ready: {ss.status.ready_replicas}"
    except ApiException as e:
        return handle_api_error(e)

def describe_daemonset(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        ds = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)
        return f"🔁 DaemonSet '{name}' scheduled: {ds.status.current_number_scheduled}, ready: {ds.status.number_ready}"
    except ApiException as e:
        return handle_api_error(e)

def describe_ingress(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        ing = networking_v1.read_namespaced_ingress(name=name, namespace=namespace)
        hosts = [rule.host for rule in ing.spec.rules] if ing.spec.rules else []
        services = []
        for rule in ing.spec.rules or []:
            if rule.http:
                for path in rule.http.paths:
                    if path.backend and path.backend.service:
                        services.append(path.backend.service.name)
        return f"🚪 Ingress '{name}' exposes hosts: {hosts or '[]'} and forwards to services: {services or '[]'}"
    except ApiException as e:
        return handle_api_error(e)

def describe_node(name):
    try:
        name = name.strip()
        node = v1.read_node(name=name)
        return f"🖥️ Node '{name}' labels: {node.metadata.labels}"
    except ApiException as e:
        return handle_api_error(e)

# ----------------------- Creation Functions -----------------------

def create_pod_from_yaml(yaml_content: str, namespace: str = None):
    """Create a pod from YAML content"""
    try:
        namespace = namespace or get_namespace()
        
        # Parse YAML content
        yaml_data = yaml.safe_load(yaml_content)
        
        # Ensure namespace is set
        if not yaml_data.get("metadata"):
            yaml_data["metadata"] = {}
        yaml_data["metadata"]["namespace"] = namespace
        
        # Create pod using Kubernetes API
        api = client.CoreV1Api()
        pod = api.create_namespaced_pod(namespace=namespace, body=yaml_data)
        
        return f"[SUCCESS] Created pod '{pod.metadata.name}' in namespace '{namespace}'"
        
    except ApiException as e:
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error creating pod: {str(e)}"

def create_pod_programmatic(name: str = "test-pod", image: str = "ubuntu", 
                          memory_limit: str = "100Mi", cpu_limit: str = "100m",
                          memory_request: str = "100Mi", cpu_request: str = "100m",
                          command: List[str] = None, namespace: str = None):
    """Create a pod programmatically with specified parameters"""
    try:
        namespace = namespace or get_namespace()
        command = command or ["sh", "-c", "echo 'Im a new pod' && sleep infinity"]
        
        validate_k8s_name(name)
        
        api = client.CoreV1Api()
        pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="main-container",
                        image=image,
                        resources=client.V1ResourceRequirements(
                            limits={"memory": memory_limit, "cpu": cpu_limit},
                            requests={"memory": memory_request, "cpu": cpu_request},
                        ),
                        command=command,
                    )
                ]
            ),
        )
        
        result = api.create_namespaced_pod(namespace=namespace, body=pod)
        return f"[SUCCESS] Created pod '{name}' in namespace '{namespace}'"
        
    except ApiException as e:
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error creating pod: {str(e)}"

def create_deployment_from_yaml(yaml_content: str, namespace: str = None):
    """Create a deployment from YAML content"""
    try:
        namespace = namespace or get_namespace()
        
        # Parse YAML content
        yaml_data = yaml.safe_load(yaml_content)
        
        # Ensure namespace is set
        if not yaml_data.get("metadata"):
            yaml_data["metadata"] = {}
        yaml_data["metadata"]["namespace"] = namespace
        
        # Create deployment using Kubernetes API
        api = client.AppsV1Api()
        deployment = api.create_namespaced_deployment(namespace=namespace, body=yaml_data)
        
        return f"[SUCCESS] Created deployment '{deployment.metadata.name}' in namespace '{namespace}'"
        
    except ApiException as e:
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error creating deployment: {str(e)}"

def create_deployment_programmatic(name: str = "test-dep", image: str = "ubuntu", 
                                 replicas: int = 1, memory_limit: str = "500Mi", 
                                 cpu_limit: str = "500m", memory_request: str = "100Mi", 
                                 cpu_request: str = "50m", command: List[str] = None, 
                                 namespace: str = None):
    """Create a deployment programmatically with specified parameters"""
    try:
        namespace = namespace or get_namespace()
        command = command or ["sh", "-c", "sleep infinity"]
        
        validate_k8s_name(name)
        
        api = client.AppsV1Api()
        
        # Create deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=name, 
                namespace=namespace,
                labels={"k8s-app": name}
            ),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(
                    match_labels={"k8s-app": name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"k8s-app": name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="main-container",
                                image=image,
                                resources=client.V1ResourceRequirements(
                                    limits={"memory": memory_limit, "cpu": cpu_limit},
                                    requests={"memory": memory_request, "cpu": cpu_request},
                                ),
                                command=command,
                            )
                        ]
                    )
                )
            )
        )
        
        result = api.create_namespaced_deployment(namespace=namespace, body=deployment)
        return f"[SUCCESS] Created deployment '{name}' in namespace '{namespace}' with {replicas} replica(s)"
        
    except ApiException as e:
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error creating deployment: {str(e)}"

def delete_pod(name: str, namespace: str = None):
    """Delete a pod by name"""
    try:
        namespace = namespace or get_namespace()
        validate_k8s_name(name)
        
        api = client.CoreV1Api()
        api.delete_namespaced_pod(name=name, namespace=namespace)
        return f"[DELETE] Deleting pod '{name}' in namespace '{namespace}' (gracefully)"
        
    except ApiException as e:
        if e.status == 404:
            return f"[INFO] Pod '{name}' not found in namespace '{namespace}'. Nothing to delete."
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error deleting pod: {str(e)}"

def delete_deployment(name: str, namespace: str = None):
    """Delete a deployment by name"""
    try:
        namespace = namespace or get_namespace()
        validate_k8s_name(name)
        
        api = client.AppsV1Api()
        propagation = client.V1DeleteOptions(propagation_policy="Foreground")
        api.delete_namespaced_deployment(name=name, namespace=namespace, body=propagation)
        return f"[DELETE] Deleting deployment '{name}' in namespace '{namespace}'"
        
    except ApiException as e:
        if e.status == 404:
            return f"[INFO] Deployment '{name}' not found in namespace '{namespace}'. Nothing to delete."
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error deleting deployment: {str(e)}"

def pod_logs(name: str, tail_lines: Optional[int] = None, namespace: str = None):
    """Get logs from a pod"""
    try:
        namespace = namespace or get_namespace()
        validate_k8s_name(name)
        
        api = client.CoreV1Api()
        logs = api.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=tail_lines)
        return f"[LOGS] Logs for pod '{name}':\n{logs}"
        
    except ApiException as e:
        if e.status == 404:
            return f"[INFO] Pod '{name}' not found in namespace '{namespace}'"
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error getting pod logs: {str(e)}"

def pod_exec(name: str, command: List[str], container: Optional[str] = None, 
           namespace: str = None):
    """Execute a command in a pod"""
    try:
        namespace = namespace or get_namespace()
        validate_k8s_name(name)
        
        api = client.CoreV1Api()
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            name,
            namespace,
            command=command,
            container=container,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        return f"[EXEC] Executed '{' '.join(command)}' in pod '{name}':\n{resp}"
        
    except ApiException as e:
        return handle_api_error(e)
    except Exception as e:
        return f"[ERROR] Error executing command in pod: {str(e)}"

# Context functions
def get_service_account(_=None):
    """Get information about the current service account."""
    try:
        # Try to read service account from the token file
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            token = f.read().strip()
        
        # Try to get service account name from the file path
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/serviceaccount.name", "r") as f:
                sa_name = f.read().strip()
                return f"Current service account: system:serviceaccount:gsoc:{sa_name}"
        except FileNotFoundError:
            # If the service account name file doesn't exist, return what we can
            return f"Current service account in gsoc namespace (token available but name not directly accessible)"
    except Exception as e:
        return f"[ERROR] Error getting service account info: {str(e)}"

def get_pod_info(_=None):
    """Get information about the current pod."""
    try:
        # Get pod name from environment variable
        pod_name = os.environ.get("HOSTNAME")
        if not pod_name:
            return "[ERROR] Could not determine pod name from HOSTNAME environment variable"
        
        # Get pod details
        pod = v1.read_namespaced_pod(name=pod_name, namespace=CURRENT_NAMESPACE)
        
        return f"📋 Current pod: {pod_name}\nNamespace: {CURRENT_NAMESPACE}\nStatus: {pod.status.phase}\nNode: {pod.spec.node_name}\nService Account: {pod.spec.service_account_name}"
    except Exception as e:
        return f"[ERROR] Error getting pod info: {str(e)}"

# Check permissions function
def check_permissions(_=None):
    """Check what permissions the current service account has."""
    try:
        # Try to access self subject access review API to check permissions
        from kubernetes.client import V1SelfSubjectAccessReview, V1SelfSubjectAccessReviewSpec, V1ResourceAttributes
        
        # Check if we can list pods
        access_review = V1SelfSubjectAccessReview(
            spec=V1SelfSubjectAccessReviewSpec(
                resource_attributes=V1ResourceAttributes(
                    namespace=CURRENT_NAMESPACE,
                    verb="list",
                    resource="pods"
                )
            )
        )
        
        response = auth_v1.create_self_subject_access_review(access_review)
        if response.status.allowed:
            return "✅ You have permission to list pods in gsoc namespace"
        else:
            return f"[ERROR] Permission denied: {response.status.reason}"
    except Exception as e:
        return f"[ERROR] Error checking permissions: {str(e)}"

# Action registry
KNOWN_ACTIONS = {
    # LIST actions
    "list_pods": list_pods,
    "list_deployments": list_deployments,
    "list_services": list_services,
    "list_jobs": list_jobs,
    "list_configmaps": list_configmaps,
    "list_secrets": list_secrets,
    "list_pvcs": list_pvcs,
    "list_replicasets": list_replicasets,
    "list_statefulsets": list_statefulsets,
    "list_daemonsets": list_daemonsets,
    "list_ingresses": list_ingresses,
    "list_events": list_events,
    "list_nodes": list_nodes,
    # DESCRIBE actions
    "describe_pod": describe_pod,
    "describe_deployment": describe_deployment,
    "describe_service": describe_service,
    "describe_job": describe_job,
    "describe_configmap": describe_configmap,
    "describe_secret": describe_secret,
    "describe_pvc": describe_pvc,
    "describe_replicaset": describe_replicaset,
    "describe_statefulset": describe_statefulset,
    "describe_daemonset": describe_daemonset,
    "describe_ingress": describe_ingress,
    "describe_node": describe_node,
    # CREATE actions
    "create_pod": create_pod_programmatic,
    "create_pod_yaml": create_pod_from_yaml,
    "create_deployment": create_deployment_programmatic,
    "create_deployment_yaml": create_deployment_from_yaml,
    # DELETE actions
    "delete_pod": delete_pod,
    "delete_deployment": delete_deployment,
    # UTILITY actions
    "pod_logs": pod_logs,
    "pod_exec": pod_exec,
    # CONTEXT actions
    "check_permissions": check_permissions,
    "get_service_account": get_service_account,
    "get_pod_info": get_pod_info,
}

# Action pattern
ACTION_RE = re.compile(r'^Action: (\w+):(.*)$')

def query(agent, question, max_turns=15):
    """Process a user query through the agent."""
    i = 0
    next_prompt = question
    while i < max_turns:
        print(f"\n--- Turn {i+1} ---")
        i += 1
        print("Prompt to bot:", next_prompt)
        result = agent(next_prompt)
        print("Bot response:\n", result)
        
        actions = [
            action_match
            for action in result.split('\n')
            if (action_match := ACTION_RE.match(action))
        ]
        
        if actions:
            for action_match in actions:
                action, action_input = action_match.groups()
                if action not in KNOWN_ACTIONS:
                    raise Exception(f"Unknown action: {action}: {action_input}")
                print(f" -- Running action '{action}' with input '{action_input}'")
                observation = KNOWN_ACTIONS[action](action_input)
                print("Observation:", observation)
                next_prompt = f"Observation: {observation}"
        else:
            print("No more actions. Halting.")
            return

def create_resource_from_yaml(yaml_content: str, namespace: str = None) -> str:
    """Create Kubernetes resource from YAML content"""
    try:
        namespace = namespace or CURRENT_NAMESPACE
        
        # Parse YAML content
        import tempfile
        import os
        
        # Create temporary file with YAML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_yaml_file = f.name
        
        try:
            # Use Kubernetes utilities to create resource from YAML
            k8s_client = client.ApiClient()
            create_from_yaml(k8s_client, temp_yaml_file, namespace=namespace)
            
            # Extract resource info for response
            yaml_data = yaml.safe_load(yaml_content)
            resource_kind = yaml_data.get('kind', 'Resource')
            resource_name = yaml_data.get('metadata', {}).get('name', 'unnamed')
            
            return f"[SUCCESS] Created {resource_kind} '{resource_name}' in namespace '{namespace}'"
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_yaml_file):
                os.unlink(temp_yaml_file)
                
    except Exception as e:
        return f"[ERROR] Failed to create resource from YAML: {str(e)}"

def main():
    """Main interactive loop."""
    print("Kubernetes ReAct Agent - Operating in 'gsoc' namespace")
    print("Type 'exit' or 'quit' to exit the program\n")
    
    # Initialize agent with system prompt
    agent = Agent(PROMPT)
    
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ('exit', 'quit'):
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            query(agent, user_input)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()