#!/usr/bin/env python3
"""
Kubernetes ReAct Agent - Terminal Interface
A simple agent that helps you interact with Kubernetes using natural language.
Designed to run inside a Kubernetes pod in the 'gsoc' namespace.
"""

import os
import re
import sys
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
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
(Observation: ❌ Permission denied: User "system:serviceaccount:gsoc:default" cannot list resource "pods" in API group "" in the namespace "gsoc")
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
        raise ValueError(f"❌ Invalid Kubernetes resource name: '{name}'. Must match RFC1123 format.")
    return name

# Helper function to handle API errors
def handle_api_error(e):
    """Handle Kubernetes API errors and return user-friendly messages."""
    if e.status == 403:
        return f"❌ Permission denied: {e.reason}"
    elif e.status == 404:
        return f"❌ Resource not found: {e.reason}"
    else:
        return f"❌ API error ({e.status}): {e.reason}"

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
        return f"📋 Pod '{name}' phase: {pod.status.phase}, node: {pod.spec.node_name}"
    except ApiException as e:
        return handle_api_error(e)

def describe_deployment(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        return f"📦 Deployment '{name}' has {dep.status.replicas or 0} replicas and {dep.status.ready_replicas or 0} ready."
    except ApiException as e:
        return handle_api_error(e)

def describe_service(name):
    try:
        name = name.strip()
        namespace = get_namespace()
        svc = v1.read_namespaced_service(name=name, namespace=namespace)
        return f"🌐 Service '{name}' type: {svc.spec.type}, cluster IP: {svc.spec.cluster_ip}"
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
        return f"❌ Error getting service account info: {str(e)}"

def get_pod_info(_=None):
    """Get information about the current pod."""
    try:
        # Get pod name from environment variable
        pod_name = os.environ.get("HOSTNAME")
        if not pod_name:
            return "❌ Could not determine pod name from HOSTNAME environment variable"
        
        # Get pod details
        pod = v1.read_namespaced_pod(name=pod_name, namespace=CURRENT_NAMESPACE)
        
        return f"📋 Current pod: {pod_name}\nNamespace: {CURRENT_NAMESPACE}\nStatus: {pod.status.phase}\nNode: {pod.spec.node_name}\nService Account: {pod.spec.service_account_name}"
    except Exception as e:
        return f"❌ Error getting pod info: {str(e)}"

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
            return f"❌ Permission denied: {response.status.reason}"
    except Exception as e:
        return f"❌ Error checking permissions: {str(e)}"

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