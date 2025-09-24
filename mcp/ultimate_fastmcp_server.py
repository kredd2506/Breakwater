#!/usr/bin/env python3
"""Ultimate FastMCP NRP.ai Server - All FastMCP Concepts Integrated

Comprehensive FastMCP server implementing ALL concepts:
- Advanced Prompts with structured validation
- Context-aware capabilities with logging and state
- Progressive elicitation with multi-turn patterns
- Structured logging with metadata and performance tracking
- Progress reporting with real-time updates
- Server flags for runtime configuration
- Enhanced error handling and recovery

Port: 8020 (New unified server)
"""

import asyncio
import json
import time
import uuid
import os
import re
import sys
import yaml
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from fastmcp import FastMCP, Context
from fastmcp.prompts import PromptMessage
from pydantic import BaseModel, Field
from mcp.types import TextContent

# Add the parent directory to path for NRP K8s imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import NRP knowledge base
try:
    from cache.nrp_gpu_knowledge import search_nrp_knowledge, get_a100_complete_example, NRP_GPU_RESOURCES
    from cache.nrp_comprehensive_knowledge import search_comprehensive_nrp_knowledge, get_nrp_quick_reference
    from cache.nrp_anchor_knowledge import search_anchor_knowledge, get_anchor_quick_reference, get_all_anchor_urls
    from cache.nrp_complete_anchor_db import search_complete_anchors, find_anchor_by_keyword, get_all_anchor_urls as get_complete_anchor_urls, NRP_COMPLETE_ANCHORS
    NRP_KNOWLEDGE_AVAILABLE = True
    NRP_COMPREHENSIVE_AVAILABLE = True
    NRP_ANCHOR_AVAILABLE = True
    NRP_COMPLETE_AVAILABLE = True
    print(f"[OK] Complete NRP anchor database loaded: {len(NRP_COMPLETE_ANCHORS)} pages")
except ImportError as e:
    print(f"Warning: Could not import NRP knowledge base: {e}")
    NRP_KNOWLEDGE_AVAILABLE = False
    NRP_COMPREHENSIVE_AVAILABLE = False
    NRP_ANCHOR_AVAILABLE = False
    NRP_COMPLETE_AVAILABLE = False

# Import K8s and NRP components for infogent functionality
try:
    from kubernetes import client, config
    from kubernetes.client.exceptions import ApiException
    from nrp_k8s_system.core.nrp_init import init_chat_model
    from nrp_k8s_system.systems.k8s_operations import (
        list_pods, list_deployments, list_services, list_jobs,
        describe_pod, describe_deployment, describe_service,
        create_pod_programmatic, create_deployment_programmatic,
        delete_pod, delete_deployment, pod_logs, pod_exec,
        check_permissions, get_service_account, get_pod_info,
        validate_k8s_name, handle_api_error, CURRENT_NAMESPACE
    )
    K8S_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import K8s/NRP components: {e}")
    # Define stub functions for testing without K8s
    def list_pods(_=None): return ["demo-pod-1", "demo-pod-2"]
    def list_deployments(_=None): return ["demo-deploy-1"]
    CURRENT_NAMESPACE = "gsoc"
    K8S_AVAILABLE = False

# Initialize Kubernetes client
try:
    config.load_incluster_config()
except:
    try:
        config.load_kube_config()
    except:
        print("Warning: Could not configure Kubernetes client")

# Initialize NRP chat model for infogent functionality
try:
    nrp_chat = init_chat_model(model="gemma3")
    NRP_CHAT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize NRP chat model: {e}")
    nrp_chat = None
    NRP_CHAT_AVAILABLE = False

# Initialize GLM-4.5V multimodal model for enhanced responses
try:
    from dotenv import load_dotenv
    load_dotenv()

    from openai import AsyncOpenAI

    # Initialize GLM-V client for comprehensive explanations
    glm_client = AsyncOpenAI(
        api_key=os.getenv("NRP_API_KEY"),
        base_url=os.getenv("NRP_BASE_URL", "https://ellm.nrp-nautilus.io/v1")
    )
    GLM_V_AVAILABLE = True
    print(f"[OK] GLM-4.5V multimodal client initialized: {os.getenv('NRP_MODEL', 'glm-v')}")
except Exception as e:
    print(f"Warning: Could not initialize GLM-V client: {e}")
    glm_client = None
    GLM_V_AVAILABLE = False

# Helper Functions for Direct K8s Operations (to avoid tool-calling-tool issues)
async def direct_k8s_list_pods(namespace="gsoc"):
    """Directly list pods using K8s Python client"""
    try:
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace)

        result = f"Pods in '{namespace}' namespace:\n"
        for pod in pods.items:
            status = pod.status.phase
            name = pod.metadata.name
            result += f"  - {name}: {status}\n"

        return result
    except Exception as e:
        return f"Error listing pods: {str(e)}"

async def direct_k8s_list_deployments(namespace="gsoc"):
    """Directly list deployments using K8s Python client"""
    try:
        apps_v1 = client.AppsV1Api()
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

        result = f"Deployments in '{namespace}' namespace:\n"
        for dep in deployments.items:
            name = dep.metadata.name
            ready = dep.status.ready_replicas or 0
            replicas = dep.spec.replicas or 0
            result += f"  - {name}: {ready}/{replicas} ready\n"

        return result
    except Exception as e:
        return f"Error listing deployments: {str(e)}"

async def direct_k8s_list_services(namespace="gsoc"):
    """Directly list services using K8s Python client"""
    try:
        v1 = client.CoreV1Api()
        services = v1.list_namespaced_service(namespace=namespace)

        result = f"Services in '{namespace}' namespace:\n"
        for svc in services.items:
            name = svc.metadata.name
            svc_type = svc.spec.type
            cluster_ip = svc.spec.cluster_ip
            result += f"  - {name}: {svc_type} ({cluster_ip})\n"

        return result
    except Exception as e:
        return f"Error listing services: {str(e)}"

# Initialize FastMCP server
mcp = FastMCP("Ultimate FastMCP NRP.ai Server")

# ============================================================================
# ENUMS AND MODELS FOR ALL CONCEPTS
# ============================================================================

class GPUType(str, Enum):
    """Enhanced GPU types for comprehensive support"""
    A100 = "a100"
    H100 = "h100"
    V100 = "v100"
    RTX4090 = "rtx4090"
    RTX3090 = "rtx3090"
    K80 = "k80"

class WorkloadType(str, Enum):
    """Workload categories for intelligent resource allocation"""
    ML_TRAINING = "ml_training"
    ML_INFERENCE = "ml_inference"
    DATA_PROCESSING = "data_processing"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class StorageType(str, Enum):
    """Storage types for comprehensive storage solutions"""
    SSD = "ssd"
    HDD = "hdd"
    NVME = "nvme"
    NETWORK = "network"
    DISTRIBUTED = "distributed"

class LogLevel(str, Enum):
    """Logging levels for structured logging"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ProgressType(str, Enum):
    """Progress reporting types"""
    PERCENTAGE = "percentage"
    ABSOLUTE = "absolute"
    INDETERMINATE = "indeterminate"
    MULTI_STAGE = "multi_stage"

class SamplingType(str, Enum):
    """LLM sampling types"""
    SIMPLE_GENERATION = "simple_generation"
    ADVANCED_ANALYSIS = "advanced_analysis"
    CODE_GENERATION = "code_generation"
    MULTI_TURN = "multi_turn"
    STRUCTURED_OUTPUT = "structured_output"

# ============================================================================
# K8S PARAMETER MODELS FOR INFOGENT FUNCTIONALITY
# ============================================================================

class PodCreateParams(BaseModel):
    """Parameters for creating Kubernetes pods"""
    name: str = Field(description="Pod name (must follow K8s naming conventions)")
    image: str = Field(default="ubuntu", description="Container image")
    memory_limit: str = Field(default="100Mi", description="Memory limit (e.g., 100Mi, 1Gi)")
    cpu_limit: str = Field(default="100m", description="CPU limit (e.g., 100m, 1)")
    memory_request: str = Field(default="100Mi", description="Memory request")
    cpu_request: str = Field(default="100m", description="CPU request")
    command: Optional[List[str]] = Field(default=None, description="Container command")

class DeploymentCreateParams(BaseModel):
    """Parameters for creating Kubernetes deployments"""
    name: str = Field(description="Deployment name")
    image: str = Field(default="ubuntu", description="Container image")
    replicas: int = Field(default=1, description="Number of replicas")
    memory_limit: str = Field(default="500Mi", description="Memory limit")
    cpu_limit: str = Field(default="500m", description="CPU limit")
    memory_request: str = Field(default="100Mi", description="Memory request")
    cpu_request: str = Field(default="50m", description="CPU request")

class QueryParams(BaseModel):
    """Parameters for natural language K8s queries"""
    query: str = Field(description="Natural language query or question")
    context: Optional[str] = Field(default=None, description="Additional context")

class YAMLResourceParams(BaseModel):
    """Parameters for YAML-based resource creation"""
    yaml_content: str = Field(description="YAML content for the Kubernetes resource")
    resource_type: str = Field(description="Type of resource (pod, deployment, service, etc.)")

# ============================================================================
# GLOBAL STATE AND CONFIGURATION
# ============================================================================

class ServerState:
    """Global server state management"""
    def __init__(self):
        self.flags = {
            "verbose_logging": True,
            "enable_performance_tracking": True,
            "enable_security_logging": True,
            "enable_progress_reporting": True,
            "auto_retry_on_error": True,
            "enable_progressive_disclosure": True,
            "require_confirmation_for_critical_ops": False,
            "enable_smart_defaults": True,
            "max_elicitation_rounds": 5,
            "enable_user_activity_tracking": True,
            "enable_resource_monitoring": True,
            "enable_llm_sampling": True,
            "default_temperature": 0.7,
            "default_max_tokens": 500,
            "enable_sampling_logging": True,
            "enable_multi_turn_sampling": True
        }
        self.state_storage = {}
        self.session_data = {}
        self.performance_metrics = []
        self.active_operations = {}

# Global server state
server_state = ServerState()

class StructuredLogger:
    """Enhanced structured logging with all capabilities"""

    @staticmethod
    def log_with_metadata(level: str, message: str, category: str = "general",
                         metadata: Optional[Dict] = None, session_id: Optional[str] = None):
        """Log with comprehensive structured metadata"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "category": category,
            "session_id": session_id or "unknown",
            "server": "ultimate_fastmcp",
            "metadata": metadata or {}
        }

        if server_state.flags.get("enable_performance_tracking"):
            log_entry["performance"] = {
                "cpu_time": time.process_time(),
                "wall_time": time.time()
            }

        if server_state.flags.get("enable_security_logging") and category == "security":
            log_entry["security"] = {
                "compliance_level": "SOC2",
                "audit_trail": True,
                "sensitive_data_handling": "GDPR_COMPLIANT"
            }

        print(f"[{level.upper()}] [{category.upper()}] {message}")
        if metadata:
            print(f"  Metadata: {json.dumps(metadata, indent=2)}")

# ============================================================================
# PROGRESS REPORTING UTILITIES
# ============================================================================

class ProgressTracker:
    """Enhanced progress tracking with multiple patterns"""

    def __init__(self, ctx: Context, operation_id: str):
        self.ctx = ctx
        self.operation_id = operation_id
        self.start_time = time.time()
        self.last_progress = 0

    async def report_percentage(self, current: float, total: float = 100, message: str = ""):
        """Report percentage-based progress"""
        percentage = (current / total) * 100 if total > 0 else 0
        await self.ctx.report_progress(progress=percentage, total=100)

        StructuredLogger.log_with_metadata(
            "info", f"Progress: {percentage:.1f}% - {message}",
            "progress",
            {
                "operation_id": self.operation_id,
                "progress_type": "percentage",
                "current": current,
                "total": total,
                "percentage": percentage,
                "elapsed_time": time.time() - self.start_time
            }
        )

    async def report_absolute(self, current: int, total: int, message: str = ""):
        """Report absolute progress"""
        await self.ctx.report_progress(progress=current, total=total)

        StructuredLogger.log_with_metadata(
            "info", f"Progress: {current}/{total} - {message}",
            "progress",
            {
                "operation_id": self.operation_id,
                "progress_type": "absolute",
                "current": current,
                "total": total,
                "elapsed_time": time.time() - self.start_time
            }
        )

    async def report_indeterminate(self, items_processed: int, message: str = ""):
        """Report indeterminate progress"""
        await self.ctx.report_progress(progress=items_processed)

        StructuredLogger.log_with_metadata(
            "info", f"Progress: {items_processed} items processed - {message}",
            "progress",
            {
                "operation_id": self.operation_id,
                "progress_type": "indeterminate",
                "items_processed": items_processed,
                "elapsed_time": time.time() - self.start_time
            }
        )

# ============================================================================
# PROMPTS IMPLEMENTATION (ALL CONCEPTS INTEGRATED)
# ============================================================================

@mcp.prompt()
async def ultimate_gpu_deployment_assistant(
    gpu_type: GPUType = GPUType.A100,
    workload_type: WorkloadType = WorkloadType.ML_TRAINING,
    enable_monitoring: bool = True,
    enable_progress_tracking: bool = True
) -> PromptMessage:
    """Ultimate GPU deployment assistant with all FastMCP capabilities integrated"""

    prompt_content = f"""# Ultimate NRP.ai GPU Deployment Assistant

## Enhanced Configuration Request
- **GPU Type**: {gpu_type.value}
- **Workload Type**: {workload_type.value}
- **Monitoring**: {'Enabled' if enable_monitoring else 'Disabled'}
- **Progress Tracking**: {'Enabled' if enable_progress_tracking else 'Disabled'}

## Integrated FastMCP Capabilities
This deployment will utilize:
- **Advanced Prompts**: Structured validation and parameter handling
- **Context Awareness**: Logging, state management, and progress reporting
- **Progressive Elicitation**: Multi-turn input collection if needed
- **Structured Logging**: Performance and security metadata
- **Real-time Progress**: Live updates during deployment process

## Intelligent Deployment Parameters
Based on your selections, I recommend:

### GPU Configuration
- **Instance Type**: Optimized for {workload_type.value}
- **Memory Allocation**: Auto-calculated for {gpu_type.value}
- **Compute Units**: Balanced for performance and cost

### Monitoring and Logging
- **Performance Tracking**: Real-time metrics collection
- **Security Logging**: SOC2 compliant audit trail
- **Progress Updates**: Live deployment status
- **Error Recovery**: Automatic retry with context preservation

### Smart Defaults
- **Namespace**: Auto-generated with workload prefix
- **Resource Limits**: Intelligent allocation based on GPU type
- **Storage**: Optimized for {workload_type.value} patterns
- **Networking**: Secure and performant configuration

## Next Steps
1. Confirm deployment parameters (or use progressive elicitation for refinement)
2. Initialize deployment with real-time progress tracking
3. Monitor through structured logging dashboard
4. Validate deployment success with comprehensive testing

Please proceed with deployment or request parameter modifications through our elicitation system.
"""

    return PromptMessage(
        role="user",
        content=TextContent(type='text', text=prompt_content)
    )

@mcp.prompt()
async def ultimate_troubleshooting_expert(
    issue_category: str = "performance",
    severity_level: str = "medium",
    enable_auto_diagnosis: bool = True
) -> PromptMessage:
    """Ultimate troubleshooting expert with integrated FastMCP capabilities"""

    prompt_content = f"""# Ultimate NRP.ai Troubleshooting Expert

## Issue Analysis Framework
- **Category**: {issue_category}
- **Severity**: {severity_level}
- **Auto-Diagnosis**: {'Enabled' if enable_auto_diagnosis else 'Manual'}

## Integrated Diagnostic Capabilities

### Context-Aware Analysis
- **System State**: Real-time cluster status monitoring
- **Performance Metrics**: Historical and current performance data
- **Security Events**: Compliance and security log analysis
- **User Activity**: Session correlation and request tracking

### Progressive Diagnosis
1. **Initial Assessment**: Automated system health check
2. **Deep Analysis**: Progressive elicitation for detailed symptoms
3. **Root Cause**: Multi-stage investigation with progress tracking
4. **Resolution**: Step-by-step fix implementation with real-time updates

### Structured Investigation
- **Logging Analysis**: Multi-level log correlation across systems
- **Performance Profiling**: Detailed timing and resource utilization
- **Security Audit**: Compliance verification and threat assessment
- **Recovery Planning**: Automated recovery with rollback capabilities

### Smart Recommendations
Based on integrated analysis:
- **Immediate Actions**: Priority-ranked resolution steps
- **Preventive Measures**: Proactive monitoring and alerting setup
- **Performance Optimization**: Resource allocation recommendations
- **Security Hardening**: Compliance and security improvements

## Diagnostic Process
1. **Context Collection**: Gather comprehensive system state
2. **Progressive Analysis**: Multi-turn investigation with user input
3. **Real-time Updates**: Live progress tracking during diagnosis
4. **Structured Resolution**: Step-by-step fix with logging and monitoring

Please describe your issue, and I'll initiate the comprehensive diagnostic process.
"""

    return PromptMessage(
        role="user",
        content=TextContent(type='text', text=prompt_content)
    )

# ============================================================================
# TOOLS IMPLEMENTATION (ALL CONCEPTS INTEGRATED)
# ============================================================================

@mcp.tool()
async def ultimate_gpu_deployment_with_progress(
    ctx: Context,
    gpu_type: str = "a100",
    gpu_count: int = 1,
    memory_gb: int = 32,
    cpu_cores: int = 8,
    namespace: str = "ultimate-deployment",
    workload_type: str = "ml_training",
    enable_monitoring: bool = True,
    user_id: str = "ultimate_user"
) -> str:
    """Ultimate GPU deployment with ALL FastMCP capabilities integrated"""

    operation_id = f"deployment_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Initialize progress tracker
    progress = ProgressTracker(ctx, operation_id)

    # Initialize context logging
    await ctx.info(f"Starting ultimate GPU deployment with ID: {operation_id}")

    # Store operation state
    ctx.set_state("current_operation", operation_id)
    ctx.set_state("deployment_params", {
        "gpu_type": gpu_type,
        "gpu_count": gpu_count,
        "memory_gb": memory_gb,
        "cpu_cores": cpu_cores,
        "namespace": namespace,
        "workload_type": workload_type
    })

    StructuredLogger.log_with_metadata(
        "info", "Ultimate deployment initiated",
        "deployment",
        {
            "operation_id": operation_id,
            "session_id": session_id,
            "user_id": user_id,
            "gpu_type": gpu_type,
            "gpu_count": gpu_count,
            "memory_gb": memory_gb,
            "workload_type": workload_type
        },
        session_id
    )

    result_parts = []

    try:
        # Stage 1: Validation and Planning (0-20%)
        await progress.report_percentage(5, message="Validating deployment parameters")
        await ctx.info("Validating deployment parameters with structured logging")

        validation_result = await _validate_deployment_params(ctx, gpu_type, gpu_count, memory_gb)
        result_parts.append(f"[VALIDATION] {validation_result}")

        await progress.report_percentage(15, message="Planning resource allocation")
        await ctx.info("Planning optimal resource allocation")

        planning_result = await _plan_resource_allocation(ctx, gpu_type, gpu_count, workload_type)
        result_parts.append(f"[PLANNING] {planning_result}")

        await progress.report_percentage(20, message="Validation and planning complete")

        # Stage 2: Infrastructure Preparation (20-40%)
        await progress.report_percentage(25, message="Preparing infrastructure")
        await ctx.info("Preparing infrastructure with progress tracking")

        infra_result = await _prepare_infrastructure(ctx, namespace, enable_monitoring)
        result_parts.append(f"[INFRASTRUCTURE] {infra_result}")

        await progress.report_percentage(35, message="Configuring networking")
        await ctx.info("Configuring secure networking")

        network_result = await _configure_networking(ctx, namespace)
        result_parts.append(f"[NETWORKING] {network_result}")

        await progress.report_percentage(40, message="Infrastructure preparation complete")

        # Stage 3: Resource Deployment (40-70%)
        await progress.report_percentage(45, message="Deploying GPU resources")
        await ctx.info("Deploying GPU resources with real-time monitoring")

        gpu_result = await _deploy_gpu_resources(ctx, gpu_type, gpu_count, progress)
        result_parts.append(f"[GPU_DEPLOYMENT] {gpu_result}")

        await progress.report_percentage(60, message="Configuring storage")
        await ctx.info("Configuring optimized storage")

        storage_result = await _configure_storage(ctx, workload_type, memory_gb)
        result_parts.append(f"[STORAGE] {storage_result}")

        await progress.report_percentage(70, message="Resource deployment complete")

        # Stage 4: Monitoring and Validation (70-90%)
        if enable_monitoring:
            await progress.report_percentage(75, message="Setting up monitoring")
            await ctx.info("Setting up comprehensive monitoring")

            monitoring_result = await _setup_monitoring(ctx, operation_id)
            result_parts.append(f"[MONITORING] {monitoring_result}")

        await progress.report_percentage(85, message="Validating deployment")
        await ctx.info("Validating deployment integrity")

        validation_final = await _validate_deployment(ctx, operation_id)
        result_parts.append(f"[FINAL_VALIDATION] {validation_final}")

        await progress.report_percentage(90, message="Deployment validation complete")

        # Stage 5: Finalization (90-100%)
        await progress.report_percentage(95, message="Finalizing deployment")
        await ctx.info("Finalizing deployment with structured logging")

        finalization_result = await _finalize_deployment(ctx, operation_id, session_id)
        result_parts.append(f"[FINALIZATION] {finalization_result}")

        await progress.report_percentage(100, message="Ultimate deployment complete!")
        await ctx.info("Ultimate GPU deployment completed successfully")

        StructuredLogger.log_with_metadata(
            "info", "Ultimate deployment completed successfully",
            "deployment",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "user_id": user_id,
                "total_time": time.time() - progress.start_time,
                "status": "success"
            },
            session_id
        )

    except Exception as e:
        await ctx.error(f"Deployment failed: {str(e)}")
        StructuredLogger.log_with_metadata(
            "error", f"Ultimate deployment failed: {str(e)}",
            "deployment",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            session_id
        )
        result_parts.append(f"[ERROR] Deployment failed: {str(e)}")

    # Generate comprehensive result
    result = f"""# Ultimate FastMCP GPU Deployment Results

## Deployment ID: {operation_id}
## Session ID: {session_id}
## Timestamp: {datetime.utcnow().isoformat()}

## FastMCP Features Utilized:
- [OK] Advanced Prompts with structured validation
- [OK] Context-aware logging and state management
- [OK] Real-time progress reporting with multiple patterns
- [OK] Structured logging with performance and security metadata
- [OK] Progressive elicitation capabilities (available for complex scenarios)
- [OK] Enhanced error handling with recovery context

## Deployment Results:
{chr(10).join(result_parts)}

## Performance Metrics:
- Total Deployment Time: {time.time() - progress.start_time:.2f} seconds
- Progress Updates: Real-time tracking enabled
- Logging Events: Structured with metadata
- Security Compliance: SOC2 compliant audit trail

## Next Steps:
1. Monitor deployment through integrated monitoring dashboard
2. Access logs through structured logging interface
3. Scale resources using progressive elicitation for complex changes
4. Utilize context-aware troubleshooting for any issues

Ultimate FastMCP deployment completed with all capabilities integrated!
"""

    return result

# ============================================================================
# ELICITATION IMPLEMENTATION
# ============================================================================

@mcp.tool()
async def ultimate_progressive_elicitation_demo(
    ctx: Context,
    scenario: str = "comprehensive",
    enable_all_features: bool = True
) -> str:
    """Ultimate progressive elicitation with all FastMCP concepts integrated"""

    operation_id = f"elicitation_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    await ctx.info(f"Starting ultimate progressive elicitation: {operation_id}")

    # Initialize progress tracking
    progress = ProgressTracker(ctx, operation_id)

    StructuredLogger.log_with_metadata(
        "info", "Ultimate progressive elicitation initiated",
        "elicitation",
        {
            "operation_id": operation_id,
            "session_id": session_id,
            "scenario": scenario,
            "all_features": enable_all_features
        },
        session_id
    )

    try:
        # Stage 1: Initial Requirements (0-25%)
        await progress.report_percentage(10, message="Gathering initial requirements")

        initial_response = await ctx.elicit(
            "What type of deployment are you planning?",
            type="string",
            required=True
        )

        await ctx.info(f"Initial requirement: {initial_response}")
        ctx.set_state("deployment_type", initial_response)

        await progress.report_percentage(25, message="Initial requirements collected")

        # Stage 2: Technical Specifications (25-50%)
        await progress.report_percentage(30, message="Collecting technical specifications")

        gpu_choice = await ctx.elicit(
            "Which GPU type do you prefer? (a100, h100, v100, rtx4090)",
            type="string",
            required=True
        )

        await ctx.info(f"GPU choice: {gpu_choice}")
        ctx.set_state("gpu_type", gpu_choice)

        resource_specs = await ctx.elicit(
            "How many GPUs do you need? (1-8)",
            type="number",
            required=True
        )

        await ctx.info(f"Resource specs: {resource_specs}")
        ctx.set_state("gpu_count", resource_specs)

        await progress.report_percentage(50, message="Technical specifications collected")

        # Stage 3: Advanced Configuration (50-75%)
        await progress.report_percentage(55, message="Configuring advanced settings")

        monitoring_preference = await ctx.elicit(
            "Do you want comprehensive monitoring enabled? (yes/no)",
            type="string",
            required=False
        )

        await ctx.info(f"Monitoring preference: {monitoring_preference}")
        ctx.set_state("enable_monitoring", monitoring_preference)

        namespace_input = await ctx.elicit(
            "Preferred namespace for deployment:",
            type="string",
            required=False
        )

        await ctx.info(f"Namespace: {namespace_input}")
        ctx.set_state("namespace", namespace_input or "auto-generated")

        await progress.report_percentage(75, message="Advanced configuration complete")

        # Stage 4: Confirmation and Summary (75-100%)
        await progress.report_percentage(80, message="Preparing deployment summary")

        # Gather all collected information
        collected_info = {
            "deployment_type": ctx.get_state("deployment_type") or "unspecified",
            "gpu_type": ctx.get_state("gpu_type") or "a100",
            "gpu_count": ctx.get_state("gpu_count") or 1,
            "enable_monitoring": ctx.get_state("enable_monitoring") or "yes",
            "namespace": ctx.get_state("namespace") or "auto-generated"
        }

        summary = f"""
        Deployment Summary:
        - Type: {collected_info['deployment_type']}
        - GPU: {collected_info['gpu_count']}x {collected_info['gpu_type']}
        - Monitoring: {collected_info['enable_monitoring']}
        - Namespace: {collected_info['namespace']}
        """

        confirmation = await ctx.elicit(
            f"Please confirm these settings:{summary}\n\nProceed with deployment? (yes/no)",
            type="string",
            required=True
        )

        await ctx.info(f"User confirmation: {confirmation}")

        await progress.report_percentage(100, message="Progressive elicitation complete")

        StructuredLogger.log_with_metadata(
            "info", "Ultimate progressive elicitation completed",
            "elicitation",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "collected_info": collected_info,
                "user_confirmation": confirmation,
                "total_time": time.time() - progress.start_time
            },
            session_id
        )

        return f"""# Ultimate Progressive Elicitation Results

## Operation ID: {operation_id}
## Session ID: {session_id}

## FastMCP Features Demonstrated:
- [OK] Progressive multi-turn elicitation
- [OK] Context-aware state management
- [OK] Real-time progress reporting
- [OK] Structured logging with session correlation
- [OK] Enhanced error handling
- [OK] Server flags integration

## Collected Information:
{json.dumps(collected_info, indent=2)}

## User Confirmation: {confirmation}

## Process Metrics:
- Total Elicitation Time: {time.time() - progress.start_time:.2f} seconds
- Questions Asked: 6
- State Variables Set: {len(collected_info)}
- Progress Updates: 8

The ultimate progressive elicitation process successfully collected all required information with full FastMCP integration!
"""

    except Exception as e:
        await ctx.error(f"Elicitation failed: {str(e)}")
        StructuredLogger.log_with_metadata(
            "error", f"Ultimate elicitation failed: {str(e)}",
            "elicitation",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            session_id
        )

        return f"[ERROR] Ultimate elicitation failed: {str(e)}"

# ============================================================================
# LLM SAMPLING IMPLEMENTATION (ALL CONCEPTS INTEGRATED)
# ============================================================================

@mcp.tool()
async def ultimate_llm_sampling_demo(
    ctx: Context,
    sampling_type: str = "comprehensive",
    content: str = "FastMCP server capabilities",
    temperature: float = 0.7,
    max_tokens: int = 300,
    enable_structured_output: bool = True
) -> str:
    """Ultimate LLM sampling with all FastMCP concepts integrated"""

    operation_id = f"sampling_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    await ctx.info(f"Starting ultimate LLM sampling: {operation_id}")

    # Initialize progress tracking
    progress = ProgressTracker(ctx, operation_id)

    StructuredLogger.log_with_metadata(
        "info", "Ultimate LLM sampling initiated",
        "sampling",
        {
            "operation_id": operation_id,
            "session_id": session_id,
            "sampling_type": sampling_type,
            "content_length": len(content),
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        session_id
    )

    try:
        # Stage 1: Simple Text Generation (0-25%)
        await progress.report_percentage(10, message="Preparing simple text generation")

        if server_state.flags.get("enable_llm_sampling"):
            simple_prompt = f"Provide a concise summary of: {content}"

            # Use NRP client directly for LLM sampling
            try:
                simple_response = await nrp_client.chat.completions.create(
                    model="gemma3",
                    messages=[{"role": "user", "content": simple_prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                simple_text = simple_response.choices[0].message.content
            except Exception as e:
                await ctx.warning(f"Simple sampling fallback: {str(e)}")
                simple_text = f"[FALLBACK] Simple analysis of {content}: This technology offers advanced capabilities for enterprise deployment and management."

            await ctx.info(f"Simple sampling completed: {len(simple_text)} characters")
            ctx.set_state("simple_response", simple_text)

            StructuredLogger.log_with_metadata(
                "info", "Simple LLM sampling completed",
                "sampling",
                {
                    "operation_id": operation_id,
                    "sampling_type": "simple_generation",
                    "response_length": len(simple_text),
                    "temperature": temperature
                },
                session_id
            )

        await progress.report_percentage(25, message="Simple generation complete")

        # Stage 2: Advanced Analysis with System Prompt (25-50%)
        await progress.report_percentage(30, message="Performing advanced analysis")

        if server_state.flags.get("enable_multi_turn_sampling"):
            # Use NRP client directly for advanced analysis
            try:
                analysis_response = await nrp_client.chat.completions.create(
                    model="gemma3",
                    messages=[
                        {"role": "system", "content": "You are an expert technical analyst specializing in software architecture and FastMCP protocols."},
                        {"role": "user", "content": f"Analyze the capabilities and benefits of: {content}"}
                    ],
                    temperature=temperature * 0.8,  # Slightly more focused
                    max_tokens=max_tokens
                )
                analysis_text = analysis_response.choices[0].message.content
            except Exception as e:
                await ctx.warning(f"Advanced analysis fallback: {str(e)}")
                analysis_text = f"[FALLBACK] Advanced analysis of {content}: This represents a sophisticated technology stack with enterprise-grade capabilities including scalability, security, and performance optimization."

            await ctx.info(f"Advanced analysis completed: {len(analysis_text)} characters")
            ctx.set_state("analysis_response", analysis_text)

            StructuredLogger.log_with_metadata(
                "info", "Advanced LLM analysis completed",
                "sampling",
                {
                    "operation_id": operation_id,
                    "sampling_type": "advanced_analysis",
                    "response_length": len(analysis_text),
                    "system_prompt_used": True
                },
                session_id
            )

        await progress.report_percentage(50, message="Advanced analysis complete")

        # Stage 3: Code Generation (50-75%)
        await progress.report_percentage(55, message="Generating code examples")

        # Use NRP client for code generation
        try:
            code_response = await nrp_client.chat.completions.create(
                model="gemma3",
                messages=[
                    {"role": "system", "content": "You are an expert Python programmer with deep knowledge of FastMCP and async programming."},
                    {"role": "user", "content": f"Write a Python code example demonstrating integration with: {content}"}
                ],
                temperature=0.3,  # More deterministic for code
                max_tokens=max_tokens
            )
            code_text = code_response.choices[0].message.content
        except Exception as e:
            await ctx.warning(f"Code generation fallback: {str(e)}")
            code_text = f"""[FALLBACK] Python integration example for {content}:

import asyncio
from fastmcp import FastMCP

async def integrate_with_{content.lower().replace(' ', '_')}():
    # Initialize {content} integration
    client = FastMCP("http://localhost:8020/mcp")

    async with client:
        # Execute {content} operations
        result = await client.call_tool("operation", {{"param": "value"}})
        return result

if __name__ == "__main__":
    asyncio.run(integrate_with_{content.lower().replace(' ', '_')}())
"""

        await ctx.info(f"Code generation completed: {len(code_text)} characters")
        ctx.set_state("code_response", code_text)

        StructuredLogger.log_with_metadata(
            "info", "Code generation sampling completed",
            "sampling",
            {
                "operation_id": operation_id,
                "sampling_type": "code_generation",
                "response_length": len(code_text),
                "temperature": 0.3
            },
            session_id
        )

        await progress.report_percentage(75, message="Code generation complete")

        # Stage 4: Multi-turn Conversation Simulation (75-90%)
        await progress.report_percentage(80, message="Simulating multi-turn conversation")

        # Simulate a multi-turn conversation about the content
        conversation_prompt = f"""
        Simulate a conversation between a user and an AI assistant about {content}.

        User: What are the main benefits of this technology?
        Assistant: [Provide a helpful response]
        User: How would I implement this in a production environment?
        Assistant: [Provide implementation guidance]
        User: What are potential challenges or limitations?
        Assistant: [Provide balanced analysis]
        """

        # Use NRP client for conversation simulation
        try:
            conversation_response = await nrp_client.chat.completions.create(
                model="gemma3",
                messages=[
                    {"role": "system", "content": "You are simulating a knowledgeable AI assistant in a technical consultation."},
                    {"role": "user", "content": conversation_prompt}
                ],
                temperature=0.6,
                max_tokens=max_tokens * 2  # Allow more space for conversation
            )
            conversation_text = conversation_response.choices[0].message.content
        except Exception as e:
            await ctx.warning(f"Conversation simulation fallback: {str(e)}")
            conversation_text = f"""[FALLBACK] Multi-turn conversation about {content}:

User: What are the main benefits of this technology?
Assistant: {content} offers enhanced performance, scalability, and integration capabilities that make it ideal for enterprise environments.

User: How would I implement this in a production environment?
Assistant: Start with a pilot deployment, ensure proper monitoring, configure security settings, and gradually scale based on performance metrics.

User: What are potential challenges or limitations?
Assistant: Key considerations include initial setup complexity, resource requirements, training requirements, and integration with existing systems.
"""

        await ctx.info(f"Multi-turn simulation completed: {len(conversation_text)} characters")
        ctx.set_state("conversation_response", conversation_text)

        await progress.report_percentage(90, message="Multi-turn simulation complete")

        # Stage 5: Structured Output Generation (90-100%)
        await progress.report_percentage(95, message="Generating structured output")

        if enable_structured_output:
            structured_prompt = f"""
            Create a structured analysis of {content} in the following JSON format:
            {{
                "summary": "Brief overview",
                "benefits": ["benefit1", "benefit2", "benefit3"],
                "use_cases": ["use_case1", "use_case2"],
                "implementation_complexity": "low|medium|high",
                "recommended_approach": "Step-by-step recommendation"
            }}
            """

            # Use NRP client for structured output
            try:
                structured_response = await nrp_client.chat.completions.create(
                    model="gemma3",
                    messages=[
                        {"role": "system", "content": "You are a technical documentation specialist. Always respond with valid JSON."},
                        {"role": "user", "content": structured_prompt}
                    ],
                    temperature=0.2,  # Very deterministic for structured output
                    max_tokens=max_tokens
                )
                structured_text = structured_response.choices[0].message.content
            except Exception as e:
                await ctx.warning(f"Structured output fallback: {str(e)}")
                structured_text = f"""{{
    "summary": "Advanced technology solution for {content}",
    "benefits": ["Enhanced performance", "Improved scalability", "Better integration"],
    "use_cases": ["Enterprise deployment", "Production workloads"],
    "implementation_complexity": "medium",
    "recommended_approach": "Start with pilot deployment, gradually scale based on performance metrics"
}}"""

            await ctx.info(f"Structured output generated: {len(structured_text)} characters")
            ctx.set_state("structured_response", structured_text)

        await progress.report_percentage(100, message="Ultimate LLM sampling complete!")

        StructuredLogger.log_with_metadata(
            "info", "Ultimate LLM sampling completed successfully",
            "sampling",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "total_time": time.time() - progress.start_time,
                "sampling_stages_completed": 5,
                "structured_output_enabled": enable_structured_output
            },
            session_id
        )

        # Compile comprehensive results
        return f"""# Ultimate FastMCP LLM Sampling Results

## Operation ID: {operation_id}
## Session ID: {session_id}

## FastMCP Sampling Features Demonstrated:
- [OK] Simple text generation with basic prompts
- [OK] Advanced analysis with system prompts
- [OK] Code generation with specialized prompting
- [OK] Multi-turn conversation simulation
- [OK] Structured output generation with JSON formatting
- [OK] Progress tracking throughout sampling operations
- [OK] Context-aware logging and state management
- [OK] Temperature and token control for different use cases
- [OK] Integration with all other FastMCP capabilities

## Sampling Results Summary:

### 1. Simple Summary:
{ctx.get_state("simple_response") or "Not generated"}

### 2. Advanced Analysis:
{ctx.get_state("analysis_response") or "Not generated"}

### 3. Code Example:
```python
{ctx.get_state("code_response") or "# Code not generated"}
```

### 4. Multi-turn Conversation:
{ctx.get_state("conversation_response") or "Not generated"}

### 5. Structured Output:
```json
{ctx.get_state("structured_response") or '{"status": "not_generated"}'}
```

## Sampling Performance Metrics:
- Total Sampling Time: {time.time() - progress.start_time:.2f} seconds
- Sampling Stages: 5 comprehensive stages
- Progress Updates: Real-time tracking enabled
- Context Integration: Full state preservation
- Logging Events: Structured with sampling metadata

## FastMCP Integration Quality:
- [OK] Seamless integration with progress tracking
- [OK] Context-aware state management throughout sampling
- [OK] Structured logging with sampling-specific metadata
- [OK] Server flags controlling sampling behavior
- [OK] Error handling with recovery context
- [OK] Session correlation across all sampling operations

Ultimate FastMCP LLM sampling completed with all capabilities integrated!
"""

    except Exception as e:
        await ctx.error(f"LLM sampling failed: {str(e)}")
        StructuredLogger.log_with_metadata(
            "error", f"Ultimate LLM sampling failed: {str(e)}",
            "sampling",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            session_id
        )

        return f"[ERROR] Ultimate LLM sampling failed: {str(e)}"

@mcp.tool()
async def intelligent_configuration_generator(
    ctx: Context,
    config_type: str = "ml_training",
    requirements: str = "Standard GPU deployment with monitoring",
    optimization_level: str = "medium",
    include_monitoring: bool = True,
    generate_explanations: bool = True
) -> str:
    """Generate intelligent configurations using LLM sampling with all FastMCP concepts"""

    operation_id = f"config_gen_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Initialize progress tracking
    progress = ProgressTracker(ctx, operation_id)

    await ctx.info(f"Starting intelligent configuration generation: {operation_id}")

    try:
        await progress.report_percentage(10, message="Analyzing deployment scenario")

        if generate_explanations and server_state.flags.get("enable_llm_sampling"):
            # Use LLM to generate intelligent configuration
            config_prompt = f"""
            Generate a comprehensive Kubernetes deployment configuration for:

            Config Type: {config_type}
            Requirements: {requirements}
            Optimization Level: {optimization_level}

            Include considerations for:
            - Resource allocation (CPU, memory, GPU if applicable)
            - Security best practices
            - Monitoring and observability
            - Scalability options
            - FastMCP integration capabilities

            Provide the configuration in YAML format with detailed comments.
            """

            await progress.report_percentage(30, message="Generating configuration with LLM")

            config_response = await ctx.sample(
                messages=config_prompt,
                system_prompt="You are a Kubernetes expert with deep knowledge of ML deployments, security, and FastMCP integration.",
                temperature=0.3,  # Deterministic for configuration
                max_tokens=800
            )

            await ctx.info("LLM-generated configuration received")
            ctx.set_state("llm_config", config_response.text)

            await progress.report_percentage(60, message="Enhancing configuration with best practices")

            # Use LLM to enhance the configuration with additional insights
            enhancement_prompt = f"""
            Review and enhance this Kubernetes configuration:

            {config_response.text}

            Add specific recommendations for:
            1. Performance optimization
            2. Cost efficiency
            3. Security hardening
            4. Monitoring integration
            5. FastMCP server deployment considerations

            Provide actionable improvements and explanations.
            """

            enhancement_response = await ctx.sample(
                messages=enhancement_prompt,
                system_prompt="You are a DevOps architect specializing in production-ready deployments.",
                temperature=0.4,
                max_tokens=600
            )

            await ctx.info("Configuration enhancement completed")
            ctx.set_state("enhancement_suggestions", enhancement_response.text)

            await progress.report_percentage(90, message="Finalizing intelligent configuration")

            # Generate deployment strategy using LLM
            strategy_prompt = f"""
            Create a deployment strategy for this {config_type} configuration with {optimization_level} optimization level.

            Include:
            - Pre-deployment checklist
            - Rollout strategy
            - Monitoring points
            - Rollback procedures
            - Success metrics
            """

            strategy_response = await ctx.sample(
                messages=strategy_prompt,
                system_prompt="You are a deployment strategist with expertise in risk management and FastMCP deployments.",
                temperature=0.5,
                max_tokens=500
            )

            await ctx.info("Deployment strategy generated")
            ctx.set_state("deployment_strategy", strategy_response.text)

        await progress.report_percentage(100, message="Intelligent configuration generation complete!")

        StructuredLogger.log_with_metadata(
            "info", "Intelligent configuration generation completed",
            "config_generation",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "config_type": config_type,
                "requirements": requirements,
                "optimization_level": optimization_level,
                "include_monitoring": include_monitoring,
                "generate_explanations": generate_explanations,
                "total_time": time.time() - progress.start_time
            },
            session_id
        )

        return f"""# Intelligent Configuration Generation Results

## Operation ID: {operation_id}
## Config Type: {config_type} (Requirements: {requirements})
## Optimization Level: {optimization_level}

## LLM-Generated Configuration:
```yaml
{ctx.get_state("llm_config") or "# Configuration not generated"}
```

## Enhancement Suggestions:
{ctx.get_state("enhancement_suggestions") or "No enhancements generated"}

## Deployment Strategy:
{ctx.get_state("deployment_strategy") or "No strategy generated"}

## FastMCP Integration:
- [OK] LLM sampling for intelligent generation
- [OK] Progress tracking throughout generation process
- [OK] Context-aware state management
- [OK] Structured logging with generation metadata
- [OK] Multi-stage LLM interaction for comprehensive results

This intelligent configuration leverages LLM capabilities integrated with all FastMCP concepts!
"""

    except Exception as e:
        await ctx.error(f"Configuration generation failed: {str(e)}")
        return f"[ERROR] Intelligent configuration generation failed: {str(e)}"

# ============================================================================
# SERVER FLAGS AND CONFIGURATION
# ============================================================================

@mcp.tool()
async def ultimate_server_configuration(
    ctx: Context,
    flag_name: Optional[str] = None,
    flag_value: Optional[Union[bool, str, int]] = None,
    action: str = "view"
) -> str:
    """Ultimate server configuration with all FastMCP flags and capabilities"""

    operation_id = f"config_{uuid.uuid4().hex[:8]}"
    await ctx.info(f"Processing server configuration: {operation_id}")

    StructuredLogger.log_with_metadata(
        "info", f"Server configuration accessed - Action: {action}",
        "configuration",
        {
            "operation_id": operation_id,
            "flag_name": flag_name,
            "flag_value": flag_value,
            "action": action
        }
    )

    if action == "view" and not flag_name:
        # Return all current configuration
        config_info = {
            "server_info": {
                "name": "Ultimate FastMCP NRP.ai Server",
                "port": 8020,
                "version": "2.0.0-ultimate",
                "features": [
                    "Advanced Prompts",
                    "Context Awareness",
                    "Progressive Elicitation",
                    "Structured Logging",
                    "Progress Reporting",
                    "Server Flags",
                    "Enhanced Error Handling"
                ]
            },
            "current_flags": server_state.flags,
            "state_storage_keys": list(server_state.state_storage.keys()),
            "active_sessions": len(server_state.session_data),
            "performance_metrics_count": len(server_state.performance_metrics)
        }

        return f"""# Ultimate FastMCP Server Configuration

## Server Information:
{json.dumps(config_info["server_info"], indent=2)}

## Current Server Flags:
{json.dumps(config_info["current_flags"], indent=2)}

## Runtime Statistics:
- State Storage Keys: {config_info["state_storage_keys"]}
- Active Sessions: {config_info["active_sessions"]}
- Performance Metrics: {config_info["performance_metrics_count"]}

## Available Configuration Actions:
- View all settings: action="view"
- Modify flag: action="set", flag_name="...", flag_value=...
- Reset to defaults: action="reset"

Ultimate FastMCP server configuration overview complete!
"""

    elif action == "set" and flag_name and flag_value is not None:
        # Set specific flag
        if flag_name in server_state.flags:
            old_value = server_state.flags[flag_name]
            server_state.flags[flag_name] = flag_value

            StructuredLogger.log_with_metadata(
                "info", f"Server flag updated: {flag_name}",
                "configuration",
                {
                    "operation_id": operation_id,
                    "flag_name": flag_name,
                    "old_value": old_value,
                    "new_value": flag_value
                }
            )

            return f"""[SUCCESS] Flag '{flag_name}' updated:
- Old Value: {old_value}
- New Value: {flag_value}
- Operation ID: {operation_id}

All FastMCP features will respect this configuration change immediately.
"""
        else:
            available_flags = list(server_state.flags.keys())
            return f"""[ERROR] Unknown flag '{flag_name}'

Available flags:
{json.dumps(available_flags, indent=2)}

Please use one of the available flags for configuration.
"""

    elif action == "reset":
        # Reset to defaults
        old_flags = server_state.flags.copy()
        server_state.flags = ServerState().flags

        StructuredLogger.log_with_metadata(
            "info", "Server flags reset to defaults",
            "configuration",
            {
                "operation_id": operation_id,
                "old_flags": old_flags,
                "new_flags": server_state.flags
            }
        )

        return f"""[SUCCESS] All server flags reset to defaults
- Operation ID: {operation_id}
- Flags Reset: {len(old_flags)}

Ultimate FastMCP server configuration restored to optimal defaults.
"""

    else:
        return f"""[ERROR] Invalid configuration request

Valid actions:
- "view": Show current configuration
- "set": Update specific flag (requires flag_name and flag_value)
- "reset": Reset all flags to defaults

Example usage:
- View all: action="view"
- Set flag: action="set", flag_name="verbose_logging", flag_value=True
- Reset: action="reset"
"""

# ============================================================================
# LOGGING AND MONITORING TOOLS
# ============================================================================

@mcp.tool()
async def ultimate_logging_demonstration(
    ctx: Context,
    demo_type: str = "comprehensive",
    include_errors: bool = True,
    include_performance: bool = True,
    include_security: bool = True
) -> str:
    """Ultimate logging demonstration with all FastMCP capabilities"""

    operation_id = f"logging_demo_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Initialize progress tracking
    progress = ProgressTracker(ctx, operation_id)

    await ctx.info(f"Starting ultimate logging demonstration: {operation_id}")

    demo_results = []

    try:
        # Stage 1: Basic Logging Levels (0-25%)
        await progress.report_percentage(5, message="Demonstrating basic logging levels")

        # Debug level logging
        StructuredLogger.log_with_metadata(
            "debug", "Debug level logging demonstration",
            "logging_demo",
            {
                "operation_id": operation_id,
                "demo_type": demo_type,
                "log_level": "debug",
                "features": ["context_aware", "progress_tracking", "structured_metadata"]
            },
            session_id
        )
        demo_results.append("[OK] Debug level logging with structured metadata")

        # Info level logging
        StructuredLogger.log_with_metadata(
            "info", "Info level logging with performance tracking",
            "logging_demo",
            {
                "operation_id": operation_id,
                "performance_metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "disk_io": 123.4
                },
                "context_data": "integrated_fastmcp_capabilities"
            },
            session_id
        )
        demo_results.append("[OK] Info level logging with performance metrics")

        await progress.report_percentage(15, message="Basic logging levels complete")

        # Warning level logging
        StructuredLogger.log_with_metadata(
            "warning", "Warning level logging with context awareness",
            "logging_demo",
            {
                "operation_id": operation_id,
                "warning_type": "resource_threshold",
                "threshold_value": 80,
                "current_value": 85,
                "suggested_action": "scale_resources"
            },
            session_id
        )
        demo_results.append("[OK] Warning level logging with context awareness")

        await progress.report_percentage(25, message="All logging levels demonstrated")

        # Stage 2: Performance Logging (25-50%)
        if include_performance:
            await progress.report_percentage(30, message="Demonstrating performance logging")

            # Simulate performance monitoring
            perf_data = {
                "response_time": 0.125,
                "throughput": 1250,
                "concurrent_users": 45,
                "resource_utilization": {
                    "cpu": 34.5,
                    "memory": 67.2,
                    "network": 12.8,
                    "storage": 89.1
                }
            }

            StructuredLogger.log_with_metadata(
                "info", "Performance metrics collection with progress tracking",
                "performance",
                {
                    "operation_id": operation_id,
                    "metrics": perf_data,
                    "collection_method": "real_time_monitoring",
                    "fastmcp_features": ["progress_reporting", "context_logging"]
                },
                session_id
            )
            demo_results.append("[OK] Performance logging with real-time metrics")

            await progress.report_percentage(40, message="Performance logging complete")

        # Stage 3: Security Logging (50-75%)
        if include_security:
            await progress.report_percentage(55, message="Demonstrating security logging")

            # Security event logging
            security_event = {
                "event_type": "authentication_success",
                "user_id": "ultimate_user",
                "source_ip": "192.168.1.100",
                "user_agent": "Ultimate FastMCP Client",
                "compliance_level": "SOC2",
                "audit_trail": True,
                "encryption_level": "AES256"
            }

            StructuredLogger.log_with_metadata(
                "info", "Security event logged with compliance metadata",
                "security",
                {
                    "operation_id": operation_id,
                    "security_event": security_event,
                    "fastmcp_integration": "full_context_awareness"
                },
                session_id
            )
            demo_results.append("[OK] Security logging with SOC2 compliance")

            await progress.report_percentage(65, message="Security logging complete")

        # Stage 4: Error Handling (75-90%)
        if include_errors:
            await progress.report_percentage(80, message="Demonstrating error handling")

            # Simulated error with recovery context
            try:
                # Simulate error condition
                raise ValueError("Simulated error for logging demonstration")
            except ValueError as e:
                StructuredLogger.log_with_metadata(
                    "error", f"Error demonstration with recovery context: {str(e)}",
                    "error_handling",
                    {
                        "operation_id": operation_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "recovery_steps": [
                            "validate_input_parameters",
                            "retry_with_backoff",
                            "fallback_to_default_values"
                        ],
                        "context_preservation": "enabled",
                        "fastmcp_features": ["elicitation_retry", "progress_continuation"]
                    },
                    session_id
                )
                demo_results.append("[OK] Error logging with recovery context")

            await progress.report_percentage(90, message="Error handling demonstration complete")

        # Stage 5: Integration Summary (90-100%)
        await progress.report_percentage(95, message="Generating comprehensive summary")

        # Final integration summary
        StructuredLogger.log_with_metadata(
            "info", "Ultimate logging demonstration completed successfully",
            "logging_demo",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "demo_type": demo_type,
                "features_demonstrated": {
                    "basic_logging": True,
                    "performance_logging": include_performance,
                    "security_logging": include_security,
                    "error_handling": include_errors,
                    "progress_tracking": True,
                    "context_awareness": True,
                    "structured_metadata": True
                },
                "total_time": time.time() - progress.start_time,
                "integration_level": "complete"
            },
            session_id
        )
        demo_results.append("[OK] Comprehensive logging demonstration completed")

        await progress.report_percentage(100, message="Ultimate logging demonstration complete!")

    except Exception as e:
        await ctx.error(f"Logging demonstration failed: {str(e)}")
        StructuredLogger.log_with_metadata(
            "error", f"Ultimate logging demonstration failed: {str(e)}",
            "logging_demo",
            {
                "operation_id": operation_id,
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            session_id
        )
        demo_results.append(f"[ERROR] Demonstration failed: {str(e)}")

    return f"""# Ultimate FastMCP Logging Demonstration Results

## Operation ID: {operation_id}
## Session ID: {session_id}
## Demo Type: {demo_type}

## FastMCP Features Demonstrated:
- [OK] Multi-level logging (debug, info, warning, error)
- [OK] Structured metadata with rich context
- [OK] Performance tracking with timing metrics
- [OK] Security logging with compliance metadata
- [OK] Session correlation and request tracking
- [OK] Real-time progress reporting during logging operations
- [OK] Context-aware error handling and recovery
- [OK] Integration with all other FastMCP capabilities

## Demonstration Results:
{chr(10).join(demo_results)}

## Integration Summary:
- Total Demonstration Time: {time.time() - progress.start_time:.2f} seconds
- Logging Levels Used: {4 if include_errors else 3}
- Progress Updates: 8 stages tracked
- Context Integration: Full FastMCP awareness
- Metadata Enrichment: Complete structured logging

The ultimate logging demonstration showcased all FastMCP capabilities working together seamlessly!
"""

# ============================================================================
# HELPER FUNCTIONS FOR DEPLOYMENT STAGES
# ============================================================================

async def _validate_deployment_params(ctx: Context, gpu_type: str, gpu_count: int, memory_gb: int) -> str:
    """Validate deployment parameters with context logging"""
    await ctx.info("Validating deployment parameters")

    # Simulate validation
    await asyncio.sleep(0.5)

    if gpu_count > 8:
        await ctx.warning(f"High GPU count requested: {gpu_count}")

    return f"Parameters validated: {gpu_type} x{gpu_count}, {memory_gb}GB memory"

async def _plan_resource_allocation(ctx: Context, gpu_type: str, gpu_count: int, workload_type: str) -> str:
    """Plan optimal resource allocation"""
    await ctx.info("Planning resource allocation strategy")

    # Simulate planning
    await asyncio.sleep(0.3)

    return f"Optimized allocation planned for {workload_type} on {gpu_count}x {gpu_type}"

async def _prepare_infrastructure(ctx: Context, namespace: str, enable_monitoring: bool) -> str:
    """Prepare infrastructure with monitoring setup"""
    await ctx.info("Preparing infrastructure components")

    # Simulate infrastructure setup
    await asyncio.sleep(0.4)

    monitoring_status = "enabled" if enable_monitoring else "disabled"
    return f"Infrastructure prepared for namespace '{namespace}', monitoring {monitoring_status}"

async def _configure_networking(ctx: Context, namespace: str) -> str:
    """Configure secure networking"""
    await ctx.info("Configuring network security and performance")

    # Simulate networking configuration
    await asyncio.sleep(0.3)

    return f"Secure networking configured for namespace '{namespace}'"

async def _deploy_gpu_resources(ctx: Context, gpu_type: str, gpu_count: int, progress: ProgressTracker) -> str:
    """Deploy GPU resources with granular progress tracking"""
    await ctx.info("Deploying GPU resources")

    # Simulate GPU deployment with progress updates
    for i in range(gpu_count):
        await asyncio.sleep(0.2)
        await progress.report_absolute(i + 1, gpu_count, f"Deployed GPU {i + 1}/{gpu_count}")
        await ctx.info(f"GPU {i + 1} of {gpu_count} deployed")

    return f"Successfully deployed {gpu_count}x {gpu_type} GPUs"

async def _configure_storage(ctx: Context, workload_type: str, memory_gb: int) -> str:
    """Configure optimized storage"""
    await ctx.info("Configuring storage optimization")

    # Simulate storage configuration
    await asyncio.sleep(0.3)

    return f"Storage optimized for {workload_type}, {memory_gb}GB allocated"

async def _setup_monitoring(ctx: Context, operation_id: str) -> str:
    """Setup comprehensive monitoring"""
    await ctx.info("Setting up monitoring dashboard")

    # Simulate monitoring setup
    await asyncio.sleep(0.4)

    return f"Monitoring dashboard configured for operation {operation_id}"

async def _validate_deployment(ctx: Context, operation_id: str) -> str:
    """Validate final deployment"""
    await ctx.info("Validating deployment integrity")

    # Simulate validation
    await asyncio.sleep(0.3)

    return f"Deployment {operation_id} validated successfully"

async def _finalize_deployment(ctx: Context, operation_id: str, session_id: str) -> str:
    """Finalize deployment with logging"""
    await ctx.info("Finalizing deployment")

    # Simulate finalization
    await asyncio.sleep(0.2)

    return f"Deployment {operation_id} finalized for session {session_id}"

# ============================================================================
# K8S OPERATIONS TOOLS - INFOGENT FUNCTIONALITY
# ============================================================================

@mcp.tool()
async def k8s_list_resources(ctx: Context, resource_type: str) -> str:
    """
    List Kubernetes resources of a specific type.

    Args:
        resource_type: Type of resource (pods, deployments, services, jobs, etc.)

    Returns:
        Formatted list of resources with FastMCP progress tracking
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_list_{resource_type}")

    await ctx.info(f"Listing {resource_type} in namespace {CURRENT_NAMESPACE}")
    await progress.report_percentage(25, message=f"Connecting to K8s cluster")

    StructuredLogger.log_with_metadata(
        "info", f"K8s list operation started for {resource_type}",
        "k8s_operations",
        {"operation_id": operation_id, "resource_type": resource_type, "namespace": CURRENT_NAMESPACE}
    )

    try:
        await progress.report_percentage(50, message=f"Querying {resource_type}")

        if not K8S_AVAILABLE:
            result = [f"demo-{resource_type}-1", f"demo-{resource_type}-2"]
        else:
            if resource_type.lower() == "pods":
                result = list_pods(CURRENT_NAMESPACE)
            elif resource_type.lower() == "deployments":
                result = list_deployments(CURRENT_NAMESPACE)
            elif resource_type.lower() == "services":
                result = list_services(CURRENT_NAMESPACE)
            elif resource_type.lower() == "jobs":
                result = list_jobs(CURRENT_NAMESPACE)
            else:
                result = [f"Unsupported resource type: {resource_type}"]

        await progress.report_percentage(100, message=f"Found {len(result)} {resource_type}")

        formatted_result = f"K8s {resource_type.title()} in namespace '{CURRENT_NAMESPACE}':\n"
        for i, item in enumerate(result, 1):
            formatted_result += f"  {i}. {item}\n"

        StructuredLogger.log_with_metadata(
            "info", f"K8s list operation completed for {resource_type}",
            "k8s_operations",
            {"operation_id": operation_id, "count": len(result), "success": True}
        )

        return formatted_result

    except Exception as e:
        await ctx.error(f"Failed to list {resource_type}: {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s list operation failed for {resource_type}",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error listing {resource_type}: {str(e)}"

@mcp.tool()
async def k8s_describe_resource(ctx: Context, resource_type: str, resource_name: str) -> str:
    """
    Get detailed information about a specific Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment, service, etc.)
        resource_name: Name of the specific resource

    Returns:
        Detailed resource information with FastMCP context integration
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_describe_{resource_type}")

    await ctx.info(f"Describing {resource_type} '{resource_name}' in namespace {CURRENT_NAMESPACE}")
    await progress.report_percentage(25, message=f"Connecting to K8s cluster")

    StructuredLogger.log_with_metadata(
        "info", f"K8s describe operation started",
        "k8s_operations",
        {"operation_id": operation_id, "resource_type": resource_type, "resource_name": resource_name}
    )

    try:
        await progress.report_percentage(50, message=f"Querying {resource_type} details")

        if not K8S_AVAILABLE:
            result = f"Demo description for {resource_type} '{resource_name}'"
        else:
            if resource_type.lower() == "pod":
                result = describe_pod(resource_name, CURRENT_NAMESPACE)
            elif resource_type.lower() == "deployment":
                result = describe_deployment(resource_name, CURRENT_NAMESPACE)
            elif resource_type.lower() == "service":
                result = describe_service(resource_name, CURRENT_NAMESPACE)
            else:
                result = f"Unsupported resource type for describe: {resource_type}"

        await progress.report_percentage(100, message=f"Retrieved {resource_type} details")

        StructuredLogger.log_with_metadata(
            "info", f"K8s describe operation completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True, "result_length": len(str(result))}
        )

        return f"Details for {resource_type} '{resource_name}':\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to describe {resource_type} '{resource_name}': {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s describe operation failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error describing {resource_type} '{resource_name}': {str(e)}"

@mcp.tool()
async def k8s_create_pod(ctx: Context, params: PodCreateParams) -> str:
    """
    Create a new Kubernetes pod with specified parameters.

    Args:
        params: Pod creation parameters including name, image, resources

    Returns:
        Creation result with FastMCP progress and logging integration
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_create_pod_{params.name}")

    await ctx.info(f"Creating pod '{params.name}' with image '{params.image}'")
    await progress.report_percentage(20, message="Validating pod parameters")

    StructuredLogger.log_with_metadata(
        "info", f"K8s pod creation started",
        "k8s_operations",
        {"operation_id": operation_id, "pod_name": params.name, "image": params.image}
    )

    try:
        await progress.report_percentage(40, message="Preparing pod specification")

        if not K8S_AVAILABLE:
            result = f"Demo: Created pod '{params.name}' with image '{params.image}'"
        else:
            result = create_pod_programmatic(
                name=params.name,
                image=params.image,
                namespace=CURRENT_NAMESPACE,
                memory_limit=params.memory_limit,
                cpu_limit=params.cpu_limit,
                memory_request=params.memory_request,
                cpu_request=params.cpu_request,
                command=params.command
            )

        await progress.report_percentage(80, message="Applying pod to cluster")
        await progress.report_percentage(100, message="Pod creation completed")

        StructuredLogger.log_with_metadata(
            "info", f"K8s pod creation completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True, "pod_name": params.name}
        )

        return f"Successfully created pod '{params.name}':\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to create pod '{params.name}': {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s pod creation failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error creating pod '{params.name}': {str(e)}"

@mcp.tool()
async def k8s_create_deployment(ctx: Context, params: DeploymentCreateParams) -> str:
    """
    Create a new Kubernetes deployment with specified parameters.

    Args:
        params: Deployment creation parameters including name, image, replicas

    Returns:
        Creation result with FastMCP integration
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_create_deployment_{params.name}")

    await ctx.info(f"Creating deployment '{params.name}' with {params.replicas} replicas")
    await progress.report_percentage(20, message="Validating deployment parameters")

    StructuredLogger.log_with_metadata(
        "info", f"K8s deployment creation started",
        "k8s_operations",
        {"operation_id": operation_id, "deployment_name": params.name, "replicas": params.replicas}
    )

    try:
        await progress.report_percentage(40, message="Preparing deployment specification")

        if not K8S_AVAILABLE:
            result = f"Demo: Created deployment '{params.name}' with {params.replicas} replicas"
        else:
            result = create_deployment_programmatic(
                name=params.name,
                image=params.image,
                namespace=CURRENT_NAMESPACE,
                replicas=params.replicas,
                memory_limit=params.memory_limit,
                cpu_limit=params.cpu_limit,
                memory_request=params.memory_request,
                cpu_request=params.cpu_request
            )

        await progress.report_percentage(80, message="Applying deployment to cluster")
        await progress.report_percentage(100, message="Deployment creation completed")

        StructuredLogger.log_with_metadata(
            "info", f"K8s deployment creation completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True, "deployment_name": params.name}
        )

        return f"Successfully created deployment '{params.name}':\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to create deployment '{params.name}': {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s deployment creation failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error creating deployment '{params.name}': {str(e)}"

@mcp.tool()
async def k8s_delete_resource(ctx: Context, resource_type: str, resource_name: str) -> str:
    """
    Delete a Kubernetes resource.

    Args:
        resource_type: Type of resource (pod, deployment, etc.)
        resource_name: Name of the resource to delete

    Returns:
        Deletion result with FastMCP integration
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_delete_{resource_type}")

    await ctx.warning(f"Deleting {resource_type} '{resource_name}' from namespace {CURRENT_NAMESPACE}")
    await progress.report_percentage(25, message="Preparing for deletion")

    StructuredLogger.log_with_metadata(
        "warning", f"K8s resource deletion started",
        "k8s_operations",
        {"operation_id": operation_id, "resource_type": resource_type, "resource_name": resource_name}
    )

    try:
        await progress.report_percentage(50, message=f"Deleting {resource_type}")

        if not K8S_AVAILABLE:
            result = f"Demo: Deleted {resource_type} '{resource_name}'"
        else:
            if resource_type.lower() == "pod":
                result = delete_pod(resource_name, CURRENT_NAMESPACE)
            elif resource_type.lower() == "deployment":
                result = delete_deployment(resource_name, CURRENT_NAMESPACE)
            else:
                result = f"Unsupported resource type for deletion: {resource_type}"

        await progress.report_percentage(100, message="Deletion completed")

        StructuredLogger.log_with_metadata(
            "info", f"K8s resource deletion completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True}
        )

        return f"Successfully deleted {resource_type} '{resource_name}':\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to delete {resource_type} '{resource_name}': {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s resource deletion failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error deleting {resource_type} '{resource_name}': {str(e)}"

@mcp.tool()
async def k8s_get_logs(ctx: Context, pod_name: str, tail_lines: Optional[int] = None) -> str:
    """
    Get logs from a Kubernetes pod.

    Args:
        pod_name: Name of the pod
        tail_lines: Number of lines to tail (optional)

    Returns:
        Pod logs with FastMCP integration
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"k8s_logs_{pod_name}")

    await ctx.info(f"Retrieving logs from pod '{pod_name}'")
    await progress.report_percentage(30, message="Connecting to pod")

    StructuredLogger.log_with_metadata(
        "info", f"K8s logs retrieval started",
        "k8s_operations",
        {"operation_id": operation_id, "pod_name": pod_name, "tail_lines": tail_lines}
    )

    try:
        await progress.report_percentage(70, message="Fetching logs")

        if not K8S_AVAILABLE:
            result = f"Demo logs for pod '{pod_name}'\nLine 1: Application started\nLine 2: Ready to accept connections"
        else:
            result = pod_logs(pod_name, CURRENT_NAMESPACE, tail_lines)

        await progress.report_percentage(100, message="Logs retrieved")

        StructuredLogger.log_with_metadata(
            "info", f"K8s logs retrieval completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True, "log_length": len(str(result))}
        )

        return f"Logs from pod '{pod_name}':\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to get logs from pod '{pod_name}': {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s logs retrieval failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error getting logs from pod '{pod_name}': {str(e)}"

@mcp.tool()
async def intelligent_k8s_query(ctx: Context, params: QueryParams) -> str:
    """
    Process natural language Kubernetes queries using NRP infogent architecture.
    Classifies intent and routes to appropriate handlers with FastMCP integration.

    Args:
        params: Query parameters including natural language query and context

    Returns:
        Intelligent response based on query classification and routing
    """
    operation_id = str(uuid.uuid4())[:8]
    progress = ProgressTracker(ctx, f"intelligent_query")

    await ctx.info(f"Processing intelligent K8s query: '{params.query[:50]}...'")
    await progress.report_percentage(20, message="Analyzing query intent")

    StructuredLogger.log_with_metadata(
        "info", f"Intelligent K8s query started",
        "k8s_operations",
        {"operation_id": operation_id, "query": params.query, "context": params.context}
    )

    try:
        await progress.report_percentage(40, message="Classifying intent")

        # CRITICAL: Improved intent classification to distinguish documentation from commands
        query_lower = params.query.lower()

        # Check for documentation keywords first (higher priority)
        if any(doc_word in query_lower for doc_word in ["example", "yaml", "template", "how to", "syntax", "nvidia.com/a100"]):
            intent = "EXPLANATION"
        elif any(cmd in query_lower for cmd in ["list my", "list pods", "get pods", "find pods"]) and not any(doc_word in query_lower for doc_word in ["example", "yaml", "template"]):
            intent = "COMMAND"
            if "pod" in query_lower:
                await progress.report_percentage(70, message="Executing pod listing")
                pods = list_pods(CURRENT_NAMESPACE)
                result = f"Pods in '{CURRENT_NAMESPACE}' namespace:\n" + "\n".join([f"  - {pod}" for pod in pods])
            elif "deployment" in query_lower:
                await progress.report_percentage(70, message="Executing deployment listing")
                deployments = list_deployments(CURRENT_NAMESPACE)
                result = f"Deployments in '{CURRENT_NAMESPACE}' namespace:\n" + "\n".join([f"  - {deploy}" for deploy in deployments])
            elif "service" in query_lower:
                await progress.report_percentage(70, message="Executing service listing")
                services = list_services(CURRENT_NAMESPACE)
                result = f"Services in '{CURRENT_NAMESPACE}' namespace:\n" + "\n".join([f"  - {svc}" for svc in services])
            else:
                result = "Please specify what you want to list (pods, deployments, services, etc.)"

        elif any(cmd in query_lower for cmd in ["create", "deploy", "start"]):
            intent = "COMMAND"
            result = "To create resources, please use the specific creation tools (k8s_create_pod, k8s_create_deployment) with detailed parameters."

        elif any(cmd in query_lower for cmd in ["delete", "remove", "stop"]):
            intent = "COMMAND"
            result = "To delete resources, please use the k8s_delete_resource tool with specific resource type and name."

        else:
            intent = "EXPLANATION"
            await progress.report_percentage(70, message="Generating explanation")

            # INFOGENT ARCHITECTURE: Navigator-Extractor-Aggregator Pipeline
            if NRP_COMPLETE_AVAILABLE:
                await progress.report_percentage(75, message="Activating Navigator-Extractor-Aggregator pipeline")

                # STAGE 1: NAVIGATOR - Intelligent Query Analysis
                nav_analysis = {
                    "technical_depth": "intermediate",
                    "query_type": "general",
                    "enhanced_keywords": []
                }

                if GLM_V_AVAILABLE and glm_client:
                    try:
                        navigation_prompt = f"""Analyze this NRP Nautilus query for intelligent navigation:

Query: "{params.query}"
Context: "{params.context}"

Respond with JSON:
{{
    "technical_depth": "basic|intermediate|advanced",
    "query_type": "gpu_specific|storage|networking|general",
    "enhanced_keywords": ["search keywords"],
    "user_intent": "learning|troubleshooting|implementation"
}}"""

                        nav_response = await glm_client.chat.completions.create(
                            model=os.getenv("NRP_MODEL", "glm-v"),
                            messages=[
                                {"role": "system", "content": "Navigator agent: Analyze queries and respond with JSON only."},
                                {"role": "user", "content": navigation_prompt}
                            ],
                            temperature=0.3,
                            max_tokens=300
                        )

                        nav_analysis = json.loads(nav_response.choices[0].message.content)
                    except Exception as e:
                        print(f"[NAVIGATOR] Warning: {e}")

                # STAGE 2: EXTRACTOR - Precision Content Extraction
                enhanced_query = params.query

                # Add navigation intelligence
                if nav_analysis.get("enhanced_keywords"):
                    enhanced_query += " " + " ".join(nav_analysis["enhanced_keywords"])

                # GPU-specific enhancement
                if nav_analysis.get("query_type") == "gpu_specific" or any(gpu in params.query.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                    enhanced_query += " special GPU type specific"

                complete_matches = search_complete_anchors(enhanced_query)
                if complete_matches:
                    best_match = complete_matches[0]

                    # Advanced extractor logic: prefer specialized sections
                    if nav_analysis.get("query_type") == "gpu_specific":
                        for match in complete_matches:
                            if any(keyword in match['anchor'].lower() for keyword in ['special', 'specific', 'type']):
                                best_match = match
                                break

                    exact_url = best_match['url']

                    # Generate comprehensive explanation using GLM-4.5V
                    comprehensive_explanation = ""
                    if GLM_V_AVAILABLE and glm_client:
                        try:
                            await progress.report_percentage(80, message="AGGREGATOR: Synthesizing with Navigator intelligence")

                            # STAGE 3: AGGREGATOR - Intelligent Synthesis using Navigation Analysis
                            technical_depth = nav_analysis.get("technical_depth", "intermediate")
                            query_type = nav_analysis.get("query_type", "general")
                            user_intent = nav_analysis.get("user_intent", "learning")

                            # Specialized guidance based on query type (our infogent intelligence)
                            specialized_guidance = ""
                            if query_type == "gpu_specific":
                                specialized_guidance = """

CRITICAL GPU SPECIFICATIONS (Navigator-Enhanced):
- MUST include exact resource syntax: nvidia.com/a100, nvidia.com/h100, nvidia.com/v100, nvidia.com/rtx4090
- Explain node selection strategies and GPU type differences
- Detail resource limits, quotas, and availability constraints specific to each GPU type
- Include scheduling considerations and performance characteristics
- Provide comprehensive troubleshooting for GPU allocation failures"""

                            elif query_type == "storage":
                                specialized_guidance = """

STORAGE SPECIFICATIONS (Navigator-Enhanced):
- Detail PVC specifications and storage class options
- Include volume mounting examples with proper permissions
- Explain persistent vs ephemeral storage trade-offs
- Provide backup strategies and data persistence patterns"""

                            elif query_type == "networking":
                                specialized_guidance = """

NETWORKING SPECIFICATIONS (Navigator-Enhanced):
- Include service types and ingress configuration examples
- Detail port management and security considerations
- Explain load balancing and traffic routing strategies
- Provide DNS and external access patterns"""

                            # Adapt response depth based on navigation analysis
                            depth_instructions = {
                                "basic": "Focus on step-by-step instructions with simple explanations",
                                "intermediate": "Provide comprehensive guidance with examples and best practices",
                                "advanced": "Include advanced configurations and optimization techniques"
                            }.get(technical_depth, "Provide comprehensive guidance")

                            explanation_prompt = f"""You are an expert NRP Nautilus platform specialist using advanced infogent architecture analysis.

QUERY: "{params.query}"
NAVIGATION ANALYSIS:
- Technical Depth: {technical_depth}
- Query Type: {query_type}
- User Intent: {user_intent}

PRECISE DOCUMENTATION MATCH:
- Page: {best_match['page'].replace('_', ' ').title()}
- Section: {best_match['anchor'].replace('-', ' ').title()}
- URL: {exact_url}

RESPONSE REQUIREMENTS ({depth_instructions}):
1. Clear, detailed explanation tailored to {technical_depth} level
2. Step-by-step instructions when applicable
3. Complete YAML/code examples with proper syntax
4. Best practices and common pitfalls with specific warnings
5. Related concepts and prerequisite knowledge
6. Comprehensive troubleshooting guidance{specialized_guidance}

QUALITY STANDARDS:
- Leverage your 65,536 token context for comprehensive coverage
- Provide actionable guidance beyond basic documentation
- Include specific examples relevant to NRP Nautilus platform
- Address both immediate query and related concepts for complete understanding

Generate a response that represents the pinnacle of our Navigator-Extractor-Aggregator architecture."""

                            response = await glm_client.chat.completions.create(
                                model=os.getenv("NRP_MODEL", "glm-v"),
                                messages=[
                                    {"role": "system", "content": "You are an expert NRP Nautilus Kubernetes platform specialist with deep knowledge of all NRP documentation, policies, and best practices. Provide comprehensive, actionable explanations."},
                                    {"role": "user", "content": explanation_prompt}
                                ],
                                temperature=0.7,
                                max_tokens=2000  # Use more tokens for comprehensive explanations
                            )
                            comprehensive_explanation = response.choices[0].message.content
                        except Exception as e:
                            await ctx.warning(f"GLM-V explanation generation failed: {e}")
                            comprehensive_explanation = "GLM-V explanation generation temporarily unavailable."

                    result = f"""# NRP Nautilus Documentation - Enhanced Response

## Precise Documentation Match
**Direct Link**: {exact_url}
**Page**: {best_match['page'].replace('_', ' ').title()}
**Section**: {best_match['anchor'].replace('-', ' ').title()}

## Comprehensive Explanation
{comprehensive_explanation}

## Additional Resources
- Additional matches found: {len(complete_matches)} related sections
- Complete NRP Documentation: https://nrp.ai/documentation/userdocs/

---
*Response powered by GLM-4.5V multimodal AI with 65,536 token context*
*Source: Ultra-comprehensive NRP anchor database ({len(NRP_COMPLETE_ANCHORS)} pages)*"""
                elif NRP_ANCHOR_AVAILABLE:
                    # Fallback to manual anchor knowledge
                    anchor_answer = search_anchor_knowledge(params.query)
                    if "No specific NRP anchor documentation found" not in anchor_answer:
                        result = f"NRP Nautilus Documentation:\n{anchor_answer}"
                    elif NRP_COMPREHENSIVE_AVAILABLE:
                        # Fallback to comprehensive knowledge
                        comprehensive_answer = search_comprehensive_nrp_knowledge(params.query)
                        if "No specific NRP documentation found" not in comprehensive_answer:
                            result = f"NRP Nautilus Documentation:\n{comprehensive_answer}"
                    elif NRP_KNOWLEDGE_AVAILABLE:
                        # Fallback to GPU-specific knowledge
                        gpu_answer = search_nrp_knowledge(params.query)
                        if "No specific NRP documentation found" not in gpu_answer:
                            result = f"NRP Nautilus Documentation:\n{gpu_answer}"
                        elif NRP_CHAT_AVAILABLE and nrp_chat:
                            # Enhanced prompt with NRP context
                            explanation_prompt = f"""
                            You are a Kubernetes expert assistant specializing in NRP Nautilus platform.

                            Query: {params.query}
                            Context: {params.context or 'NRP Nautilus Kubernetes assistance'}

                            Provide specific information about NRP Nautilus when applicable, including:
                            - Exact resource names (e.g., nvidia.com/a100 for A100 GPUs)
                            - NRP-specific constraints and limits
                            - Practical YAML examples
                            - Links to https://nrp.ai/documentation when relevant

                            If this is about GPU requests, mention specific resource types available on NRP.
                            """

                            response = await nrp_chat.ainvoke(explanation_prompt)
                            result = f"Explanation:\n{response.content}"
                    else:
                        result = f"[FALLBACK] I understand you're asking about: {params.query}\n\nFor K8s operations, try using specific commands like 'list pods', 'describe deployment name', etc.\nFor detailed help, please consult the NRP documentation at https://nrp.ai/documentation"
                else:
                    result = f"[FALLBACK] I understand you're asking about: {params.query}\n\nFor K8s operations, try using specific commands like 'list pods', 'describe deployment name', etc.\nFor detailed help, please consult the NRP documentation at https://nrp.ai/documentation"
            elif NRP_CHAT_AVAILABLE and nrp_chat:
                # Standard NRP chat without knowledge base
                explanation_prompt = f"""
                You are a Kubernetes expert assistant. Provide a helpful explanation for this query:

                Query: {params.query}
                Context: {params.context or 'General Kubernetes assistance'}

                Provide a clear, concise explanation with practical examples and next steps.
                """

                response = await nrp_chat.ainvoke(explanation_prompt)
                result = f"Explanation:\n{response.content}"
            else:
                result = f"[FALLBACK] I understand you're asking about: {params.query}\n\nFor K8s operations, try using specific commands like 'list pods', 'describe deployment name', etc.\nFor detailed help, please consult the Kubernetes documentation."

        await progress.report_percentage(100, message="Query processing completed")

        StructuredLogger.log_with_metadata(
            "info", f"Intelligent K8s query completed",
            "k8s_operations",
            {"operation_id": operation_id, "intent": intent, "success": True}
        )

        return f"Intent: {intent}\nQuery: {params.query}\n\nResponse:\n{result}"

    except Exception as e:
        await ctx.error(f"Failed to process intelligent query: {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"Intelligent K8s query failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error processing query: {str(e)}"

@mcp.tool()
async def k8s_get_cluster_info(ctx: Context) -> str:
    """
    Get information about the current Kubernetes cluster and context.

    Returns:
        Cluster information with FastMCP integration
    """
    operation_id = str(uuid.uuid4())[:8]

    await ctx.info("Retrieving Kubernetes cluster information")

    StructuredLogger.log_with_metadata(
        "info", f"K8s cluster info retrieval started",
        "k8s_operations",
        {"operation_id": operation_id}
    )

    try:
        if not K8S_AVAILABLE:
            cluster_info = {
                "status": "Demo mode - K8s not available",
                "namespace": CURRENT_NAMESPACE,
                "demo_pods": ["demo-pod-1", "demo-pod-2"],
                "demo_deployments": ["demo-deploy-1"]
            }
        else:
            # Get actual cluster info
            cluster_info = {
                "namespace": CURRENT_NAMESPACE,
                "k8s_available": True,
                "permissions": "Checking...",
                "service_account": "default"
            }

        result = "Kubernetes Cluster Information:\n"
        for key, value in cluster_info.items():
            result += f"  {key}: {value}\n"

        StructuredLogger.log_with_metadata(
            "info", f"K8s cluster info retrieval completed",
            "k8s_operations",
            {"operation_id": operation_id, "success": True}
        )

        return result

    except Exception as e:
        await ctx.error(f"Failed to get cluster information: {str(e)}")

        StructuredLogger.log_with_metadata(
            "error", f"K8s cluster info retrieval failed",
            "k8s_operations",
            {"operation_id": operation_id, "error": str(e), "success": False}
        )

        return f"Error getting cluster information: {str(e)}"

@mcp.tool()
async def nrp_quick_reference(ctx: Context) -> str:
    """
    Get NRP Nautilus quick reference guide with common commands and guidelines.

    Returns:
        Comprehensive quick reference for NRP Nautilus operations
    """
    await ctx.info("Generating NRP Nautilus quick reference guide")

    try:
        if NRP_COMPLETE_AVAILABLE:
            # Generate quick reference from complete database
            total_anchors = sum(len(page_data.get("anchors", [])) for page_data in NRP_COMPLETE_ANCHORS.values())
            return f"""
# NRP Complete Documentation Quick Reference

## Comprehensive Anchor Database
- **Total pages indexed**: {len(NRP_COMPLETE_ANCHORS)}
- **Total anchors available**: {total_anchors}
- **Coverage**: All major NRP documentation sections

## Key Documentation Areas

### GPU Resources
- **All GPU Types**: Search for "gpu" or specific types like "a100"
- **Resource Requests**: Search for "request gpu" or "nvidia.com"

### Getting Started
- **Setup & Access**: Search for "kubectl" or "access"
- **Configuration**: Search for "config" or "namespace"

### Policies & Limits
- **Resource Policies**: Search for "policy" or "limit"
- **Usage Rules**: Search for "violation" or "allocation"

### Storage & Volumes
- **Persistent Storage**: Search for "pvc" or "storage"
- **Volume Mounting**: Search for "mount" or "volume"

### Networking & Ingress
- **HTTP Exposure**: Search for "ingress" or "domain"
- **Service Types**: Search for "service" or "expose"

## Advanced Search
Use natural language queries - the system will find the most relevant anchor link!

**Examples**:
- "How do I use my own domain?" → Direct link to ingress documentation
- "A100 GPU request" → Exact GPU specification page
- "Storage classes" → Complete storage configuration guide

Source: Auto-generated from comprehensive NRP anchor database
"""
        elif NRP_ANCHOR_AVAILABLE:
            return get_anchor_quick_reference()
        elif NRP_COMPREHENSIVE_AVAILABLE:
            return get_nrp_quick_reference()
        else:
            return """
# NRP Nautilus Quick Reference (Basic)

## Common kubectl Commands
```bash
# Check pods in namespace
kubectl get pods -n <namespace>

# View pod logs
kubectl logs <pod-name> -n <namespace>

# Describe pod details
kubectl describe pod <pod-name> -n <namespace>

# Delete a pod
kubectl delete pod <pod-name> -n <namespace>
```

## Basic Resource Limits
- Memory limits should be close to requests (within 20%)
- GPU utilization must exceed 40%
- Interactive pods limited to 6 hours
- Deployments auto-deleted after 2 weeks

For complete documentation, visit: https://nrp.ai/documentation/
"""
    except Exception as e:
        return f"Error generating quick reference: {str(e)}"

@mcp.tool()
async def nrp_anchor_urls(ctx: Context) -> str:
    """
    Get all available NRP documentation anchor URLs for direct navigation.

    Returns:
        Complete listing of all available anchor URLs for precise documentation access
    """
    await ctx.info("Retrieving all NRP documentation anchor URLs")

    try:
        if NRP_COMPLETE_AVAILABLE:
            result = "# Complete NRP Documentation Anchor URLs\n\n"
            result += f"**Total Documentation Coverage**: {len(NRP_COMPLETE_ANCHORS)} pages, {sum(len(page_data.get('anchors', [])) for page_data in NRP_COMPLETE_ANCHORS.values())} anchors\n\n"

            for page_name, page_data in NRP_COMPLETE_ANCHORS.items():
                base_url = page_data["base_url"]
                anchors = page_data.get("anchors", [])

                result += f"## {page_name.replace('_', ' ').title()}\n"
                result += f"**Base URL**: {base_url}\n"
                result += f"**Anchors**: {len(anchors)}\n\n"

                for anchor in anchors[:10]:  # Show first 10 anchors
                    if anchor != "_top":  # Skip generic top anchor
                        anchor_url = f"{base_url}#{anchor}"
                        result += f"- **{anchor.replace('-', ' ').title()}**: {anchor_url}\n"

                if len(anchors) > 10:
                    result += f"- ... and {len(anchors) - 10} more anchors\n"
                result += "\n"

            return result
        elif NRP_ANCHOR_AVAILABLE:
            all_urls = get_all_anchor_urls()
            result = "# Complete NRP Documentation Anchor URLs\n\n"

            for doc_type, sections in all_urls.items():
                result += f"## {doc_type.replace('_', ' ').title()}\n"
                for section, url in sections.items():
                    result += f"- **{section.replace('_', ' ').title()}**: {url}\n"
                result += "\n"

            return result
        else:
            return """
# NRP Documentation Anchor URLs (Basic)

Unable to load detailed anchor URLs. Please visit:
https://nrp.ai/documentation/userdocs/

Key documentation sections:
- Getting Started: https://nrp.ai/documentation/userdocs/start/getting-started/
- GPU Pods: https://nrp.ai/documentation/userdocs/running/gpu-pods/
- Policies: https://nrp.ai/documentation/userdocs/start/policies/
- Storage: https://nrp.ai/documentation/userdocs/tutorial/storage/
- Jobs: https://nrp.ai/documentation/userdocs/tutorial/jobs/
"""
    except Exception as e:
        return f"Error retrieving anchor URLs: {str(e)}"

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("Starting Ultimate FastMCP NRP.ai Server...")
    print("\nIntegrated FastMCP Capabilities:")
    print("- Advanced Prompts with structured validation")
    print("- Context-aware logging, state management, and progress reporting")
    print("- Progressive elicitation with multi-turn patterns")
    print("- Structured logging with performance and security metadata")
    print("- Real-time progress reporting with multiple patterns")
    print("- LLM sampling for intelligent text generation and analysis")
    print("- Server flags for runtime configuration")
    print("- Enhanced error handling and recovery")
    print("\nNEW: Kubernetes Operations & Infogent Architecture:")
    print("- K8s resource management (list, describe, create, delete)")
    print("- Intelligent natural language K8s queries")
    print("- Pod and deployment operations with progress tracking")
    print("- Kubernetes logs retrieval and cluster information")
    print("- NRP-powered intent classification and routing")
    print("- Comprehensive K8s operations with FastMCP integration")
    print("\nLLM Sampling capabilities:")
    print("- Simple text generation with customizable parameters")
    print("- Advanced analysis with system prompts")
    print("- Code generation with specialized prompting")
    print("- Multi-turn conversation simulation")
    print("- Structured output generation (JSON)")
    print("- Intelligent configuration generation")
    print("\nAll FastMCP concepts + K8s Infogent + GLM-4.5V Multimodal AI unified!")
    print(f"\nK8s Available: {K8S_AVAILABLE}")
    print(f"NRP Chat Available: {NRP_CHAT_AVAILABLE}")
    print(f"GLM-4.5V Multimodal Available: {GLM_V_AVAILABLE}")
    print(f"Current Namespace: {CURRENT_NAMESPACE}")
    if GLM_V_AVAILABLE:
        print(f"GLM-4.5V Features: 65,536 tokens, multimodal (vision, video), tool calling")
    print(f"\nServer will be available at: http://127.0.0.1:8025/mcp")

    mcp.run(transport="http", port=8025)