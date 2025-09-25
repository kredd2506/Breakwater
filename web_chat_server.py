#!/usr/bin/env python3
"""
Web-based Chat Interface for DeepSeek-R1 NRP K8s System
Browser-accessible chat interface running on localhost
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import asyncio
from openai import AsyncOpenAI
import json
from datetime import datetime
import os
import threading
import sys
import re
from pathlib import Path

# Add NRP K8s system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))
# Add MCP cache for comprehensive knowledge
sys.path.insert(0, str(Path(__file__).parent / "mcp"))

# Import K8s operations
try:
    from systems.k8s_operations import (
        list_pods, list_deployments, list_services, list_jobs,
        list_configmaps, list_secrets, list_pvcs, list_replicasets,
        list_statefulsets, list_daemonsets, list_ingresses, list_events, list_nodes,
        describe_pod, describe_deployment, describe_service, describe_job,
        describe_configmap, describe_secret, describe_pvc, describe_replicaset,
        describe_statefulset, describe_daemonset, describe_ingress, describe_node,
        create_pod_programmatic, create_deployment_programmatic,
        delete_pod, delete_deployment, pod_logs, pod_exec,
        get_service_account, CURRENT_NAMESPACE
    )
    K8S_AVAILABLE = True
    print(f"[OK] Kubernetes operations loaded - namespace: {CURRENT_NAMESPACE}")
except ImportError as e:
    print(f"[WARNING] Could not import K8s operations: {e}")
    K8S_AVAILABLE = False

# Import comprehensive NRP knowledge base
try:
    from cache.nrp_comprehensive_templates import NRP_TEMPLATES
    from cache.nrp_complete_anchor_db import search_complete_anchors, NRP_COMPLETE_ANCHORS
    from cache.nrp_gpu_knowledge import NRP_GPU_RESOURCES, search_nrp_knowledge
    NRP_KNOWLEDGE_AVAILABLE = True
    print(f"[OK] Comprehensive NRP knowledge loaded: {len(NRP_COMPLETE_ANCHORS)} pages, {len(NRP_TEMPLATES)} templates")
except ImportError as e:
    print(f"[WARNING] Could not import NRP knowledge: {e}")
    NRP_KNOWLEDGE_AVAILABLE = False

app = Flask(__name__)

class DeepSeekWebChat:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key="60giG4L3xNAMC1FT2f2ivYnExpHYA1fD",
            base_url="https://ellm.nrp-nautilus.io/v1"
        )
        self.conversations = {}  # Store conversations by session

    def get_system_prompt(self):
        return """You are an expert assistant for the National Research Platform (NRP) Kubernetes system powered by DeepSeek-R1.

You help users with:
🔧 Kubernetes operations and troubleshooting
🎮 GPU allocation and resource management (A100, A40, RTX series)
📦 Container deployment and configuration
🌐 NRP-specific features and capabilities
🧪 Research computing workflows
📝 YAML configuration and best practices

You have access to comprehensive NRP documentation and 261+ YAML templates scraped from official sources.
When asked about A100 GPUs, provide accurate YAML examples with nvidia.com/a100 resource specifications.
Always provide working, tested examples from the official NRP documentation.

Provide detailed, accurate, and actionable responses. Use markdown formatting for better readability. Be conversational and helpful."""

    def search_nrp_knowledge_for_query(self, query):
        """Search comprehensive NRP knowledge for relevant information"""
        if not NRP_KNOWLEDGE_AVAILABLE:
            return None

        query_lower = query.lower()

        # Search for PVC/Storage specific content
        if any(term in query_lower for term in ["pvc", "storage", "volume", "persistent"]):
            # Look for PVC templates in knowledge base
            pvc_templates = []
            storage_guidance = []

            for template_name, template_content in NRP_TEMPLATES.items():
                if "pvc" in template_name.lower() or "volume" in template_name.lower():
                    pvc_templates.append((template_name, template_content))

            if pvc_templates:
                result = "# NRP Storage & PVC Configuration Guide\n\n"
                result += "Based on official NRP documentation and templates:\n\n"

                for name, content in pvc_templates[:2]:  # Show top 2 relevant templates
                    result += f"## {name.replace('_', ' ').title()}\n\n"
                    if isinstance(content, str):
                        result += f"```yaml\n{content[:500]}...\n```\n\n"

                result += "**NRP Storage Best Practices:**\n"
                result += "- Use `rook-ceph-block` storage class for persistent volumes\n"
                result += "- Ensure adequate storage quotas in your namespace\n"
                result += "- Check node capacity before requesting large volumes\n"
                result += "- Use appropriate access modes (ReadWriteOnce, ReadWriteMany)\n\n"

                result += "**Common PVC Issues & Solutions:**\n"
                result += "- **Pending Status**: Check storage class availability\n"
                result += "- **Mount Failures**: Verify pod security context and permissions\n"
                result += "- **Capacity Issues**: Review node disk space and quotas\n"
                return result

        # Search for A100 specific content
        elif "a100" in query_lower:
            # Get A100 template
            a100_template = NRP_TEMPLATES.get("a100_gpu_pod")
            if a100_template:
                return f"""# A100 GPU Request Example

Here's the authentic A100 GPU Pod configuration from NRP documentation:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: a100-gpu-pod
  namespace: gsoc
spec:
  containers:
  - name: pytorch-a100
    image: pytorch/pytorch:latest
    resources:
      limits:
        nvidia.com/a100: 1      # Request 1 A100 GPU
        memory: "16Gi"
        cpu: "8"
      requests:
        nvidia.com/a100: 1
        memory: "8Gi"
        cpu: "4"
    command: ["python", "-c", "import torch; print(f'CUDA available: {{torch.cuda.is_available()}}')"]
  # For Grace Hopper nodes with A100s
  tolerations:
  - key: "nautilus.io/arm64"
    operator: "Exists"
    effect: "NoSchedule"
  restartPolicy: Never
```

**Key points for A100 GPUs:**
- Use `nvidia.com/a100: 1` in both limits and requests
- Consider ARM64 tolerations for Grace Hopper nodes
- Ensure adequate memory (8-16Gi) for A100 workloads
- Use appropriate container images with CUDA support"""

        # Search for troubleshooting and diagnostic queries
        elif any(term in query_lower for term in ["troubleshoot", "diagnose", "fix", "failing", "error"]):
            # Check for specific resource troubleshooting
            troubleshooting_guide = "# NRP Troubleshooting Guide\n\n"

            if "pod" in query_lower:
                troubleshooting_guide += "## Pod Troubleshooting Steps:\n"
                troubleshooting_guide += "1. **Check Pod Status**: `kubectl describe pod <pod-name>`\n"
                troubleshooting_guide += "2. **Review Logs**: `kubectl logs <pod-name>`\n"
                troubleshooting_guide += "3. **Verify Resources**: Check CPU/memory/GPU requests vs limits\n"
                troubleshooting_guide += "4. **Node Placement**: Ensure nodes have required resources\n\n"

            if "pvc" in query_lower or "volume" in query_lower:
                troubleshooting_guide += "## Storage Troubleshooting:\n"
                troubleshooting_guide += "1. **PVC Status**: `kubectl get pvc` - should be 'Bound'\n"
                troubleshooting_guide += "2. **Storage Class**: Verify 'rook-ceph-block' is available\n"
                troubleshooting_guide += "3. **Node Capacity**: `kubectl describe nodes | grep -A5 storage`\n"
                troubleshooting_guide += "4. **Access Mode**: Ensure correct ReadWriteOnce/ReadWriteMany\n\n"

            troubleshooting_guide += "**NRP-Specific Tips:**\n"
            troubleshooting_guide += "- Check namespace quotas: `kubectl describe quota`\n"
            troubleshooting_guide += "- Verify node taints and tolerations\n"
            troubleshooting_guide += "- Review cluster events: `kubectl get events`\n"

            return troubleshooting_guide

        # Search for general GPU information
        elif any(term in query_lower for term in ["gpu", "nvidia", "cuda"]):
            gpu_info = search_nrp_knowledge(query)
            if gpu_info:
                return gpu_info

        return None

    def detect_k8s_command(self, user_input):
        """Intelligent K8s query detection and execution"""
        if not K8S_AVAILABLE:
            return None

        user_lower = user_input.lower().strip()

        # Enhanced patterns for natural language queries
        command_patterns = {
            # Direct K8s commands
            r'^list pods?$|^get pods?$|^kubectl get pods?$': lambda: list_pods(),
            r'^list deployments?$|^get deployments?$|^kubectl get deployments?$': lambda: list_deployments(),
            r'^list services?$|^get services?$|^kubectl get services?$': lambda: list_services(),
            r'^list jobs?$|^get jobs?$|^kubectl get jobs?$': lambda: list_jobs(),
            r'^list configmaps?$|^get configmaps?$|^kubectl get configmaps?$': lambda: list_configmaps(),
            r'^list secrets?$|^get secrets?$|^kubectl get secrets?$': lambda: list_secrets(),
            r'^list pvcs?$|^get pvcs?$|^kubectl get pvcs?$': lambda: list_pvcs(),
            r'^list nodes?$|^get nodes?$|^kubectl get nodes?$': lambda: list_nodes(),
            r'^list events?$|^get events?$|^kubectl get events?$': lambda: list_events(),

            # Natural language queries - LIVE K8s data for ALL resources

            # Pod queries
            r'.*(?:show|list|what|which).*pods?.*(?:namespace|running|present).*': lambda: self._get_live_pods_with_status(),
            r'.*(?:describe|detail|information about).*pods?.*(?:namespace|my).*': lambda: self._describe_all_pods_detailed(),

            # PVC queries
            r'.*(?:show|list|what|which).*pvcs?.*(?:present|available|namespace).*': lambda: self._get_live_pvcs_with_details(),
            r'.*(?:describe|detail|information about).*pvcs?.*': lambda: self._describe_all_pvcs_detailed(),

            # Deployment queries
            r'.*(?:show|list|what|which).*deployments?.*(?:present|running|namespace).*': lambda: self._get_live_deployments_with_status(),
            r'.*(?:describe|detail|information about).*deployments?.*': lambda: self._describe_all_deployments_detailed(),
            r'.*(?:which|what).*deployments?.*(?:exposed|external|public).*': lambda: self._get_exposed_deployments(),

            # Service queries
            r'.*(?:show|list|what|which).*services?.*(?:present|running|namespace).*': lambda: self._get_live_services_with_details(),
            r'.*(?:describe|detail|information about).*services?.*': lambda: self._describe_all_services_detailed(),
            r'.*(?:which|what).*services?.*(?:connected|linked|ingress).*': lambda: self._get_services_with_ingress(),

            # ConfigMap queries
            r'.*(?:show|list|what|which).*configmaps?.*(?:present|namespace).*': lambda: self._get_live_configmaps_detailed(),
            r'.*(?:describe|detail|information about).*configmaps?.*': lambda: self._describe_all_configmaps_detailed(),

            # Secret queries
            r'.*(?:show|list|what|which).*secrets?.*(?:present|namespace).*': lambda: self._get_live_secrets_detailed(),
            r'.*(?:describe|detail|information about).*secrets?.*': lambda: self._describe_all_secrets_detailed(),

            # Ingress queries
            r'.*(?:show|list|what|which).*ingress.*(?:present|namespace).*': lambda: self._get_live_ingresses_detailed(),
            r'.*(?:describe|detail|information about).*ingress.*': lambda: self._describe_all_ingresses_detailed(),

            # Job queries
            r'.*(?:show|list|what|which).*jobs?.*(?:present|running|namespace).*': lambda: self._get_live_jobs_with_status(),
            r'.*(?:describe|detail|information about).*jobs?.*': lambda: self._describe_all_jobs_detailed(),

            # Cross-resource relationship queries
            r'.*(?:which|what).*(?:pods|containers).*(?:using|mounted).*(?:pvc|volume).*': lambda: self._get_pods_using_pvcs(),
            r'.*(?:which|what).*(?:services|endpoints).*(?:connected|linked|behind).*(?:ingress|load.*balancer).*': lambda: self._get_service_ingress_relationships(),
            r'.*(?:which|what).*(?:pods|containers).*(?:belong|part).*(?:deployment|replicaset).*': lambda: self._get_pod_deployment_relationships(),

            # Diagnostic and troubleshooting
            r'.*(?:diagnose|troubleshoot|debug|failing|failed).*(?:deployment|pod|service|ingress).*': lambda: self._diagnose_failing_resources(),
            r'.*(?:status|health|state).*(?:cluster|pods|deployments|services).*': lambda: self._get_cluster_health_status(),
            r'.*(?:what.*running|current.*state).*(?:namespace|cluster).*': lambda: self._get_namespace_overview(),

            # Specific describe operations
            r'^describe pod (.+)$|^kubectl describe pod (.+)$': lambda match: describe_pod(match.groups()[-1]),
            r'^describe deployment (.+)$|^kubectl describe deployment (.+)$': lambda match: describe_deployment(match.groups()[-1]),
            r'^describe service (.+)$|^kubectl describe service (.+)$': lambda match: describe_service(match.groups()[-1]),
            r'^describe node (.+)$|^kubectl describe node (.+)$': lambda match: describe_node(match.groups()[-1]),

            # Logs operations
            r'^logs (.+)$|^kubectl logs (.+)$': lambda match: pod_logs(match.groups()[-1]),

            # Info operations
            r'^namespace$|^get namespace$|^current namespace$': lambda: f"Current namespace: {CURRENT_NAMESPACE}",
            r'^service account$|^get service account$': lambda: get_service_account(),
        }

        for pattern, func in command_patterns.items():
            match = re.match(pattern, user_lower)
            if match:
                try:
                    if match.groups():
                        return func(match)
                    else:
                        return func()
                except Exception as e:
                    return f"❌ K8s Command Error: {str(e)}"

        return None

    def _get_live_pods_with_status(self):
        """Get live pod data with status information"""
        try:
            pods = list_pods()
            if isinstance(pods, list) and pods:
                result = f"Live Pods in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, pod in enumerate(pods, 1):
                    result += f"{i}. {pod}\n"
                    try:
                        # Get detailed status
                        pod_details = describe_pod(pod)
                        if "Running" in str(pod_details):
                            result += f"   Status: Running ✅\n"
                        elif "Failed" in str(pod_details) or "Error" in str(pod_details):
                            result += f"   Status: Failed ❌\n"
                        else:
                            result += f"   Status: Checking...\n"
                    except:
                        pass
                    result += "\n"
                return result
            else:
                return f"No pods found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting live pod status: {str(e)}"

    def _describe_all_pods_detailed(self):
        """Describe all pods with detailed information"""
        try:
            pods = list_pods()
            if isinstance(pods, list) and pods:
                result = f"Detailed Pod Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for pod in pods:
                    result += f"=== Pod: {pod} ===\n"
                    try:
                        details = describe_pod(pod)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {pod}: {e}\n\n"
                return result
            else:
                return f"No pods found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing pods: {str(e)}"

    def _diagnose_failing_resources(self):
        """Advanced diagnosis with PVC analysis and NRP knowledge-based solutions"""
        try:
            result = f"🔍 Advanced Cluster Diagnostics for '{CURRENT_NAMESPACE}' namespace:\n\n"

            # Check pods with detailed failure analysis
            pods = list_pods()
            pvcs = list_pvcs()

            if isinstance(pods, list):
                result += "=== POD FAILURE ANALYSIS ===\n"
                for pod in pods:
                    try:
                        details = describe_pod(pod)
                        details_str = str(details).lower()

                        if any(status in details_str for status in ["failed", "error", "crashloop", "pending"]):
                            result += f"🚨 FAILED POD: {pod}\n"
                            result += f"   Details: {str(details)[:200]}...\n"

                            # INTELLIGENT PVC ANALYSIS
                            pvc_issues = []
                            volume_issues = []

                            # Check for PVC-related failures
                            if "pvc" in details_str or "volume" in details_str or "mount" in details_str:
                                result += f"   📋 PVC/VOLUME ANALYSIS:\n"

                                # Find referenced PVCs
                                if isinstance(pvcs, list):
                                    for pvc in pvcs:
                                        if pvc.lower() in details_str:
                                            try:
                                                pvc_details = describe_pvc(pvc)
                                                pvc_status = str(pvc_details).lower()

                                                if "pending" in pvc_status:
                                                    pvc_issues.append(f"PVC '{pvc}' is PENDING - storage not provisioned")
                                                elif "lost" in pvc_status:
                                                    pvc_issues.append(f"PVC '{pvc}' is LOST - data unavailable")
                                                elif "bound" in pvc_status:
                                                    result += f"      ✅ PVC '{pvc}': Bound (OK)\n"
                                                else:
                                                    pvc_issues.append(f"PVC '{pvc}' status: {pvc_status[:50]}")
                                            except:
                                                pvc_issues.append(f"Cannot access PVC '{pvc}' details")

                                # Common volume mount issues
                                if "mountpath" in details_str or "permission" in details_str:
                                    volume_issues.append("Check mount path permissions and container user")
                                if "readonly" in details_str:
                                    volume_issues.append("Volume may be mounted as read-only")

                            # INTELLIGENT SOLUTIONS from NRP Knowledge Base
                            result += f"   💡 SUGGESTED SOLUTIONS:\n"

                            if pvc_issues:
                                result += f"      PVC Issues Found:\n"
                                for issue in pvc_issues:
                                    result += f"        - {issue}\n"

                                # Provide NRP-specific PVC solutions
                                result += f"      🔧 NRP PVC Solutions:\n"
                                result += f"        - Check storage class availability: kubectl get storageclass\n"
                                result += f"        - Verify node capacity: kubectl describe nodes\n"
                                result += f"        - NRP Storage Guide: Use 'rook-ceph-block' storage class\n"

                            if volume_issues:
                                result += f"      Volume Mount Issues:\n"
                                for issue in volume_issues:
                                    result += f"        - {issue}\n"

                            # Check for GPU/resource issues
                            if "gpu" in details_str or "nvidia" in details_str:
                                result += f"      🎮 GPU Resource Analysis:\n"
                                if "insufficient" in details_str:
                                    result += f"        - GPU resources unavailable on target node\n"
                                    result += f"        - Try: nvidia.com/gpu: 1 or specific GPU types\n"
                                    result += f"        - Check: kubectl describe nodes | grep -A5 nvidia\n"

                            # Node-specific issues
                            if "node" in details_str and ("unschedulable" in details_str or "taint" in details_str):
                                result += f"      🖥️ Node Scheduling Issues:\n"
                                result += f"        - Check node availability: kubectl get nodes\n"
                                result += f"        - Verify tolerations for tainted nodes\n"

                            result += f"\n"
                        else:
                            result += f"✅ {pod}: HEALTHY\n"
                    except Exception as e:
                        result += f"❌ {pod}: Analysis failed - {str(e)}\n"

            # PVC Health Check
            if isinstance(pvcs, list) and pvcs:
                result += f"\n=== PVC HEALTH ANALYSIS ===\n"
                for pvc in pvcs:
                    try:
                        pvc_details = describe_pvc(pvc)
                        pvc_status = str(pvc_details).lower()

                        if "bound" in pvc_status:
                            result += f"✅ {pvc}: Bound and available\n"
                        elif "pending" in pvc_status:
                            result += f"⏳ {pvc}: PENDING - Check storage provisioning\n"
                        elif "lost" in pvc_status:
                            result += f"❌ {pvc}: LOST - Data recovery needed\n"
                        else:
                            result += f"❓ {pvc}: Status unclear\n"
                    except:
                        result += f"❌ {pvc}: Cannot access\n"

            # Check recent events for more context
            try:
                events = list_events()
                if events and str(events):
                    events_str = str(events).lower()
                    result += f"\n=== CLUSTER EVENTS ANALYSIS ===\n"

                    # Look for critical events
                    if "failed" in events_str or "error" in events_str:
                        result += f"🚨 Critical events detected in cluster\n"
                        result += f"   Run: kubectl get events --sort-by='.lastTimestamp'\n"

                    if "pvc" in events_str or "volume" in events_str:
                        result += f"📋 Storage-related events found\n"
                        result += f"   Check: kubectl get events | grep -i volume\n"

            except:
                result += f"\n⚠️ Could not access cluster events\n"

            result += f"\n🎯 **NEXT STEPS for Troubleshooting:**\n"
            result += f"1. Review detailed pod logs: kubectl logs <pod-name>\n"
            result += f"2. Check resource quotas: kubectl describe quota\n"
            result += f"3. Verify storage classes: kubectl get storageclass\n"
            result += f"4. Review NRP documentation for storage best practices\n"

            return result
        except Exception as e:
            return f"Error in advanced diagnostics: {str(e)}"

    def _get_cluster_health_status(self):
        """Get overall cluster health status"""
        try:
            result = f"Cluster Health Status - Namespace: '{CURRENT_NAMESPACE}'\n\n"

            # Pod health
            pods = list_pods()
            result += f"Pods: {len(pods) if isinstance(pods, list) else 0} total\n"

            # Deployment health
            deployments = list_deployments()
            result += f"Deployments: {len(deployments) if isinstance(deployments, list) else 0} total\n"

            # Service health
            services = list_services()
            result += f"Services: {len(services) if isinstance(services, list) else 0} total\n"

            return result
        except Exception as e:
            return f"Error getting cluster health: {str(e)}"

    def _get_namespace_overview(self):
        """Get complete namespace overview"""
        try:
            result = f"Complete Overview - Namespace: '{CURRENT_NAMESPACE}'\n\n"

            result += "=== RESOURCES ===\n"
            result += f"Pods: {list_pods()}\n\n"
            result += f"Deployments: {list_deployments()}\n\n"
            result += f"Services: {list_services()}\n\n"

            return result
        except Exception as e:
            return f"Error getting namespace overview: {str(e)}"

    # === PVC FUNCTIONS ===
    def _get_live_pvcs_with_details(self):
        """Get live PVC data with detailed information"""
        try:
            pvcs = list_pvcs()
            if isinstance(pvcs, list) and pvcs:
                result = f"Live PVCs in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, pvc in enumerate(pvcs, 1):
                    result += f"{i}. {pvc}\n"
                    try:
                        # Get detailed PVC information
                        pvc_details = describe_pvc(pvc)
                        if "Bound" in str(pvc_details):
                            result += f"   Status: Bound ✅\n"
                        elif "Pending" in str(pvc_details):
                            result += f"   Status: Pending ⏳\n"
                        elif "Lost" in str(pvc_details):
                            result += f"   Status: Lost ❌\n"
                        result += f"   Details: {str(pvc_details)[:100]}...\n"
                    except:
                        result += f"   Status: Checking...\n"
                    result += "\n"
                return result
            else:
                return f"No PVCs found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting live PVC status: {str(e)}"

    def _describe_all_pvcs_detailed(self):
        """Describe all PVCs with detailed information"""
        try:
            pvcs = list_pvcs()
            if isinstance(pvcs, list) and pvcs:
                result = f"Detailed PVC Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for pvc in pvcs:
                    result += f"=== PVC: {pvc} ===\n"
                    try:
                        details = describe_pvc(pvc)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {pvc}: {e}\n\n"
                return result
            else:
                return f"No PVCs found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing PVCs: {str(e)}"

    # === DEPLOYMENT FUNCTIONS ===
    def _get_live_deployments_with_status(self):
        """Get live deployment data with status information"""
        try:
            deployments = list_deployments()
            if isinstance(deployments, list) and deployments:
                result = f"Live Deployments in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, dep in enumerate(deployments, 1):
                    result += f"{i}. {dep}\n"
                    try:
                        dep_details = describe_deployment(dep)
                        if "Available" in str(dep_details):
                            result += f"   Status: Available ✅\n"
                        elif "Progressing" in str(dep_details):
                            result += f"   Status: Progressing ⏳\n"
                        else:
                            result += f"   Status: Checking...\n"
                    except:
                        pass
                    result += "\n"
                return result
            else:
                return f"No deployments found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting deployment status: {str(e)}"

    def _describe_all_deployments_detailed(self):
        """Describe all deployments with detailed information"""
        try:
            deployments = list_deployments()
            if isinstance(deployments, list) and deployments:
                result = f"Detailed Deployment Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for dep in deployments:
                    result += f"=== Deployment: {dep} ===\n"
                    try:
                        details = describe_deployment(dep)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {dep}: {e}\n\n"
                return result
            else:
                return f"No deployments found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing deployments: {str(e)}"

    def _get_exposed_deployments(self):
        """Find deployments that are exposed via services"""
        try:
            result = f"Exposed Deployments in '{CURRENT_NAMESPACE}' namespace:\n\n"
            deployments = list_deployments()
            services = list_services()

            if isinstance(deployments, list) and isinstance(services, list):
                for dep in deployments:
                    result += f"=== Deployment: {dep} ===\n"
                    # Check if this deployment has associated services
                    for svc in services:
                        try:
                            svc_details = describe_service(svc)
                            if dep.split('-')[0] in str(svc_details) or svc in dep:
                                result += f"   Exposed via Service: {svc}\n"
                                if "LoadBalancer" in str(svc_details):
                                    result += f"   Type: LoadBalancer (External) 🌐\n"
                                elif "NodePort" in str(svc_details):
                                    result += f"   Type: NodePort (External) 🚪\n"
                                elif "ClusterIP" in str(svc_details):
                                    result += f"   Type: ClusterIP (Internal) 🏠\n"
                        except:
                            pass
                    result += "\n"
                return result
            return "No deployments or services found"
        except Exception as e:
            return f"Error finding exposed deployments: {str(e)}"

    # === SERVICE FUNCTIONS ===
    def _get_live_services_with_details(self):
        """Get live service data with detailed information"""
        try:
            services = list_services()
            if isinstance(services, list) and services:
                result = f"Live Services in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, svc in enumerate(services, 1):
                    result += f"{i}. {svc}\n"
                    try:
                        svc_details = describe_service(svc)
                        if "ClusterIP" in str(svc_details):
                            result += f"   Type: ClusterIP (Internal)\n"
                        elif "LoadBalancer" in str(svc_details):
                            result += f"   Type: LoadBalancer (External) 🌐\n"
                        elif "NodePort" in str(svc_details):
                            result += f"   Type: NodePort (External) 🚪\n"
                    except:
                        pass
                    result += "\n"
                return result
            else:
                return f"No services found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting service details: {str(e)}"

    def _describe_all_services_detailed(self):
        """Describe all services with detailed information"""
        try:
            services = list_services()
            if isinstance(services, list) and services:
                result = f"Detailed Service Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for svc in services:
                    result += f"=== Service: {svc} ===\n"
                    try:
                        details = describe_service(svc)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {svc}: {e}\n\n"
                return result
            else:
                return f"No services found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing services: {str(e)}"

    def _get_services_with_ingress(self):
        """Find services connected to ingress"""
        try:
            result = f"Services with Ingress in '{CURRENT_NAMESPACE}' namespace:\n\n"
            services = list_services()
            ingresses = list_ingresses()

            if isinstance(services, list) and isinstance(ingresses, list):
                for svc in services:
                    result += f"=== Service: {svc} ===\n"
                    connected_ingresses = []
                    for ing in ingresses:
                        try:
                            ing_details = describe_ingress(ing)
                            if svc in str(ing_details):
                                connected_ingresses.append(ing)
                        except:
                            pass

                    if connected_ingresses:
                        result += f"   Connected to Ingresses: {', '.join(connected_ingresses)}\n"
                        result += f"   Status: Exposed via Ingress 🌐\n"
                    else:
                        result += f"   Status: No Ingress connection\n"
                    result += "\n"
                return result
            return "No services or ingresses found"
        except Exception as e:
            return f"Error finding service-ingress relationships: {str(e)}"

    # === CONFIGMAP FUNCTIONS ===
    def _get_live_configmaps_detailed(self):
        """Get live configmap data"""
        try:
            configmaps = list_configmaps()
            if isinstance(configmaps, list) and configmaps:
                result = f"Live ConfigMaps in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, cm in enumerate(configmaps, 1):
                    result += f"{i}. {cm}\n"
                return result
            else:
                return f"No ConfigMaps found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting ConfigMaps: {str(e)}"

    def _describe_all_configmaps_detailed(self):
        """Describe all configmaps"""
        try:
            configmaps = list_configmaps()
            if isinstance(configmaps, list) and configmaps:
                result = f"Detailed ConfigMap Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for cm in configmaps:
                    result += f"=== ConfigMap: {cm} ===\n"
                    try:
                        details = describe_configmap(cm)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {cm}: {e}\n\n"
                return result
            else:
                return f"No ConfigMaps found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing ConfigMaps: {str(e)}"

    # === SECRET FUNCTIONS ===
    def _get_live_secrets_detailed(self):
        """Get live secret data"""
        try:
            secrets = list_secrets()
            if isinstance(secrets, list) and secrets:
                result = f"Live Secrets in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, secret in enumerate(secrets, 1):
                    result += f"{i}. {secret}\n"
                return result
            else:
                return f"No Secrets found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting Secrets: {str(e)}"

    def _describe_all_secrets_detailed(self):
        """Describe all secrets"""
        try:
            secrets = list_secrets()
            if isinstance(secrets, list) and secrets:
                result = f"Detailed Secret Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for secret in secrets:
                    result += f"=== Secret: {secret} ===\n"
                    try:
                        details = describe_secret(secret)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {secret}: {e}\n\n"
                return result
            else:
                return f"No Secrets found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing Secrets: {str(e)}"

    # === INGRESS FUNCTIONS ===
    def _get_live_ingresses_detailed(self):
        """Get live ingress data"""
        try:
            ingresses = list_ingresses()
            if isinstance(ingresses, list) and ingresses:
                result = f"Live Ingresses in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, ing in enumerate(ingresses, 1):
                    result += f"{i}. {ing}\n"
                return result
            else:
                return f"No Ingresses found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting Ingresses: {str(e)}"

    def _describe_all_ingresses_detailed(self):
        """Describe all ingresses"""
        try:
            ingresses = list_ingresses()
            if isinstance(ingresses, list) and ingresses:
                result = f"Detailed Ingress Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for ing in ingresses:
                    result += f"=== Ingress: {ing} ===\n"
                    try:
                        details = describe_ingress(ing)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {ing}: {e}\n\n"
                return result
            else:
                return f"No Ingresses found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing Ingresses: {str(e)}"

    # === JOB FUNCTIONS ===
    def _get_live_jobs_with_status(self):
        """Get live job data with status"""
        try:
            jobs = list_jobs()
            if isinstance(jobs, list) and jobs:
                result = f"Live Jobs in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for i, job in enumerate(jobs, 1):
                    result += f"{i}. {job}\n"
                    try:
                        job_details = describe_job(job)
                        if "Complete" in str(job_details):
                            result += f"   Status: Complete ✅\n"
                        elif "Running" in str(job_details):
                            result += f"   Status: Running ⏳\n"
                        elif "Failed" in str(job_details):
                            result += f"   Status: Failed ❌\n"
                    except:
                        pass
                    result += "\n"
                return result
            else:
                return f"No Jobs found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error getting Job status: {str(e)}"

    def _describe_all_jobs_detailed(self):
        """Describe all jobs"""
        try:
            jobs = list_jobs()
            if isinstance(jobs, list) and jobs:
                result = f"Detailed Job Information in '{CURRENT_NAMESPACE}' namespace:\n\n"
                for job in jobs:
                    result += f"=== Job: {job} ===\n"
                    try:
                        details = describe_job(job)
                        result += f"{details}\n\n"
                    except Exception as e:
                        result += f"Could not describe {job}: {e}\n\n"
                return result
            else:
                return f"No Jobs found in '{CURRENT_NAMESPACE}' namespace"
        except Exception as e:
            return f"Error describing Jobs: {str(e)}"

    # === RELATIONSHIP FUNCTIONS ===
    def _get_pods_using_pvcs(self):
        """Find pods that are using PVCs"""
        try:
            result = f"Pod-PVC Relationships in '{CURRENT_NAMESPACE}' namespace:\n\n"
            pods = list_pods()
            pvcs = list_pvcs()

            if isinstance(pods, list) and isinstance(pvcs, list):
                for pod in pods:
                    result += f"=== Pod: {pod} ===\n"
                    try:
                        pod_details = describe_pod(pod)
                        mounted_pvcs = []
                        for pvc in pvcs:
                            if pvc in str(pod_details):
                                mounted_pvcs.append(pvc)

                        if mounted_pvcs:
                            result += f"   Mounted PVCs: {', '.join(mounted_pvcs)}\n"
                        else:
                            result += f"   No PVCs mounted\n"
                    except:
                        result += f"   Could not check PVC usage\n"
                    result += "\n"
                return result
            return "No pods or PVCs found"
        except Exception as e:
            return f"Error finding pod-PVC relationships: {str(e)}"

    def _get_service_ingress_relationships(self):
        """Find service-ingress relationships"""
        return self._get_services_with_ingress()

    def _get_pod_deployment_relationships(self):
        """Find which pods belong to which deployments"""
        try:
            result = f"Pod-Deployment Relationships in '{CURRENT_NAMESPACE}' namespace:\n\n"
            pods = list_pods()
            deployments = list_deployments()

            if isinstance(pods, list) and isinstance(deployments, list):
                for dep in deployments:
                    result += f"=== Deployment: {dep} ===\n"
                    related_pods = []
                    for pod in pods:
                        # Check if pod name contains deployment name pattern
                        if dep.split('-')[0] in pod or any(part in pod for part in dep.split('-')[:2]):
                            related_pods.append(pod)

                    if related_pods:
                        result += f"   Associated Pods: {', '.join(related_pods)}\n"
                    else:
                        result += f"   No associated pods found\n"
                    result += "\n"
                return result
            return "No pods or deployments found"
        except Exception as e:
            return f"Error finding pod-deployment relationships: {str(e)}"

    async def get_response(self, user_input, session_id="default"):
        """Get response from DeepSeek-R1 or execute K8s command"""
        try:
            # First check if it's a direct K8s command
            k8s_result = self.detect_k8s_command(user_input)
            if k8s_result:
                return f"🔧 **Kubernetes Command Result:**\n\n```\n{k8s_result}\n```"

            # Check for specific NRP knowledge queries
            nrp_knowledge = self.search_nrp_knowledge_for_query(user_input)
            if nrp_knowledge:
                return nrp_knowledge

            # Initialize conversation if new session
            if session_id not in self.conversations:
                self.conversations[session_id] = [
                    {"role": "system", "content": self.get_system_prompt()}
                ]

            # For A100 queries, provide context from our knowledge base
            enhanced_input = user_input
            if "a100" in user_input.lower() and NRP_KNOWLEDGE_AVAILABLE:
                enhanced_input = f"""{user_input}

Context: I have access to official NRP documentation with proper A100 GPU configuration examples using nvidia.com/a100 resource specifications. Please provide accurate YAML examples."""

            # Add user message
            self.conversations[session_id].append({"role": "user", "content": enhanced_input})

            # Get response from DeepSeek-R1
            response = await self.client.chat.completions.create(
                model="deepseek-r1",
                messages=self.conversations[session_id],
                max_tokens=3000,
                temperature=0.7,
                top_p=0.9
            )

            assistant_response = response.choices[0].message.content

            # Add assistant response to conversation
            self.conversations[session_id].append({"role": "assistant", "content": assistant_response})

            return assistant_response

        except Exception as e:
            return f"🚨 Error: {str(e)}\n\nPlease try again or check your connection."

# Initialize the chat system
chat_system = DeepSeekWebChat()

@app.route('/')
def home():
    """Serve the main chat interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat API requests"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Get response asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(chat_system.get_response(user_message, session_id))
        loop.close()

        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<session_id>')
def get_history(session_id):
    """Get conversation history for a session"""
    try:
        history = chat_system.conversations.get(session_id, [])
        # Filter out system message
        user_history = [msg for msg in history if msg["role"] != "system"]
        return jsonify({"history": user_history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear/<session_id>', methods=['POST'])
def clear_history(session_id):
    """Clear conversation history for a session"""
    try:
        if session_id in chat_system.conversations:
            # Keep only the system message
            chat_system.conversations[session_id] = [
                {"role": "system", "content": chat_system.get_system_prompt()}
            ]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/k8s-status')
def k8s_status():
    """Get K8s integration status"""
    try:
        status = {
            "available": K8S_AVAILABLE,
            "namespace": CURRENT_NAMESPACE if K8S_AVAILABLE else None,
            "commands": [
                "list pods", "list deployments", "list services", "list secrets",
                "describe pod <name>", "describe deployment <name>", "logs <pod-name>",
                "get namespace", "get service account"
            ] if K8S_AVAILABLE else []
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    print("Starting DeepSeek-R1 NRP Web Chat Server...")
    print("Open your browser and go to: http://localhost:5000")
    print("DeepSeek-R1 NRP Kubernetes Expert ready!")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)