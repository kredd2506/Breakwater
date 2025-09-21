#!/usr/bin/env python3
"""
Enhanced Kubernetes Tool Calling System
Integrates template functionality with intelligent routing for expanded K8s operations
"""

import os
import re
import sys
import yaml
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.stream import stream
from kubernetes.utils import create_from_yaml


class K8sToolCaller:
    """Enhanced Kubernetes operations with tool calling capabilities"""
    
    def __init__(self):
        self.namespace = "gsoc"
        self._init_k8s_client()
        
    def _init_k8s_client(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
            self.config_type = "incluster"
        except config.ConfigException:
            try:
                config.load_kube_config()
                self.config_type = "kubeconfig"
            except config.ConfigException:
                raise Exception("Could not configure Kubernetes client")
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.auth_v1 = client.AuthorizationV1Api()
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Universal tool calling interface for K8s operations
        
        Available tools:
        - list_pods: List pods in namespace
        - describe_pod: Get detailed pod information
        - get_pod_logs: Retrieve pod logs
        - exec_pod_command: Execute command in pod
        - create_pod_yaml: Create pod from YAML
        - delete_pod: Delete a pod
        - list_deployments: List deployments
        - create_deployment_yaml: Create deployment from YAML
        - delete_deployment: Delete deployment
        - get_events: List namespace events
        - pod_port_forward: Port forward to pod
        - check_permissions: Check RBAC permissions
        """
        
        tools = {
            'list_pods': self._list_pods,
            'describe_pod': self._describe_pod,
            'get_pod_logs': self._get_pod_logs,
            'exec_pod_command': self._exec_pod_command,
            'create_pod_yaml': self._create_pod_yaml,
            'delete_pod': self._delete_pod,
            'list_deployments': self._list_deployments,
            'create_deployment_yaml': self._create_deployment_yaml,
            'delete_deployment': self._delete_deployment,
            'get_events': self._get_events,
            'pod_port_forward': self._pod_port_forward,
            'check_permissions': self._check_permissions,
            'create_pod_from_template': self._create_pod_from_template,
            'delete_one_pod_by_label': self._delete_one_pod_by_label
        }
        
        if tool_name not in tools:
            return {"error": f"Unknown tool: {tool_name}", "available_tools": list(tools.keys())}
        
        try:
            return tools[tool_name](**kwargs)
        except Exception as e:
            return {"error": str(e), "tool": tool_name, "args": kwargs}
    
    def _list_pods(self, label_selector: str = None, field_selector: str = None) -> Dict[str, Any]:
        """List pods with optional selectors"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector,
                field_selector=field_selector
            )
            
            pod_list = []
            for pod in pods.items:
                pod_info = {
                    'name': pod.metadata.name,
                    'phase': pod.status.phase,
                    'node': pod.spec.node_name,
                    'pod_ip': pod.status.pod_ip,
                    'start_time': pod.status.start_time.isoformat() if pod.status.start_time else None,
                    'containers': []
                }
                
                if pod.status.container_statuses:
                    for cs in pod.status.container_statuses:
                        container_info = {
                            'name': cs.name,
                            'image': cs.image,
                            'ready': cs.ready,
                            'restart_count': cs.restart_count
                        }
                        pod_info['containers'].append(container_info)
                
                pod_list.append(pod_info)
            
            return {"pods": pod_list, "count": len(pod_list)}
            
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _describe_pod(self, pod_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific pod"""
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=self.namespace)
            
            pod_info = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'labels': pod.metadata.labels,
                'annotations': pod.metadata.annotations,
                'phase': pod.status.phase,
                'node': pod.spec.node_name,
                'pod_ip': pod.status.pod_ip,
                'start_time': pod.status.start_time.isoformat() if pod.status.start_time else None,
                'containers': [],
                'volumes': []
            }
            
            # Container details
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    container_info = {
                        'name': cs.name,
                        'image': cs.image,
                        'ready': cs.ready,
                        'restart_count': cs.restart_count,
                        'state': {}
                    }
                    
                    if cs.state:
                        if cs.state.running:
                            container_info['state'] = {'running': cs.state.running.started_at.isoformat()}
                        elif cs.state.terminated:
                            container_info['state'] = {
                                'terminated': {
                                    'reason': cs.state.terminated.reason,
                                    'exit_code': cs.state.terminated.exit_code
                                }
                            }
                        elif cs.state.waiting:
                            container_info['state'] = {'waiting': cs.state.waiting.reason}
                    
                    pod_info['containers'].append(container_info)
            
            # Volume information
            if pod.spec.volumes:
                for vol in pod.spec.volumes:
                    volume_info = {'name': vol.name}
                    if vol.config_map:
                        volume_info['type'] = 'configMap'
                        volume_info['source'] = vol.config_map.name
                    elif vol.secret:
                        volume_info['type'] = 'secret'
                        volume_info['source'] = vol.secret.secret_name
                    elif vol.persistent_volume_claim:
                        volume_info['type'] = 'pvc'
                        volume_info['source'] = vol.persistent_volume_claim.claim_name
                    
                    pod_info['volumes'].append(volume_info)
            
            # Recent events
            field_selector = f"involvedObject.kind=Pod,involvedObject.name={pod_name}"
            events = self.v1.list_namespaced_event(
                namespace=self.namespace,
                field_selector=field_selector
            )
            
            pod_info['events'] = []
            for event in sorted(events.items, key=lambda e: e.metadata.creation_timestamp or 0):
                event_info = {
                    'time': event.metadata.creation_timestamp.isoformat() if event.metadata.creation_timestamp else None,
                    'reason': event.reason,
                    'message': event.message,
                    'type': event.type
                }
                pod_info['events'].append(event_info)
            
            return pod_info
            
        except ApiException as e:
            if e.status == 404:
                return {"error": f"Pod '{pod_name}' not found in namespace '{self.namespace}'"}
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _get_pod_logs(self, pod_name: str, container: str = None, tail_lines: int = None, follow: bool = False) -> Dict[str, Any]:
        """Get logs from a pod"""
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                container=container,
                tail_lines=tail_lines,
                follow=follow
            )
            
            return {
                "pod": pod_name,
                "container": container,
                "logs": logs,
                "tail_lines": tail_lines
            }
            
        except ApiException as e:
            if e.status == 404:
                return {"error": f"Pod '{pod_name}' not found in namespace '{self.namespace}'"}
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _exec_pod_command(self, pod_name: str, command: List[str], container: str = None, capture_output: bool = True) -> Dict[str, Any]:
        """Execute command in a pod"""
        try:
            if capture_output:
                resp = stream(
                    self.v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    self.namespace,
                    command=command,
                    container=container,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                    _preload_content=False
                )
                
                output = ""
                while resp.is_open():
                    resp.update(timeout=1)
                    if resp.peek_stdout():
                        output += resp.read_stdout()
                    if resp.peek_stderr():
                        output += resp.read_stderr()
                resp.close()
                
                return {
                    "pod": pod_name,
                    "container": container,
                    "command": command,
                    "output": output
                }
            else:
                # Interactive mode
                resp = stream(
                    self.v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    self.namespace,
                    command=command,
                    container=container,
                    stderr=True,
                    stdin=True,
                    stdout=True,
                    tty=True
                )
                return {"status": "Interactive session started"}
                
        except ApiException as e:
            if e.status == 404:
                return {"error": f"Pod '{pod_name}' not found in namespace '{self.namespace}'"}
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _create_pod_yaml(self, yaml_content: str = None, yaml_file: str = None) -> Dict[str, Any]:
        """Create pod from YAML content or file"""
        try:
            if yaml_file and Path(yaml_file).exists():
                with open(yaml_file, 'r') as f:
                    yaml_content = f.read()
            
            if not yaml_content:
                return {"error": "No YAML content provided"}
            
            yaml_obj = yaml.safe_load(yaml_content)
            if yaml_obj.get('kind') != 'Pod':
                return {"error": "YAML must be a Pod manifest"}
            
            pod = client.V1Pod(**yaml_obj)
            result = self.v1.create_namespaced_pod(namespace=self.namespace, body=pod)
            
            return {
                "status": "created",
                "pod_name": result.metadata.name,
                "namespace": result.metadata.namespace
            }
            
        except yaml.YAMLError as e:
            return {"error": f"YAML parsing error: {str(e)}"}
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _create_pod_from_template(self, name: str = "test-pod", image: str = "ubuntu", command: List[str] = None) -> Dict[str, Any]:
        """Create pod programmatically from template"""
        try:
            if not command:
                command = ["sh", "-c", "echo 'Pod created from template' && sleep infinity"]
            
            pod = client.V1Pod(
                api_version="v1",
                kind="Pod",
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="main",
                            image=image,
                            resources=client.V1ResourceRequirements(
                                limits={"memory": "100Mi", "cpu": "100m"},
                                requests={"memory": "100Mi", "cpu": "100m"}
                            ),
                            command=command
                        )
                    ]
                )
            )
            
            result = self.v1.create_namespaced_pod(namespace=self.namespace, body=pod)
            
            return {
                "status": "created",
                "pod_name": result.metadata.name,
                "image": image,
                "command": command
            }
            
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _delete_pod(self, pod_name: str, grace_period_seconds: int = 0) -> Dict[str, Any]:
        """Delete a pod"""
        try:
            body = client.V1DeleteOptions(grace_period_seconds=grace_period_seconds)
            result = self.v1.delete_namespaced_pod(
                name=pod_name,
                namespace=self.namespace,
                body=body
            )
            
            return {
                "status": "deleted",
                "pod_name": pod_name,
                "grace_period": grace_period_seconds
            }
            
        except ApiException as e:
            if e.status == 404:
                return {"error": f"Pod '{pod_name}' not found in namespace '{self.namespace}'"}
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _delete_one_pod_by_label(self, label_selector: str) -> Dict[str, Any]:
        """Delete one pod matching label selector"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )
            
            if not pods.items:
                return {"error": f"No pods found with selector '{label_selector}'"}
            
            pod_name = pods.items[0].metadata.name
            return self._delete_pod(pod_name)
            
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _list_deployments(self) -> Dict[str, Any]:
        """List deployments in namespace"""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=self.namespace)
            
            deployment_list = []
            for dep in deployments.items:
                dep_info = {
                    'name': dep.metadata.name,
                    'replicas': dep.spec.replicas,
                    'ready_replicas': dep.status.ready_replicas or 0,
                    'available_replicas': dep.status.available_replicas or 0,
                    'labels': dep.metadata.labels,
                    'creation_time': dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None
                }
                deployment_list.append(dep_info)
            
            return {"deployments": deployment_list, "count": len(deployment_list)}
            
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _create_deployment_yaml(self, yaml_content: str = None, yaml_file: str = None) -> Dict[str, Any]:
        """Create deployment from YAML"""
        try:
            if yaml_file and Path(yaml_file).exists():
                with open(yaml_file, 'r') as f:
                    yaml_content = f.read()
            
            if not yaml_content:
                return {"error": "No YAML content provided"}
            
            yaml_obj = yaml.safe_load(yaml_content)
            if yaml_obj.get('kind') != 'Deployment':
                return {"error": "YAML must be a Deployment manifest"}
            
            result = create_from_yaml(
                k8s_client=self.apps_v1.api_client,
                yaml_object=yaml_obj,
                namespace=self.namespace
            )
            
            return {
                "status": "created",
                "deployment_name": yaml_obj['metadata']['name'],
                "namespace": self.namespace
            }
            
        except yaml.YAMLError as e:
            return {"error": f"YAML parsing error: {str(e)}"}
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _delete_deployment(self, deployment_name: str) -> Dict[str, Any]:
        """Delete a deployment"""
        try:
            propagation = client.V1DeleteOptions(propagation_policy="Foreground")
            result = self.apps_v1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=propagation
            )
            
            return {
                "status": "deleted",
                "deployment_name": deployment_name,
                "propagation_policy": "Foreground"
            }
            
        except ApiException as e:
            if e.status == 404:
                return {"error": f"Deployment '{deployment_name}' not found in namespace '{self.namespace}'"}
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _get_events(self, field_selector: str = None) -> Dict[str, Any]:
        """Get namespace events"""
        try:
            events = self.v1.list_namespaced_event(
                namespace=self.namespace,
                field_selector=field_selector
            )
            
            event_list = []
            for event in sorted(events.items, key=lambda e: e.metadata.creation_timestamp or 0):
                event_info = {
                    'time': event.metadata.creation_timestamp.isoformat() if event.metadata.creation_timestamp else None,
                    'object': f"{event.involved_object.kind}/{event.involved_object.name}",
                    'reason': event.reason,
                    'message': event.message,
                    'type': event.type,
                    'count': event.count
                }
                event_list.append(event_info)
            
            return {"events": event_list, "count": len(event_list)}
            
        except ApiException as e:
            return {"error": f"API Exception: {e.reason}", "status": e.status}
    
    def _pod_port_forward(self, pod_name: str, local_port: int, pod_port: int) -> Dict[str, Any]:
        """Port forward to a pod (requires kubectl)"""
        try:
            cmd = [
                "kubectl", "port-forward",
                f"pod/{pod_name}",
                f"{local_port}:{pod_port}",
                "-n", self.namespace
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return {
                "status": "started",
                "pod_name": pod_name,
                "local_port": local_port,
                "pod_port": pod_port,
                "process_id": process.pid,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {"error": f"Port forward failed: {str(e)}"}
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check current RBAC permissions"""
        try:
            # Check if we can perform various operations
            permissions = {}
            
            test_operations = [
                ("get", "pods", ""),
                ("list", "pods", ""),
                ("create", "pods", ""),
                ("delete", "pods", ""),
                ("get", "deployments", "apps"),
                ("list", "deployments", "apps"),
                ("create", "deployments", "apps"),
                ("delete", "deployments", "apps"),
                ("get", "services", ""),
                ("list", "events", "")
            ]
            
            for verb, resource, group in test_operations:
                try:
                    body = client.V1SelfSubjectAccessReview(
                        spec=client.V1SelfSubjectAccessReviewSpec(
                            resource_attributes=client.V1ResourceAttributes(
                                namespace=self.namespace,
                                verb=verb,
                                group=group,
                                resource=resource
                            )
                        )
                    )
                    
                    result = self.auth_v1.create_self_subject_access_review(body=body)
                    permissions[f"{verb}_{resource}"] = result.status.allowed
                    
                except Exception as e:
                    permissions[f"{verb}_{resource}"] = f"error: {str(e)}"
            
            return {
                "namespace": self.namespace,
                "permissions": permissions,
                "config_type": self.config_type
            }
            
        except Exception as e:
            return {"error": f"Permission check failed: {str(e)}"}


# Convenience functions for direct usage
def create_tool_caller() -> K8sToolCaller:
    """Create and return a K8sToolCaller instance"""
    return K8sToolCaller()


def call_k8s_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to call a K8s tool"""
    caller = create_tool_caller()
    return caller.call_tool(tool_name, **kwargs)


if __name__ == "__main__":
    # Demo usage
    import json
    
    caller = create_tool_caller()
    
    print("=== Checking permissions ===")
    perms = caller.call_tool("check_permissions")
    print(json.dumps(perms, indent=2))
    
    print("\n=== Listing pods ===")
    pods = caller.call_tool("list_pods")
    print(json.dumps(pods, indent=2))
    
    print("\n=== Getting events ===")
    events = caller.call_tool("get_events")
    print(json.dumps(events, indent=2))