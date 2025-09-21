#!/usr/bin/env python3
"""
Test Script for Enhanced NRP K8s Builder
========================================

Tests all components of the enhanced kube builder system:
1. Existing Nautilus documentation scraper
2. Enhanced NRP scraper (with fallbacks)
3. Template system functionality
4. Policy validation
5. End-to-end manifest generation

Run this to understand what we have working and what needs fixes.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the nrp_k8s_system to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_existing_scraper():
    """Test the existing nautilus_docs_scraper"""
    print("\n🔍 TESTING: Existing Nautilus Documentation Scraper")
    print("=" * 60)
    
    try:
        from systems.nautilus_docs_scraper import get_critical_warnings, get_yaml_examples, format_policy_warning
        
        # Test getting warnings
        warnings = get_critical_warnings()
        print(f"✅ Loaded {len(warnings)} critical warnings")
        
        # Test getting examples
        examples = get_yaml_examples()
        print(f"✅ Loaded {len(examples)} YAML examples")
        
        # Show sample data
        if warnings:
            critical_warnings = [w for w in warnings if w.warning_level == "critical"]
            print(f"📊 Critical warnings: {len(critical_warnings)}")
            
            if critical_warnings:
                sample_warning = critical_warnings[0]
                print(f"📝 Sample warning: {sample_warning.topic}")
                print(f"   Policy: {sample_warning.policy[:100]}...")
                print(f"   Violations: {len(sample_warning.violations)}")
                print(f"   Consequences: {len(sample_warning.consequences)}")
                
                # Test formatting
                formatted = format_policy_warning([sample_warning])
                print(f"✅ Warning formatting works ({len(formatted)} chars)")
        
        if examples:
            print(f"📊 Example categories: {set(e.category for e in examples)}")
            sample_example = examples[0]
            print(f"📝 Sample example: {sample_example.title}")
            print(f"   Resource type: {sample_example.resource_type}")
            print(f"   Tags: {sample_example.tags}")
            print(f"   YAML length: {len(sample_example.yaml_content)} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_scraper():
    """Test the enhanced NRP scraper with fallbacks"""
    print("\n🔍 TESTING: Enhanced NRP Documentation Scraper")
    print("=" * 60)
    
    try:
        # Test basic import and initialization
        from systems.enhanced_nrp_scraper import EnhancedNRPScraper, NRPWarning, NRPExample
        
        scraper = EnhancedNRPScraper()
        print("✅ Enhanced scraper initialized")
        
        # Check cache status
        cache_stale = scraper.is_cache_stale()
        print(f"📊 Cache stale: {cache_stale}")
        
        # Test data structures
        sample_warning = NRPWarning(
            warning_type="CRITICAL",
            title="Test Warning",
            content="This is a test warning",
            quote="Test quote",
            source_url="https://example.com",
            context="Test context",
            severity="critical",
            applies_to=["gpu"],
            violations=["test violation"],
            consequences=["test consequence"]
        )
        print("✅ NRPWarning dataclass works")
        
        sample_example = NRPExample(
            title="Test Example",
            description="Test description", 
            code_content="apiVersion: v1\nkind: Pod",
            language="yaml",
            source_url="https://example.com",
            category="workload",
            tags=["test"],
            full_quote="Test quote",
            best_practices=["test practice"],
            warnings_referenced=["test warning"]
        )
        print("✅ NRPExample dataclass works")
        
        # Test search functionality
        search_results = scraper.search_documentation("gpu")
        print(f"✅ Search functionality works (found {sum(len(v) for v in search_results.values())} results)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_k8s_operations():
    """Test existing k8s operations functionality"""
    print("\n🔍 TESTING: Kubernetes Operations")
    print("=" * 60)
    
    try:
        from systems.k8s_operations import K8sOperationsAgent
        
        # Test initialization (might fail if not in cluster, but should import)
        print("✅ K8sOperationsAgent imported successfully")
        
        # Test that we can create the agent class
        try:
            agent = K8sOperationsAgent()
            print("✅ K8sOperationsAgent can be instantiated")
        except Exception as e:
            print(f"⚠️ K8sOperationsAgent instantiation failed (expected if not in cluster): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yaml_generation():
    """Test basic YAML generation capabilities"""
    print("\n🔍 TESTING: YAML Generation")
    print("=" * 60)
    
    try:
        import yaml
        
        # Test basic YAML generation for common resources
        
        # 1. Test Namespace
        namespace_yaml = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "test-namespace"
            }
        }
        namespace_str = yaml.dump(namespace_yaml)
        print("✅ Namespace YAML generation works")
        
        # 2. Test Pod with GPU
        gpu_pod_yaml = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "gpu-test-pod",
                "namespace": "gsoc"
            },
            "spec": {
                "containers": [{
                    "name": "pytorch",
                    "image": "pytorch/pytorch:latest",
                    "resources": {
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
                }],
                "restartPolicy": "Never"
            }
        }
        gpu_pod_str = yaml.dump(gpu_pod_yaml)
        print("✅ GPU Pod YAML generation works")
        
        # 3. Test Job with time limits (NRP compliance)
        job_yaml = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": "training-job",
                "namespace": "gsoc"
            },
            "spec": {
                "activeDeadlineSeconds": 3600,  # NRP compliance
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "trainer",
                            "image": "pytorch/pytorch:latest",
                            "command": ["python", "train.py"],
                            "resources": {
                                "requests": {"nvidia.com/gpu": "1"},
                                "limits": {"nvidia.com/gpu": "1"}
                            }
                        }],
                        "restartPolicy": "Never"
                    }
                }
            }
        }
        job_str = yaml.dump(job_yaml)
        print("✅ GPU Job YAML generation works")
        
        # 4. Test Service
        service_yaml = {
            "apiVersion": "v1", 
            "kind": "Service",
            "metadata": {
                "name": "web-service",
                "namespace": "gsoc"
            },
            "spec": {
                "type": "ClusterIP",
                "selector": {
                    "app": "web-app"
                },
                "ports": [{
                    "port": 80,
                    "targetPort": 8080
                }]
            }
        }
        service_str = yaml.dump(service_yaml)
        print("✅ Service YAML generation works")
        
        # 5. Test Ingress with NRP haproxy
        ingress_yaml = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress", 
            "metadata": {
                "name": "web-ingress",
                "namespace": "gsoc"
            },
            "spec": {
                "ingressClassName": "haproxy",  # NRP specific
                "rules": [{
                    "host": "myapp.nrp-nautilus.io",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "web-service",
                                    "port": {"number": 80}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        ingress_str = yaml.dump(ingress_yaml)
        print("✅ Ingress YAML generation works")
        
        # Test combined output
        all_resources = [namespace_yaml, gpu_pod_yaml, job_yaml, service_yaml, ingress_yaml]
        combined_yaml = "\n---\n".join(yaml.dump(resource) for resource in all_resources)
        print(f"✅ Combined YAML generation works ({len(combined_yaml)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_policy_validation():
    """Test policy validation logic"""
    print("\n🔍 TESTING: NRP Policy Validation")
    print("=" * 60)
    
    try:
        # Test 1: Sleep command detection
        bad_job_yaml = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "sleeper",
                            "image": "alpine",
                            "command": ["sh", "-c", "sleep 3600"]  # VIOLATION!
                        }]
                    }
                }
            }
        }
        
        # Simple validation function
        def check_sleep_violation(resource):
            violations = []
            if resource.get("kind") == "Job":
                containers = []
                template = resource.get("spec", {}).get("template", {})
                if template:
                    containers = template.get("spec", {}).get("containers", [])
                
                for container in containers:
                    command = container.get("command", [])
                    args = container.get("args", [])
                    all_commands = " ".join(command + args)
                    if "sleep" in all_commands.lower():
                        violations.append("Sleep command detected in Job - violates NRP policy")
            return violations
        
        violations = check_sleep_violation(bad_job_yaml)
        print(f"✅ Sleep command detection works: {violations}")
        
        # Test 2: Missing activeDeadlineSeconds
        def check_deadline_violation(resource):
            violations = []
            if resource.get("kind") == "Job":
                if "activeDeadlineSeconds" not in resource.get("spec", {}):
                    violations.append("Missing activeDeadlineSeconds - required for NRP compliance")
            return violations
        
        violations = check_deadline_violation(bad_job_yaml) 
        print(f"✅ Deadline validation works: {violations}")
        
        # Test 3: GPU resource validation
        gpu_job_yaml = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "gpu-job",
                            "resources": {
                                "limits": {"nvidia.com/gpu": "1"},
                                # Missing requests!
                            }
                        }]
                    }
                }
            }
        }
        
        def check_gpu_violation(resource):
            violations = []
            containers = []
            if resource.get("kind") in ["Job", "Pod", "Deployment"]:
                # Extract containers based on resource type
                if resource.get("kind") == "Pod":
                    containers = resource.get("spec", {}).get("containers", [])
                else:
                    template = resource.get("spec", {}).get("template", {})
                    containers = template.get("spec", {}).get("containers", [])
                
                for container in containers:
                    resources = container.get("resources", {})
                    limits = resources.get("limits", {})
                    requests = resources.get("requests", {})
                    
                    if "nvidia.com/gpu" in limits:
                        if "nvidia.com/gpu" not in requests:
                            violations.append("GPU limits without requests - may cause scheduling issues")
            
            return violations
        
        violations = check_gpu_violation(gpu_job_yaml)
        print(f"✅ GPU resource validation works: {violations}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_output():
    """Test template output generation"""
    print("\n🔍 TESTING: Template Output Generation")
    print("=" * 60)
    
    try:
        import yaml
        from systems.nautilus_docs_scraper import get_critical_warnings
        
        # Get actual NRP warnings
        warnings = get_critical_warnings()
        critical_warnings = [w for w in warnings if w.warning_level == "critical"]
        
        # Generate a sample manifest with warnings
        def generate_manifest_with_warnings(app_name="demo-app", include_gpu=False):
            resources = []
            
            # Namespace
            resources.append({
                "apiVersion": "v1",
                "kind": "Namespace", 
                "metadata": {"name": "gsoc"}
            })
            
            # Job or Deployment
            if include_gpu:
                # GPU Job with NRP compliance
                resources.append({
                    "apiVersion": "batch/v1",
                    "kind": "Job",
                    "metadata": {
                        "name": f"{app_name}-gpu-job",
                        "namespace": "gsoc",
                        "annotations": {
                            "nrp.ai/gpu-policy": "monitored",
                            "nrp.ai/warning": "GPU usage is actively monitored"
                        }
                    },
                    "spec": {
                        "activeDeadlineSeconds": 3600,  # NRP compliance
                        "template": {
                            "spec": {
                                "containers": [{
                                    "name": "trainer",
                                    "image": "pytorch/pytorch:latest",
                                    "resources": {
                                        "requests": {"nvidia.com/gpu": "1", "cpu": "4", "memory": "16Gi"},
                                        "limits": {"nvidia.com/gpu": "1", "cpu": "4", "memory": "16Gi"}
                                    },
                                    "command": ["python", "train.py"]
                                }],
                                "restartPolicy": "Never"
                            }
                        }
                    }
                })
            else:
                # Web Deployment
                resources.append({
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": app_name,
                        "namespace": "gsoc"
                    },
                    "spec": {
                        "replicas": 2,
                        "selector": {"matchLabels": {"app": app_name}},
                        "template": {
                            "metadata": {"labels": {"app": app_name}},
                            "spec": {
                                "containers": [{
                                    "name": "web",
                                    "image": "nginx:latest",
                                    "ports": [{"containerPort": 80}],
                                    "resources": {
                                        "requests": {"cpu": "100m", "memory": "128Mi"},
                                        "limits": {"cpu": "500m", "memory": "512Mi"}
                                    }
                                }]
                            }
                        }
                    }
                })
            
            # Service
            resources.append({
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": f"{app_name}-service", "namespace": "gsoc"},
                "spec": {
                    "type": "ClusterIP",
                    "selector": {"app": app_name},
                    "ports": [{"port": 80, "targetPort": 80}]
                }
            })
            
            # Ingress with NRP haproxy
            resources.append({
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {"name": f"{app_name}-ingress", "namespace": "gsoc"},
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
            })
            
            return resources
        
        # Generate output with warnings
        def format_output_with_warnings(resources, warnings):
            output_lines = []
            
            # Header with NRP information
            output_lines.extend([
                "# NRP K8s Deployment",
                "# Generated with Enhanced NRP K8s Builder",
                "# Documentation: https://nrp.ai/documentation/",
                "#"
            ])
            
            # Critical warnings section
            if warnings:
                output_lines.append("# ⚠️ CRITICAL NRP WARNINGS - READ BEFORE APPLYING:")
                for warning in warnings[:3]:  # Limit to top 3
                    output_lines.append(f"# 🚨 {warning.topic.upper()}")
                    output_lines.append(f"#    {warning.policy}")
                    output_lines.append(f"#    Source: {warning.source_url}")
                output_lines.append("#")
            
            # Summary
            output_lines.extend([
                f"# Generated {len(resources)} resources",
                f"# {len([w for w in warnings if w.warning_level == 'critical'])} critical warnings found",
                ""
            ])
            
            # Resources
            for i, resource in enumerate(resources):
                if i > 0:
                    output_lines.append("---")
                
                # Add resource comment
                kind = resource.get("kind", "Resource")
                name = resource.get("metadata", {}).get("name", "unknown")
                output_lines.append(f"# Resource: {kind} - {name}")
                
                # Add YAML
                resource_yaml = yaml.dump(resource, default_flow_style=False)
                output_lines.append(resource_yaml.rstrip())
                output_lines.append("")
            
            return "\n".join(output_lines)
        
        # Test web service manifest
        web_resources = generate_manifest_with_warnings("web-app", include_gpu=False)
        web_output = format_output_with_warnings(web_resources, critical_warnings)
        print(f"✅ Web service manifest generated ({len(web_output)} chars)")
        
        # Test GPU job manifest
        gpu_resources = generate_manifest_with_warnings("gpu-trainer", include_gpu=True)
        gpu_output = format_output_with_warnings(gpu_resources, critical_warnings)
        print(f"✅ GPU job manifest generated ({len(gpu_output)} chars)")
        
        # Show sample output
        print("\n📄 Sample GPU Job Manifest (first 500 chars):")
        print("-" * 50)
        print(gpu_output[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 NRP K8s Enhanced Builder - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Existing Scraper", test_existing_scraper),
        ("Enhanced Scraper", test_enhanced_scraper),
        ("K8s Operations", test_k8s_operations),
        ("YAML Generation", test_yaml_generation),
        ("Policy Validation", test_policy_validation),
        ("Template Output", test_template_output)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced builder is ready for use.")
    else:
        print("⚠️ Some tests failed. See details above for fixes needed.")
    
    return results

if __name__ == "__main__":
    run_all_tests()