#!/usr/bin/env python3
"""
Working Demo: Enhanced NRP K8s Builder
======================================

This demonstrates the enhanced kube_builder system working end-to-end:
1. Takes user requirements
2. Analyzes with chain of thought (simplified)
3. Generates manifests with NRP compliance
4. Validates against NRP policies
5. Outputs with warnings and documentation

This is a working implementation that demonstrates the concepts from the
original kube_builder.txt design with real NRP integration.
"""

import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def analyze_user_requirements(user_input: str) -> Dict[str, Any]:
    """
    Simplified chain-of-thought analysis of user requirements
    (In full implementation, this would use NRP LLM)
    """
    analysis = {
        "workload_type": "deployment",
        "resource_requirements": {},
        "exposure_requirements": "none",
        "nrp_considerations": [],
        "recommended_resources": [],
        "potential_warnings": [],
        "complexity_score": 3
    }
    
    user_lower = user_input.lower()
    
    # Analyze workload type
    if any(word in user_lower for word in ["job", "batch", "training", "processing"]):
        analysis["workload_type"] = "job"
        analysis["recommended_resources"].append("job")
        analysis["nrp_considerations"].append("Job time limits required")
    
    if any(word in user_lower for word in ["web", "service", "api", "server"]):
        analysis["workload_type"] = "deployment"
        analysis["recommended_resources"].extend(["deployment", "service"])
        analysis["exposure_requirements"] = "clusterip"
    
    # Analyze resource requirements
    if any(word in user_lower for word in ["gpu", "nvidia", "cuda", "pytorch", "tensorflow", "training"]):
        analysis["resource_requirements"]["gpu"] = True
        analysis["nrp_considerations"].append("GPU monitoring policies")
        analysis["potential_warnings"].append("GPU usage is actively monitored")
    
    if any(word in user_lower for word in ["storage", "persistent", "data", "checkpoint", "model"]):
        analysis["resource_requirements"]["storage"] = True
        analysis["nrp_considerations"].append("Storage class selection")
    
    # Analyze exposure needs
    if any(word in user_lower for word in ["expose", "external", "ingress", "public", "web"]):
        analysis["exposure_requirements"] = "ingress"
        analysis["recommended_resources"].append("ingress")
        analysis["nrp_considerations"].append("Ingress class configuration")
    
    # Adjust complexity based on requirements
    if analysis["resource_requirements"].get("gpu"):
        analysis["complexity_score"] += 2
    if analysis["exposure_requirements"] == "ingress":
        analysis["complexity_score"] += 1
    if analysis["workload_type"] == "job":
        analysis["complexity_score"] += 1
    
    return analysis

def get_nrp_warnings_for_requirements(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get relevant NRP warnings based on analysis"""
    try:
        from systems.nautilus_docs_scraper import get_critical_warnings, get_policies_for_topic
        
        all_warnings = get_critical_warnings()
        relevant_warnings = []
        
        # Always include critical warnings
        critical_warnings = [w for w in all_warnings if w.warning_level == "critical"]
        relevant_warnings.extend(critical_warnings)
        
        # Add specific warnings based on requirements
        if analysis["resource_requirements"].get("gpu"):
            gpu_warnings = get_policies_for_topic("gpu")
            relevant_warnings.extend(gpu_warnings)
        
        if analysis["workload_type"] == "job":
            job_warnings = get_policies_for_topic("job")
            relevant_warnings.extend(job_warnings)
        
        return relevant_warnings
        
    except Exception as e:
        print(f"Warning: Could not load NRP warnings: {e}")
        # Return hardcoded critical warnings as fallback
        return [{
            "topic": "sleep commands in batch jobs",
            "policy": "Using sleep commands in batch jobs while holding GPU resources is strictly prohibited",
            "warning_level": "critical",
            "source_url": "https://nrp.ai/documentation/policies/",
            "violations": ["Using sleep commands in Jobs", "Holding GPU resources while idle"],
            "consequences": ["Account suspension", "Permanent banning"]
        }]

def generate_kubernetes_resources(analysis: Dict[str, Any], app_name: str = "demo-app") -> Dict[str, str]:
    """Generate Kubernetes resources based on analysis"""
    
    resources = {}
    
    # 1. Namespace
    namespace_yaml = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": "gsoc",
            "labels": {"name": "gsoc"}
        }
    }
    resources["namespace"] = yaml.dump(namespace_yaml)
    
    # 2. ServiceAccount
    sa_yaml = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": f"{app_name}-sa",
            "namespace": "gsoc",
            "labels": {
                "app.kubernetes.io/name": app_name,
                "app.kubernetes.io/managed-by": "nrp-k8s-builder"
            }
        }
    }
    resources["serviceaccount"] = yaml.dump(sa_yaml)
    
    # 3. Main workload
    if analysis["workload_type"] == "job":
        # Job with NRP compliance
        job_yaml = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"{app_name}-job",
                "namespace": "gsoc",
                "labels": {
                    "app.kubernetes.io/name": app_name,
                    "app.kubernetes.io/component": "batch-job"
                },
                "annotations": {
                    "nrp.ai/job-type": "batch-processing"
                }
            },
            "spec": {
                "activeDeadlineSeconds": 3600,  # NRP requirement
                "template": {
                    "metadata": {
                        "labels": {"app.kubernetes.io/name": app_name}
                    },
                    "spec": {
                        "restartPolicy": "Never",
                        "serviceAccountName": f"{app_name}-sa",
                        "containers": [{
                            "name": "worker",
                            "image": "pytorch/pytorch:latest" if analysis["resource_requirements"].get("gpu") else "python:3.11",
                            "command": ["python", "-c", "print('Job starting...'); import time; time.sleep(10); print('Job completed')"],
                            "resources": _generate_resource_spec(analysis),
                        }]
                    }
                }
            }
        }
        
        # Add GPU node selector if needed
        if analysis["resource_requirements"].get("gpu"):
            job_yaml["spec"]["template"]["spec"]["nodeSelector"] = {"nvidia.com/gpu.present": "true"}
            job_yaml["spec"]["template"]["spec"]["tolerations"] = [{
                "key": "nvidia.com/gpu",
                "operator": "Exists",
                "effect": "NoSchedule"
            }]
        
        resources["job"] = yaml.dump(job_yaml)
        
    else:
        # Deployment
        deployment_yaml = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name,
                "namespace": "gsoc",
                "labels": {
                    "app.kubernetes.io/name": app_name,
                    "app.kubernetes.io/component": "web"
                }
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app.kubernetes.io/name": app_name}},
                "template": {
                    "metadata": {"labels": {"app.kubernetes.io/name": app_name}},
                    "spec": {
                        "serviceAccountName": f"{app_name}-sa",
                        "containers": [{
                            "name": "app",
                            "image": "nginx:latest",
                            "ports": [{"name": "http", "containerPort": 80}],
                            "resources": _generate_resource_spec(analysis),
                            "livenessProbe": {
                                "httpGet": {"path": "/", "port": "http"},
                                "initialDelaySeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/", "port": "http"},
                                "initialDelaySeconds": 5
                            }
                        }]
                    }
                }
            }
        }
        resources["deployment"] = yaml.dump(deployment_yaml)
    
    # 4. Storage if needed
    if analysis["resource_requirements"].get("storage"):
        pvc_yaml = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": f"{app_name}-storage",
                "namespace": "gsoc",
                "labels": {"app.kubernetes.io/name": app_name}
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "storageClassName": "rook-ceph-block",  # NRP default
                "resources": {"requests": {"storage": "50Gi"}}
            }
        }
        resources["pvc"] = yaml.dump(pvc_yaml)
    
    # 5. Service if needed
    if analysis["exposure_requirements"] in ["clusterip", "ingress"]:
        service_yaml = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{app_name}-service",
                "namespace": "gsoc",
                "labels": {"app.kubernetes.io/name": app_name}
            },
            "spec": {
                "type": "ClusterIP",
                "selector": {"app.kubernetes.io/name": app_name},
                "ports": [{"name": "http", "port": 80, "targetPort": 80}]
            }
        }
        resources["service"] = yaml.dump(service_yaml)
    
    # 6. Ingress if needed
    if analysis["exposure_requirements"] == "ingress":
        ingress_yaml = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{app_name}-ingress",
                "namespace": "gsoc",
                "labels": {"app.kubernetes.io/name": app_name}
            },
            "spec": {
                "ingressClassName": "haproxy",  # NRP specific
                "rules": [{
                    "host": f"{app_name}.nrp-nautilus.io",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": f"{app_name}-service",
                                    "port": {"number": 80}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        resources["ingress"] = yaml.dump(ingress_yaml)
    
    return resources

def _generate_resource_spec(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate resource specifications based on analysis"""
    
    if analysis["resource_requirements"].get("gpu"):
        # GPU resources
        return {
            "requests": {
                "nvidia.com/gpu": "1",
                "cpu": "4",
                "memory": "16Gi"
            },
            "limits": {
                "nvidia.com/gpu": "1", 
                "cpu": "4",
                "memory": "16Gi"
            }
        }
    else:
        # Standard CPU resources
        return {
            "requests": {
                "cpu": "100m",
                "memory": "128Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "512Mi"
            }
        }

def validate_nrp_compliance(resources: Dict[str, str]) -> List[str]:
    """Validate generated resources against NRP policies"""
    violations = []
    
    for resource_name, resource_yaml in resources.items():
        try:
            resource_data = yaml.safe_load(resource_yaml)
            
            # Check for sleep commands in Jobs
            if resource_data.get("kind") == "Job":
                containers = resource_data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                for container in containers:
                    command = " ".join(container.get("command", []))
                    if "sleep" in command:
                        violations.append(f"Sleep command detected in {resource_name} - violates NRP policy")
                
                # Check for activeDeadlineSeconds
                if "activeDeadlineSeconds" not in resource_data.get("spec", {}):
                    violations.append(f"Missing activeDeadlineSeconds in {resource_name} - required for NRP compliance")
            
            # Check GPU resource consistency
            containers = []
            if resource_data.get("kind") == "Job":
                containers = resource_data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            elif resource_data.get("kind") == "Deployment":
                containers = resource_data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            
            for container in containers:
                resources_spec = container.get("resources", {})
                limits = resources_spec.get("limits", {})
                requests = resources_spec.get("requests", {})
                
                if "nvidia.com/gpu" in limits and "nvidia.com/gpu" not in requests:
                    violations.append(f"GPU limits without requests in {resource_name} - may cause scheduling issues")
        
        except Exception as e:
            violations.append(f"Failed to validate {resource_name}: {e}")
    
    return violations

def format_output_with_warnings(resources: Dict[str, str], warnings: List[Dict], violations: List[str], analysis: Dict[str, Any]) -> str:
    """Format the final output with warnings and documentation"""
    
    output_lines = []
    
    # Header
    output_lines.extend([
        "# NRP K8s Deployment",
        "# Generated with Enhanced NRP K8s Builder",
        "# Documentation: https://nrp.ai/documentation/",
        "#",
        f"# User Requirements Analysis:",
        f"# - Workload Type: {analysis['workload_type']}",
        f"# - GPU Required: {analysis['resource_requirements'].get('gpu', False)}",
        f"# - Storage Required: {analysis['resource_requirements'].get('storage', False)}",
        f"# - Exposure: {analysis['exposure_requirements']}",
        f"# - Complexity Score: {analysis['complexity_score']}/10",
        "#"
    ])
    
    # Critical warnings
    if warnings:
        critical_warnings = [w for w in warnings if getattr(w, 'warning_level', None) == "critical"]
        if critical_warnings:
            output_lines.append("# CRITICAL NRP WARNINGS - READ BEFORE APPLYING:")
            for warning in critical_warnings[:3]:  # Show top 3
                topic = getattr(warning, 'topic', 'Unknown Warning')
                policy = getattr(warning, 'policy', 'Policy not available')
                source = getattr(warning, 'source_url', 'https://nrp.ai/documentation/')
                consequences = getattr(warning, 'consequences', [])
                
                output_lines.append(f"# ! {topic.upper()}")
                output_lines.append(f"#   {policy}")
                output_lines.append(f"#   Source: {source}")
                if consequences:
                    output_lines.append(f"#   Consequences: {', '.join(consequences[:2])}")
            output_lines.append("#")
    
    # Validation results
    output_lines.append(f"# Generated {len(resources)} resources")
    output_lines.append(f"# {len([w for w in warnings if getattr(w, 'warning_level', None) == 'critical'])} critical warnings")
    if violations:
        output_lines.append(f"# {len(violations)} policy violations detected:")
        for violation in violations:
            output_lines.append(f"#   - {violation}")
    else:
        output_lines.append("# 0 policy violations detected")
    output_lines.append("")
    
    # Resources
    for i, (resource_name, resource_yaml) in enumerate(resources.items()):
        if i > 0:
            output_lines.append("---")
        output_lines.append(f"# Resource: {resource_name}")
        output_lines.append(resource_yaml.rstrip())
        output_lines.append("")
    
    return "\n".join(output_lines)

def build_manifests(user_requirements: str, app_name: str = "demo-app") -> str:
    """
    Main function: Build Kubernetes manifests from user requirements
    
    This is the simplified working implementation of the enhanced kube_builder
    """
    
    print(f"Building manifests for: '{user_requirements}'")
    print("=" * 60)
    
    # Step 1: Analyze requirements
    print("1. Analyzing requirements...")
    analysis = analyze_user_requirements(user_requirements)
    print(f"   Workload: {analysis['workload_type']}")
    print(f"   GPU: {analysis['resource_requirements'].get('gpu', False)}")
    print(f"   Storage: {analysis['resource_requirements'].get('storage', False)}")
    print(f"   Exposure: {analysis['exposure_requirements']}")
    
    # Step 2: Get NRP warnings
    print("2. Loading NRP policies...")
    warnings = get_nrp_warnings_for_requirements(analysis)
    critical_count = len([w for w in warnings if getattr(w, 'warning_level', None) == 'critical'])
    print(f"   Found {len(warnings)} relevant warnings ({critical_count} critical)")
    
    # Step 3: Generate resources
    print("3. Generating Kubernetes resources...")
    resources = generate_kubernetes_resources(analysis, app_name)
    print(f"   Generated {len(resources)} resources: {list(resources.keys())}")
    
    # Step 4: Validate compliance
    print("4. Validating NRP compliance...")
    violations = validate_nrp_compliance(resources)
    if violations:
        print(f"   WARNING: {len(violations)} policy violations found!")
        for violation in violations:
            print(f"     - {violation}")
    else:
        print("   All resources are NRP compliant")
    
    # Step 5: Format output
    print("5. Formatting output...")
    output = format_output_with_warnings(resources, warnings, violations, analysis)
    print(f"   Generated {len(output)} characters of YAML with documentation")
    
    return output

def demo_scenarios():
    """Run several demo scenarios to showcase the system"""
    
    scenarios = [
        ("Web Service", "Create a web service that serves a simple API"),
        ("GPU Training Job", "Create a PyTorch training job that uses 1 GPU and stores model checkpoints"),
        ("Batch Processing", "Create a batch job for data processing"),
        ("Web App with Storage", "Create a web application with persistent storage and external access")
    ]
    
    print("NRP K8s Enhanced Builder - Demo Scenarios")
    print("=" * 60)
    
    for i, (name, requirement) in enumerate(scenarios, 1):
        print(f"\nSCENARIO {i}: {name}")
        print("-" * 40)
        
        try:
            output = build_manifests(requirement, f"demo-app-{i}")
            
            # Save to file
            output_file = Path(f"demo_output_{i}_{name.lower().replace(' ', '_')}.yaml")
            with open(output_file, 'w') as f:
                f.write(output)
            
            print(f"   Saved to: {output_file}")
            print(f"   Preview (first 300 chars):")
            print("   " + "-" * 50)
            preview = output.replace('\n', '\n   ')[:300]
            print("   " + preview + "...")
            
        except Exception as e:
            print(f"   ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single requirement from command line
        requirement = " ".join(sys.argv[1:])
        output = build_manifests(requirement)
        print("\n" + "=" * 60)
        print("GENERATED MANIFEST:")
        print("=" * 60)
        print(output)
    else:
        # Run demo scenarios
        demo_scenarios()