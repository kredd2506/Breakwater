#!/usr/bin/env python3
"""
Ultimate FastMCP NRP.ai Client
=============================
Comprehensive client for the Ultimate FastMCP NRP.ai Server (Port 8020).
Features all FastMCP capabilities + K8s Infogent Architecture integration.

This client demonstrates:
- Advanced prompt usage with structured validation
- Context-aware state management and logging
- Progressive elicitation with multi-turn patterns
- Real-time progress monitoring and reporting
- LLM sampling for intelligent text generation
- K8s operations with natural language queries
- Comprehensive error handling and recovery
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

from fastmcp import Client

class UltimateClient:
    """Ultimate FastMCP client with all capabilities integrated"""

    def __init__(self, server_url: str = "http://localhost:8024/mcp"):
        """Initialize the Ultimate FastMCP client"""
        self.server_url = server_url
        self.client = Client(server_url)
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.operation_count = 0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def log_operation(self, operation_name: str, status: str, metadata: Optional[Dict] = None):
        """Log client operations with structured metadata"""
        self.operation_count += 1
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "operation_id": self.operation_count,
            "operation": operation_name,
            "status": status,
            "metadata": metadata or {}
        }
        print(f"[CLIENT-{status.upper()}] {operation_name}: {json.dumps(log_entry, indent=2)}")

    async def test_server_connection(self) -> bool:
        """Test server connection and availability"""
        try:
            await self.client.ping()
            self.log_operation("server_ping", "success")
            return True
        except Exception as e:
            self.log_operation("server_ping", "error", {"error": str(e)})
            return False

    async def discover_server_capabilities(self) -> Dict[str, Any]:
        """Discover all server capabilities"""
        self.log_operation("capability_discovery", "started")

        try:
            # Get all available operations
            tools = await self.client.list_tools()
            resources = await self.client.list_resources()
            prompts = await self.client.list_prompts()

            capabilities = {
                "tools": [tool.name for tool in tools] if tools else [],
                "resources": [resource.uri for resource in resources] if resources else [],
                "prompts": [prompt.name for prompt in prompts] if prompts else [],
                "discovery_time": datetime.utcnow().isoformat()
            }

            self.log_operation("capability_discovery", "success", {
                "tool_count": len(capabilities["tools"]),
                "resource_count": len(capabilities["resources"]),
                "prompt_count": len(capabilities["prompts"])
            })

            return capabilities

        except Exception as e:
            self.log_operation("capability_discovery", "error", {"error": str(e)})
            raise

    async def test_advanced_prompts(self) -> Dict[str, Any]:
        """Test advanced prompt capabilities"""
        self.log_operation("advanced_prompts_test", "started")

        try:
            results = {}

            # Test 1: Ultimate GPU Deployment Assistant
            print("\n--- Testing Ultimate GPU Deployment Assistant ---")
            gpu_prompt = await self.client.get_prompt("ultimate_gpu_deployment_assistant", {
                "gpu_type": "a100",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "enable_progress_tracking": True
            })
            results["gpu_deployment_prompt"] = len(str(gpu_prompt)) if gpu_prompt else 0

            # Test 2: Ultimate Troubleshooting Expert
            print("\n--- Testing Ultimate Troubleshooting Expert ---")
            troubleshooting_prompt = await self.client.get_prompt("ultimate_troubleshooting_expert", {
                "issue_category": "performance",
                "severity_level": "high",
                "enable_auto_diagnosis": True
            })
            results["troubleshooting_prompt"] = len(str(troubleshooting_prompt)) if troubleshooting_prompt else 0

            self.log_operation("advanced_prompts_test", "success", results)
            return results

        except Exception as e:
            self.log_operation("advanced_prompts_test", "error", {"error": str(e)})
            raise

    async def test_ultimate_gpu_deployment(self) -> Dict[str, Any]:
        """Test ultimate GPU deployment with all FastMCP features"""
        self.log_operation("ultimate_gpu_deployment", "started")

        try:
            print("\n--- Testing Ultimate GPU Deployment ---")

            deployment_params = {
                "gpu_type": "a100",
                "gpu_count": 2,
                "memory_gb": 64,
                "cpu_cores": 16,
                "namespace": f"ultimate-test-{self.session_id}",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "user_id": f"client_user_{self.session_id}"
            }

            result = await self.client.call_tool("ultimate_gpu_deployment_with_progress", deployment_params)

            deployment_result = {
                "deployment_completed": True,
                "result_length": len(result.data) if hasattr(result, 'data') else len(str(result)),
                "deployment_params": deployment_params
            }

            self.log_operation("ultimate_gpu_deployment", "success", deployment_result)
            print(f"Deployment Result:\n{result.data if hasattr(result, 'data') else result}")

            return deployment_result

        except Exception as e:
            self.log_operation("ultimate_gpu_deployment", "error", {"error": str(e)})
            raise

    async def test_progressive_elicitation(self) -> Dict[str, Any]:
        """Test progressive elicitation with multi-turn patterns"""
        self.log_operation("progressive_elicitation", "started")

        try:
            print("\n--- Testing Progressive Elicitation ---")

            elicitation_params = {
                "scenario": "comprehensive_client_test",
                "enable_all_features": True
            }

            result = await self.client.call_tool("ultimate_progressive_elicitation_demo", elicitation_params)

            elicitation_result = {
                "elicitation_completed": True,
                "result_length": len(result.data) if hasattr(result, 'data') else len(str(result)),
                "scenario": elicitation_params["scenario"]
            }

            self.log_operation("progressive_elicitation", "success", elicitation_result)
            print(f"Elicitation Result:\n{result.data if hasattr(result, 'data') else result}")

            return elicitation_result

        except Exception as e:
            self.log_operation("progressive_elicitation", "error", {"error": str(e)})
            raise

    async def test_llm_sampling(self) -> Dict[str, Any]:
        """Test LLM sampling capabilities"""
        self.log_operation("llm_sampling", "started")

        try:
            print("\n--- Testing LLM Sampling ---")

            sampling_params = {
                "sampling_type": "comprehensive_client_test",
                "content": "Ultimate FastMCP NRP.ai Server with K8s Infogent Architecture",
                "temperature": 0.7,
                "max_tokens": 400,
                "enable_structured_output": True
            }

            result = await self.client.call_tool("ultimate_llm_sampling_demo", sampling_params)

            sampling_result = {
                "sampling_completed": True,
                "result_length": len(result.data) if hasattr(result, 'data') else len(str(result)),
                "sampling_params": sampling_params
            }

            self.log_operation("llm_sampling", "success", sampling_result)
            print(f"LLM Sampling Result:\n{result.data if hasattr(result, 'data') else result}")

            return sampling_result

        except Exception as e:
            self.log_operation("llm_sampling", "error", {"error": str(e)})
            raise

    async def test_intelligent_configuration_generation(self) -> Dict[str, Any]:
        """Test intelligent configuration generation using LLM"""
        self.log_operation("intelligent_config_generation", "started")

        try:
            print("\n--- Testing Intelligent Configuration Generation ---")

            config_params = {
                "config_type": "ml_inference",
                "requirements": "High-performance GPU deployment with real-time monitoring and auto-scaling",
                "optimization_level": "high",
                "include_monitoring": True,
                "generate_explanations": True
            }

            result = await self.client.call_tool("intelligent_configuration_generator", config_params)

            config_result = {
                "config_generated": True,
                "result_length": len(result.data) if hasattr(result, 'data') else len(str(result)),
                "config_params": config_params
            }

            self.log_operation("intelligent_config_generation", "success", config_result)
            print(f"Intelligent Config Result:\n{result.data if hasattr(result, 'data') else result}")

            return config_result

        except Exception as e:
            self.log_operation("intelligent_config_generation", "error", {"error": str(e)})
            raise

    async def test_k8s_operations(self) -> Dict[str, Any]:
        """Test Kubernetes operations with infogent architecture"""
        self.log_operation("k8s_operations", "started")

        try:
            print("\n--- Testing K8s Operations ---")
            k8s_results = {}

            # Test 1: Get cluster information
            print("\n1. Cluster Information:")
            cluster_info = await self.client.call_tool("k8s_get_cluster_info", {})
            print(f"Cluster Info: {cluster_info.data if hasattr(cluster_info, 'data') else cluster_info}")
            k8s_results["cluster_info"] = True

            # Test 2: List resources
            print("\n2. Resource Listing:")
            for resource_type in ["pods", "deployments", "services"]:
                try:
                    result = await self.client.call_tool("k8s_list_resources", {"resource_type": resource_type})
                    print(f"{resource_type.title()}: {result.data if hasattr(result, 'data') else result}")
                    k8s_results[f"list_{resource_type}"] = True
                except Exception as e:
                    print(f"Error listing {resource_type}: {e}")
                    k8s_results[f"list_{resource_type}"] = False

            # Test 3: Create a test pod
            print("\n3. Pod Creation:")
            pod_params = {
                "name": f"ultimate-client-test-{self.session_id[:8]}",
                "image": "nginx",
                "memory_limit": "128Mi",
                "cpu_limit": "100m",
                "memory_request": "64Mi",
                "cpu_request": "50m"
            }

            try:
                create_result = await self.client.call_tool("k8s_create_pod", {"params": pod_params})
                print(f"Pod Creation: {create_result.data if hasattr(create_result, 'data') else create_result}")
                k8s_results["pod_creation"] = True

                # Test 4: Describe the created pod
                print("\n4. Pod Description:")
                describe_result = await self.client.call_tool("k8s_describe_resource", {
                    "resource_type": "pod",
                    "resource_name": pod_params["name"]
                })
                print(f"Pod Description: {describe_result.data if hasattr(describe_result, 'data') else describe_result}")
                k8s_results["pod_description"] = True

                # Test 5: Get pod logs
                print("\n5. Pod Logs:")
                logs_result = await self.client.call_tool("k8s_get_logs", {
                    "pod_name": pod_params["name"],
                    "tail_lines": 10
                })
                print(f"Pod Logs: {logs_result.data if hasattr(logs_result, 'data') else logs_result}")
                k8s_results["pod_logs"] = True

                # Test 6: Delete the pod
                print("\n6. Pod Deletion:")
                delete_result = await self.client.call_tool("k8s_delete_resource", {
                    "resource_type": "pod",
                    "resource_name": pod_params["name"]
                })
                print(f"Pod Deletion: {delete_result.data if hasattr(delete_result, 'data') else delete_result}")
                k8s_results["pod_deletion"] = True

            except Exception as e:
                print(f"Error in pod lifecycle test: {e}")
                k8s_results["pod_lifecycle"] = False

            self.log_operation("k8s_operations", "success", k8s_results)
            return k8s_results

        except Exception as e:
            self.log_operation("k8s_operations", "error", {"error": str(e)})
            raise

    async def test_intelligent_k8s_queries(self) -> Dict[str, Any]:
        """Test intelligent natural language K8s queries"""
        self.log_operation("intelligent_k8s_queries", "started")

        try:
            print("\n--- Testing Intelligent K8s Queries ---")
            query_results = {}

            # Test operational queries
            operational_queries = [
                "List all pods in the cluster",
                "Show me current deployments",
                "Get all services running"
            ]

            print("\nOperational Queries:")
            for i, query in enumerate(operational_queries, 1):
                try:
                    result = await self.client.call_tool("intelligent_k8s_query", {
                        "params": {"query": query, "context": f"Client test query {i}"}
                    })
                    print(f"Q{i}: '{query}'")
                    print(f"Response: {result.data if hasattr(result, 'data') else result}")
                    query_results[f"operational_query_{i}"] = True
                except Exception as e:
                    print(f"Error with query {i}: {e}")
                    query_results[f"operational_query_{i}"] = False

            # Test explanation queries
            explanation_queries = [
                "What is a Kubernetes pod and how does it work?",
                "Explain the relationship between deployments and replica sets",
                "How do services provide networking for pods?"
            ]

            print("\nExplanation Queries:")
            for i, query in enumerate(explanation_queries, 1):
                try:
                    result = await self.client.call_tool("intelligent_k8s_query", {
                        "params": {"query": query, "context": "Educational explanation request"}
                    })
                    print(f"E{i}: '{query}'")
                    print(f"Response: {result.data if hasattr(result, 'data') else result}")
                    query_results[f"explanation_query_{i}"] = True
                except Exception as e:
                    print(f"Error with explanation {i}: {e}")
                    query_results[f"explanation_query_{i}"] = False

            # Test complex contextual query
            complex_query = "I'm running a machine learning workload and need to understand how to optimize resource allocation and monitor performance in my K8s cluster"

            print(f"\nComplex Query: '{complex_query}'")
            try:
                result = await self.client.call_tool("intelligent_k8s_query", {
                    "params": {
                        "query": complex_query,
                        "context": "Machine learning deployment optimization"
                    }
                })
                print(f"Complex Response: {result.data if hasattr(result, 'data') else result}")
                query_results["complex_query"] = True
            except Exception as e:
                print(f"Error with complex query: {e}")
                query_results["complex_query"] = False

            self.log_operation("intelligent_k8s_queries", "success", query_results)
            return query_results

        except Exception as e:
            self.log_operation("intelligent_k8s_queries", "error", {"error": str(e)})
            raise

    async def test_server_configuration(self) -> Dict[str, Any]:
        """Test server configuration and flags management"""
        self.log_operation("server_configuration", "started")

        try:
            print("\n--- Testing Server Configuration ---")

            # Test 1: View current configuration
            print("\n1. Current Configuration:")
            config_view = await self.client.call_tool("ultimate_server_configuration", {"action": "view"})
            print(f"Current Config: {config_view.data if hasattr(config_view, 'data') else config_view}")

            # Test 2: Modify a flag
            print("\n2. Modifying Server Flag:")
            flag_modify = await self.client.call_tool("ultimate_server_configuration", {
                "action": "set",
                "flag_name": "verbose_logging",
                "flag_value": True
            })
            print(f"Flag Modification: {flag_modify.data if hasattr(flag_modify, 'data') else flag_modify}")

            # Test 3: View configuration again
            print("\n3. Updated Configuration:")
            config_updated = await self.client.call_tool("ultimate_server_configuration", {"action": "view"})
            print(f"Updated Config: {config_updated.data if hasattr(config_updated, 'data') else config_updated}")

            config_results = {
                "config_view": True,
                "flag_modification": True,
                "config_verification": True
            }

            self.log_operation("server_configuration", "success", config_results)
            return config_results

        except Exception as e:
            self.log_operation("server_configuration", "error", {"error": str(e)})
            raise

    async def test_logging_demonstration(self) -> Dict[str, Any]:
        """Test comprehensive logging capabilities"""
        self.log_operation("logging_demonstration", "started")

        try:
            print("\n--- Testing Logging Demonstration ---")

            logging_params = {
                "demo_type": "comprehensive_client_test",
                "include_errors": True,
                "include_performance": True,
                "include_security": True
            }

            result = await self.client.call_tool("ultimate_logging_demonstration", logging_params)

            logging_result = {
                "logging_demo_completed": True,
                "result_length": len(result.data) if hasattr(result, 'data') else len(str(result)),
                "demo_params": logging_params
            }

            self.log_operation("logging_demonstration", "success", logging_result)
            print(f"Logging Demo Result:\n{result.data if hasattr(result, 'data') else result}")

            return logging_result

        except Exception as e:
            self.log_operation("logging_demonstration", "error", {"error": str(e)})
            raise

    async def comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive test suite for all Ultimate FastMCP capabilities"""
        print("=" * 80)
        print("ULTIMATE FASTMCP NRP.AI CLIENT - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"Server URL: {self.server_url}")
        print(f"Start Time: {datetime.utcnow().isoformat()}")
        print("=" * 80)

        test_results = {
            "session_id": self.session_id,
            "start_time": datetime.utcnow().isoformat(),
            "tests": {}
        }

        # Test 1: Server Connection
        print("\n[TEST 1] Testing Server Connection...")
        test_results["tests"]["server_connection"] = await self.test_server_connection()

        # Test 2: Capability Discovery
        print("\n[TEST 2] Discovering Server Capabilities...")
        test_results["tests"]["capabilities"] = await self.discover_server_capabilities()

        # Test 3: Advanced Prompts
        print("\n[TEST 3] Testing Advanced Prompts...")
        test_results["tests"]["advanced_prompts"] = await self.test_advanced_prompts()

        # Test 4: Ultimate GPU Deployment
        print("\n[TEST 4] Testing Ultimate GPU Deployment...")
        test_results["tests"]["gpu_deployment"] = await self.test_ultimate_gpu_deployment()

        # Test 5: Progressive Elicitation
        print("\n[TEST 5] Testing Progressive Elicitation...")
        test_results["tests"]["progressive_elicitation"] = await self.test_progressive_elicitation()

        # Test 6: LLM Sampling
        print("\n[TEST 6] Testing LLM Sampling...")
        test_results["tests"]["llm_sampling"] = await self.test_llm_sampling()

        # Test 7: Intelligent Configuration Generation
        print("\n[TEST 7] Testing Intelligent Configuration Generation...")
        test_results["tests"]["intelligent_config"] = await self.test_intelligent_configuration_generation()

        # Test 8: K8s Operations
        print("\n[TEST 8] Testing K8s Operations...")
        test_results["tests"]["k8s_operations"] = await self.test_k8s_operations()

        # Test 9: Intelligent K8s Queries
        print("\n[TEST 9] Testing Intelligent K8s Queries...")
        test_results["tests"]["intelligent_k8s_queries"] = await self.test_intelligent_k8s_queries()

        # Test 10: Server Configuration
        print("\n[TEST 10] Testing Server Configuration...")
        test_results["tests"]["server_configuration"] = await self.test_server_configuration()

        # Test 11: Logging Demonstration
        print("\n[TEST 11] Testing Logging Demonstration...")
        test_results["tests"]["logging_demonstration"] = await self.test_logging_demonstration()

        # Final Summary
        test_results["end_time"] = datetime.utcnow().isoformat()
        test_results["total_operations"] = self.operation_count

        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUITE COMPLETED")
        print("=" * 80)
        print(f"Total Operations: {self.operation_count}")
        print(f"Session ID: {self.session_id}")
        print(f"End Time: {test_results['end_time']}")

        # Count successful tests
        successful_tests = sum(1 for test_name, test_result in test_results["tests"].items()
                             if isinstance(test_result, (bool, dict)) and test_result)
        total_tests = len(test_results["tests"])

        print(f"Tests Passed: {successful_tests}/{total_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

        return test_results

async def run_ultimate_client_demo():
    """Run the ultimate client demonstration"""

    # Configuration
    server_url = "http://localhost:8024/mcp"  # Ultimate FastMCP server port

    print("Initializing Ultimate FastMCP NRP.ai Client...")
    print(f"Target Server: {server_url}")

    async with UltimateClient(server_url) as client:
        try:
            # Run comprehensive test suite
            results = await client.comprehensive_test_suite()

            # Save results to file
            results_file = Path(f"ultimate_client_test_results_{client.session_id}.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            print(f"\n[OK] Test results saved to: {results_file}")

            return results

        except Exception as e:
            print(f"\n[ERROR] Ultimate client test failed: {e}")
            client.log_operation("comprehensive_test_suite", "error", {"error": str(e)})
            raise

async def quick_demo():
    """Quick demonstration of key features"""
    print("Starting Quick Ultimate FastMCP Demo...")

    async with UltimateClient() as client:
        # Quick server test
        if await client.test_server_connection():
            print("[OK] Server connection successful")

            # Quick capability check
            capabilities = await client.discover_server_capabilities()
            print(f"[OK] Discovered {len(capabilities['tools'])} tools, {len(capabilities['prompts'])} prompts")

            # Quick K8s test
            k8s_info = await client.client.call_tool("k8s_get_cluster_info", {})
            print(f"[OK] K8s cluster info retrieved")

            # Quick intelligent query
            query_result = await client.client.call_tool("intelligent_k8s_query", {
                "params": {"query": "What is Kubernetes?"}
            })
            print(f"[OK] Intelligent query processed")

        else:
            print("[ERROR] Server connection failed")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ultimate FastMCP NRP.ai Client")
    parser.add_argument("--mode", choices=["full", "quick"], default="full",
                       help="Test mode: 'full' for comprehensive tests, 'quick' for basic demo")
    parser.add_argument("--server", default="http://localhost:8024/mcp",
                       help="FastMCP server URL (default: http://localhost:8024/mcp)")

    args = parser.parse_args()

    if args.mode == "quick":
        asyncio.run(quick_demo())
    else:
        asyncio.run(run_ultimate_client_demo())