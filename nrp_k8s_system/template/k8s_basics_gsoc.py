#!/usr/bin/env python3
"""
k8s_basics.py — Minimal Kubernetes Python API helpers that mirror your tutorial

What this script can do (no kubectl required):
- Write the sample YAMLs to disk (pod1.yaml, dep1.yaml)
- Create/Delete the sample Pod from YAML
- Create the same Pod programmatically (no YAML)
- Show Pods, Events, Logs
- "Describe" a Pod (prints key fields similar to kubectl describe)
- Exec an interactive shell or run a one-off command in a container
- Create/Delete the sample Deployment from YAML
- Delete ONE Pod from the Deployment to demonstrate self-healing

Prereqs:
  pip install kubernetes pyyaml
  Ensure your kubeconfig is available:
    - Default: ~/.kube/config
    - Or set KUBECONFIG env var
  If running inside a cluster, the script will try in-cluster config.

Examples:
  python k8s_basics.py init-yaml
  python k8s_basics.py create-pod-yaml --namespace default --file pod1.yaml
  python k8s_basics.py get-pods --namespace default
  python k8s_basics.py pod-logs --namespace default --name test-pod
  python k8s_basics.py pod-exec --namespace default --name test-pod -- cmd /bin/bash
  python k8s_basics.py delete-pod-yaml --namespace default --file pod1.yaml

  python k8s_basics.py create-dep-yaml --namespace default --file dep1.yaml
  python k8s_basics.py delete-one-dep-pod --namespace default --label k8s-app=test-dep
  python k8s_basics.py delete-dep-yaml --namespace default --file dep1.yaml
"""

import argparse
import sys
import time
from typing import List, Optional, Tuple

import yaml

from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client import ApiException
from kubernetes.utils import create_from_yaml


POD1_YAML = """apiVersion: v1
kind: Pod
metadata:
  name: test-pod
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

DEP1_YAML = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-dep
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


def load_kube_config():
    """Try local kubeconfig, fall back to in-cluster."""
    try:
        config.load_kube_config()
        return "kubeconfig"
    except Exception:
        try:
            config.load_incluster_config()
            return "incluster"
        except Exception as e:
            print("❌ Unable to load Kubernetes config (neither kubeconfig nor in-cluster).")
            raise e


def init_yaml_files(pod_path: str, dep_path: str):
    Path(pod_path).write_text(POD1_YAML)
    Path(dep_path).write_text(DEP1_YAML)
    print(f"✅ Wrote {pod_path} and {dep_path}")


def create_pod_from_yaml(namespace: str, yaml_path: str):
    api = client.CoreV1Api()
    create_from_yaml(k8s_client=api.api_client, yaml_file=yaml_path, namespace=namespace)
    print(f"✅ Created resources in {yaml_path} in namespace '{namespace}'")


def delete_pod_from_yaml(namespace: str, yaml_path: str):
    # Minimal delete handling: read YAML, delete the named Pod
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data.get("kind") != "Pod":
        raise ValueError("YAML is not a Pod manifest")
    name = data["metadata"]["name"]
    api = client.CoreV1Api()
    try:
        api.delete_namespaced_pod(name=name, namespace=namespace)
        print(f"🗑️  Deleting pod '{name}' in '{namespace}' (gracefully)")
    except ApiException as e:
        if e.status == 404:
            print(f"ℹ️ Pod '{name}' not found in '{namespace}'. Nothing to delete.")
        else:
            raise


def create_deployment_from_yaml(namespace: str, yaml_path: str):
    api_apps = client.AppsV1Api()
    create_from_yaml(k8s_client=api_apps.api_client, yaml_file=yaml_path, namespace=namespace)
    print(f"✅ Created resources in {yaml_path} in namespace '{namespace}'")


def delete_deployment_from_yaml(namespace: str, yaml_path: str):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data.get("kind") != "Deployment":
        raise ValueError("YAML is not a Deployment manifest")
    name = data["metadata"]["name"]
    api_apps = client.AppsV1Api()
    propagation = client.V1DeleteOptions(propagation_policy="Foreground")
    try:
        api_apps.delete_namespaced_deployment(name=name, namespace=namespace, body=propagation)
        print(f"🗑️  Deleting deployment '{name}' in '{namespace}'")
    except ApiException as e:
        if e.status == 404:
            print(f"ℹ️ Deployment '{name}' not found in '{namespace}'. Nothing to delete.")
        else:
            raise


def create_pod_programmatic(namespace: str, name: str = "test-pod"):
    api = client.CoreV1Api()
    pod = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1PodSpec(
            containers=[
                client.V1Container(
                    name="mypod",
                    image="ubuntu",
                    resources=client.V1ResourceRequirements(
                        limits={"memory": "100Mi", "cpu": "100m"},
                        requests={"memory": "100Mi", "cpu": "100m"},
                    ),
                    command=["sh", "-c", "echo 'Im a new pod' && sleep infinity"],
                )
            ]
        ),
    )
    api.create_namespaced_pod(namespace=namespace, body=pod)
    print(f"✅ Created Pod '{name}' in '{namespace}'")


def get_pods(namespace: str):
    api = client.CoreV1Api()
    pods = api.list_namespaced_pod(namespace=namespace)
    if not pods.items:
        print("(no pods)")
        return
    for p in pods.items:
        ip = p.status.pod_ip or "-"
        phase = p.status.phase
        print(f"{p.metadata.name:40}  {phase:10}  IP={ip}")


def get_events(namespace: str):
    api = client.CoreV1Api()
    evs = api.list_namespaced_event(namespace=namespace)
    sorted_evs = sorted(evs.items, key=lambda e: e.metadata.creation_timestamp or 0)
    for e in sorted_evs:
        ts = e.metadata.creation_timestamp
        print(f"{ts}  {e.involved_object.kind}/{e.involved_object.name}: {e.reason} - {e.message}")


def describe_pod(namespace: str, name: str):
    api = client.CoreV1Api()
    try:
        p = api.read_namespaced_pod(name=name, namespace=namespace)
    except ApiException as e:
        if e.status == 404:
            print(f"Pod '{name}' not found in '{namespace}'")
            return
        raise
    print(f"Name:        {p.metadata.name}")
    print(f"Namespace:   {p.metadata.namespace}")
    print(f"Node:        {p.spec.node_name}")
    print(f"StartTime:   {p.status.start_time}")
    print(f"Phase:       {p.status.phase}")
    if p.status.container_statuses:
        for cs in p.status.container_statuses:
            print(f"\nContainer:   {cs.name}")
            print(f"  Image:     {cs.image}")
            print(f"  Ready:     {cs.ready}")
            if cs.state and cs.state.running:
                print(f"  Running:   {cs.state.running.started_at}")
            if cs.state and cs.state.terminated:
                print(f"  Terminated:{cs.state.terminated.reason}")
            if cs.state and cs.state.waiting:
                print(f"  Waiting:   {cs.state.waiting.reason}")
    # Show recent events for this Pod
    print("\nEvents:")
    field_selector = f"involvedObject.kind=Pod,involvedObject.name={name}"
    evs = api.list_namespaced_event(namespace=namespace, field_selector=field_selector)
    evs_sorted = sorted(evs.items, key=lambda e: e.metadata.creation_timestamp or 0)
    for e in evs_sorted:
        print(f"  {e.metadata.creation_timestamp}  {e.reason} - {e.message}")


def pod_logs(namespace: str, name: str, tail_lines: Optional[int] = None):
    api = client.CoreV1Api()
    try:
        logs = api.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=tail_lines)
    except ApiException as e:
        if e.status == 404:
            print(f"Pod '{name}' not found in '{namespace}'")
            return
        raise
    print(logs)


def pod_exec(namespace: str, name: str, command: List[str], container: Optional[str] = None, tty: bool = False, stdin: bool = False):
    api = client.CoreV1Api()
    resp = stream(
        api.connect_get_namespaced_pod_exec,
        name,
        namespace,
        command=command,
        container=container,
        stderr=True,
        stdin=stdin,
        stdout=True,
        tty=tty,
    )
    # stream returns the captured output for non-interactive cases
    if not tty and not stdin:
        print(resp)


def delete_one_pod_by_label(namespace: str, label_selector: str):
    api = client.CoreV1Api()
    pods = api.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
    if not pods.items:
        print(f"No pods found with selector '{label_selector}' in '{namespace}'")
        return
    name = pods.items[0].metadata.name
    api.delete_namespaced_pod(name=name, namespace=namespace)
    print(f"🗑️  Deleted Pod '{name}' in '{namespace}' — deployment/replicaset should recreate it shortly.")


def main():
    parser = argparse.ArgumentParser(description="Kubernetes Python API helpers for your tutorial")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-yaml", help="Write pod1.yaml and dep1.yaml to disk")
    p_init.add_argument("--pod-file", default="pod1.yaml")
    p_init.add_argument("--dep-file", default="dep1.yaml")

    p_cp = sub.add_parser("create-pod-yaml", help="Create the sample Pod from YAML")
    p_cp.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_cp.add_argument("--file", default="pod1.yaml")

    p_cpp = sub.add_parser("create-pod-prog", help="Create the sample Pod programmatically")
    p_cpp.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_cpp.add_argument("--name", default="test-pod")

    p_dp = sub.add_parser("delete-pod-yaml", help="Delete the sample Pod from YAML")
    p_dp.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_dp.add_argument("--file", default="pod1.yaml")

    p_gp = sub.add_parser("get-pods", help="List pods")
    p_gp.# Namespace forced to gsoc
    "gsoc" = "gsoc"

    p_ev = sub.add_parser("get-events", help="List namespace events (sorted)")
    p_ev.# Namespace forced to gsoc
    "gsoc" = "gsoc"

    p_desc = sub.add_parser("describe-pod", help="Show key info + events about a Pod")
    p_desc.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_desc.add_argument("--name", required=True)

    p_logs = sub.add_parser("pod-logs", help="Show Pod logs")
    p_logs.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_logs.add_argument("--name", required=True)
    p_logs.add_argument("--tail", type=int, default=None)

    p_exec = sub.add_parser("pod-exec", help="Exec into Pod (non-interactive by default)")
    p_exec.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_exec.add_argument("--name", required=True)
    p_exec.add_argument("--container", default=None)
    p_exec.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run, e.g. -- /bin/bash")
    p_exec.add_argument("--tty", action="store_true", help="Allocate a TTY (may require stdin handling)")

    p_cdy = sub.add_parser("create-dep-yaml", help="Create the sample Deployment from YAML")
    p_cdy.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_cdy.add_argument("--file", default="dep1.yaml")

    p_ddy = sub.add_parser("delete-dep-yaml", help="Delete the sample Deployment from YAML")
    p_ddy.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_ddy.add_argument("--file", default="dep1.yaml")

    p_ddp = sub.add_parser("delete-one-dep-pod", help="Delete one Pod by label (e.g., k8s-app=test-dep)")
    p_ddp.# Namespace forced to gsoc
    "gsoc" = "gsoc"
    p_ddp.add_argument("--label", required=True)

    args = parser.parse_args()

    load_kube_config()

    if args.cmd == "init-yaml":
        init_yaml_files(args.pod_file, args.dep_file)

    elif args.cmd == "create-pod-yaml":
        create_pod_from_yaml("gsoc", args.file)

    elif args.cmd == "create-pod-prog":
        create_pod_programmatic("gsoc", args.name)

    elif args.cmd == "delete-pod-yaml":
        delete_pod_from_yaml("gsoc", args.file)

    elif args.cmd == "get-pods":
        get_pods("gsoc")

    elif args.cmd == "get-events":
        get_events("gsoc")

    elif args.cmd == "describe-pod":
        describe_pod("gsoc", args.name)

    elif args.cmd == "pod-logs":
        pod_logs("gsoc", args.name, tail_lines=args.tail)

    elif args.cmd == "pod-exec":
        # Handle pass-through of command after "--"
        cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
        if not cmd:
            print("Provide a command to run after '--', e.g., -- /bin/bash")
            sys.exit(2)
        pod_exec("gsoc", args.name, command=cmd, container=args.container, tty=args.tty)

    elif args.cmd == "create-dep-yaml":
        create_deployment_from_yaml("gsoc", args.file)

    elif args.cmd == "delete-dep-yaml":
        delete_deployment_from_yaml("gsoc", args.file)

    elif args.cmd == "delete-one-dep-pod":
        delete_one_pod_by_label("gsoc", args.label)


if __name__ == "__main__":
    from pathlib import Path
    main()
