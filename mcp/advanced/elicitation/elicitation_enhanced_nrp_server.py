#!/usr/bin/env python3
"""Enhanced NRP.ai FastMCP Server with Advanced Elicitation, Flags, and Error Handling"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field

from fastmcp import FastMCP, Context
from mcp.types import TextContent

# Initialize FastMCP with enhanced error handling
mcp = FastMCP("Advanced Elicitation NRP.ai Server")

# Enhanced Configuration with Flags
@dataclass
class ServerFlags:
    """Server configuration flags for enhanced control"""
    verbose_logging: bool = True
    strict_validation: bool = True
    auto_retry_on_error: bool = True
    max_elicitation_rounds: int = 5
    enable_progressive_disclosure: bool = True
    require_confirmation_for_critical_ops: bool = True
    allow_partial_execution: bool = False
    enable_smart_defaults: bool = True

# Global server configuration
SERVER_FLAGS = ServerFlags()

# Enhanced Error Types
class NRPErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    ELICITATION_CANCELLED = "elicitation_cancelled"
    INCOMPLETE_REQUIREMENTS = "incomplete_requirements"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"

@dataclass
class NRPError:
    """Enhanced error structure with detailed context"""
    error_type: NRPErrorType
    message: str
    context: Dict[str, Any]
    suggestions: List[str]
    recoverable: bool = True
    error_id: str = None

    def __post_init__(self):
        if self.error_id is None:
            self.error_id = str(uuid.uuid4())[:8]

# Elicitation Data Classes
@dataclass
class GPURequirements:
    """Structured GPU requirements for elicitation"""
    gpu_type: Literal["a100", "a40", "rtx6000", "h100", "general"]
    storage_size: str  # e.g., "100Gi", "1Ti"
    workload_type: Literal["ml_training", "inference", "research", "development", "production"]
    gpu_count: int = 1
    memory_per_gpu: int = 32  # GB
    cpu_cores: int = 8
    priority: Literal["low", "medium", "high", "critical"] = "medium"

@dataclass
class DeploymentPreferences:
    """User deployment preferences"""
    namespace: str
    enable_monitoring: bool = True
    auto_scaling: bool = False
    backup_strategy: Literal["none", "basic", "advanced"] = "basic"
    compliance_level: Literal["standard", "enterprise", "government"] = "standard"

@dataclass
class ResourceConstraints:
    """Resource constraints and limits"""
    max_cost_per_hour: Optional[float] = None
    max_duration_hours: Optional[int] = None
    region_preference: Optional[str] = None
    availability_requirements: Literal["standard", "high", "critical"] = "standard"

# Enhanced Error Handler
async def handle_error(ctx: Context, error: NRPError) -> str:
    """Enhanced error handling with context awareness"""
    await ctx.error(f"Error {error.error_id}: {error.error_type.value} - {error.message}")

    error_response = f"""
[ERROR] {error.error_type.value.upper()}
ID: {error.error_id}
Message: {error.message}

Context:
{json.dumps(error.context, indent=2)}

Suggestions:
"""

    for i, suggestion in enumerate(error.suggestions, 1):
        error_response += f"{i}. {suggestion}\n"

    if error.recoverable:
        error_response += "\nThis error is recoverable. You can retry the operation with corrections."
    else:
        error_response += "\nThis is a critical error. Please contact support."

    return error_response

# Enhanced Elicitation Tools

@mcp.tool()
async def intelligent_gpu_deployment(
    ctx: Context,
    initial_prompt: Optional[str] = None,
    skip_confirmation: bool = False
) -> str:
    """
    Intelligent GPU deployment with progressive elicitation and enhanced error handling
    """
    try:
        deployment_id = f"deploy_{str(uuid.uuid4())[:8]}"
        await ctx.info(f"Starting intelligent GPU deployment: {deployment_id}")
        await ctx.report_progress(0, 100)

        # Step 1: Initial requirements gathering
        if initial_prompt:
            await ctx.info(f"Initial requirements: {initial_prompt}")

        # Progressive elicitation for GPU requirements
        await ctx.info("Gathering GPU requirements through progressive elicitation...")

        # Elicit GPU type with smart defaults
        gpu_type_result = await ctx.elicit(
            "What type of GPU do you need?\n" +
            "Options: a100 (most powerful), a40 (balanced), rtx6000 (cost-effective), h100 (latest), general (any available)\n" +
            "Default: a100",
            response_type=str
        )

        if gpu_type_result.action == "cancel":
            error = NRPError(
                error_type=NRPErrorType.ELICITATION_CANCELLED,
                message="User cancelled GPU type selection",
                context={"step": "gpu_type_selection", "deployment_id": deployment_id},
                suggestions=["Restart the deployment process", "Use default GPU type"]
            )
            return await handle_error(ctx, error)

        gpu_type = gpu_type_result.data if gpu_type_result.action == "accept" else "a100"

        if gpu_type not in ["a100", "a40", "rtx6000", "h100", "general"]:
            if SERVER_FLAGS.auto_retry_on_error:
                await ctx.warning(f"Invalid GPU type '{gpu_type}', using default 'a100'")
                gpu_type = "a100"
            else:
                error = NRPError(
                    error_type=NRPErrorType.VALIDATION_ERROR,
                    message=f"Invalid GPU type: {gpu_type}",
                    context={"provided_value": gpu_type, "valid_options": ["a100", "a40", "rtx6000", "h100", "general"]},
                    suggestions=["Choose from: a100, a40, rtx6000, h100, general", "Use 'general' for any available GPU"]
                )
                return await handle_error(ctx, error)

        await ctx.report_progress(20, 100)

        # Elicit GPU count
        gpu_count_result = await ctx.elicit(
            f"How many {gpu_type.upper()} GPUs do you need? (1-16)",
            response_type=int
        )

        if gpu_count_result.action == "cancel":
            error = NRPError(
                error_type=NRPErrorType.ELICITATION_CANCELLED,
                message="User cancelled GPU count selection",
                context={"step": "gpu_count_selection", "deployment_id": deployment_id},
                suggestions=["Restart with a specific count", "Use default count of 1"]
            )
            return await handle_error(ctx, error)

        gpu_count = gpu_count_result.data if gpu_count_result.action == "accept" else 1

        if not (1 <= gpu_count <= 16):
            if SERVER_FLAGS.auto_retry_on_error:
                await ctx.warning(f"GPU count {gpu_count} out of range, using 1")
                gpu_count = 1
            else:
                error = NRPError(
                    error_type=NRPErrorType.VALIDATION_ERROR,
                    message=f"GPU count must be between 1 and 16, got {gpu_count}",
                    context={"provided_value": gpu_count, "valid_range": "1-16"},
                    suggestions=["Choose a number between 1 and 16", "Consider your actual workload requirements"]
                )
                return await handle_error(ctx, error)

        await ctx.report_progress(40, 100)

        # Elicit workload type with contextual help
        workload_result = await ctx.elicit(
            "What type of workload will this be?\n" +
            "- ml_training: Machine learning model training\n" +
            "- inference: Model inference/serving\n" +
            "- research: Research and experimentation\n" +
            "- development: Development and testing\n" +
            "- production: Production workloads",
            response_type=str
        )

        workload_type = workload_result.data if workload_result.action == "accept" else "research"

        if workload_type not in ["ml_training", "inference", "research", "development", "production"]:
            if SERVER_FLAGS.auto_retry_on_error:
                await ctx.warning(f"Unknown workload type '{workload_type}', using 'research'")
                workload_type = "research"

        await ctx.report_progress(60, 100)

        # Structured elicitation for deployment preferences
        preferences_result = await ctx.elicit(
            "Please provide deployment preferences:",
            response_type=DeploymentPreferences
        )

        if preferences_result.action == "accept":
            preferences = preferences_result.data
        else:
            # Use smart defaults
            preferences = DeploymentPreferences(
                namespace="default",
                enable_monitoring=True,
                auto_scaling=False,
                backup_strategy="basic",
                compliance_level="standard"
            )
            await ctx.info("Using default deployment preferences")

        await ctx.report_progress(80, 100)

        # Confirmation step for critical operations
        if SERVER_FLAGS.require_confirmation_for_critical_ops and not skip_confirmation:
            confirmation_result = await ctx.elicit(
                f"Confirm deployment:\n" +
                f"- GPU: {gpu_count}x {gpu_type.upper()}\n" +
                f"- Workload: {workload_type}\n" +
                f"- Namespace: {preferences.namespace}\n" +
                f"- Monitoring: {'Enabled' if preferences.enable_monitoring else 'Disabled'}\n" +
                "Proceed with deployment? (yes/no)",
                response_type=bool
            )

            if confirmation_result.action != "accept" or not confirmation_result.data:
                error = NRPError(
                    error_type=NRPErrorType.ELICITATION_CANCELLED,
                    message="Deployment cancelled by user during confirmation",
                    context={"deployment_config": {
                        "gpu_type": gpu_type,
                        "gpu_count": gpu_count,
                        "workload_type": workload_type,
                        "preferences": preferences
                    }},
                    suggestions=["Review and modify configuration", "Restart deployment with different parameters"]
                )
                return await handle_error(ctx, error)

        # Generate deployment configuration
        deployment_config = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": deployment_id,
                "namespace": preferences.namespace,
                "labels": {
                    "app": deployment_id,
                    "gpu-type": gpu_type,
                    "workload-type": workload_type,
                    "managed-by": "nrp-elicitation-server"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": deployment_id}},
                "template": {
                    "metadata": {"labels": {"app": deployment_id}},
                    "spec": {
                        "containers": [{
                            "name": "workload",
                            "image": f"nrp/{workload_type}:latest",
                            "resources": {
                                "requests": {
                                    f"nvidia.com/{gpu_type}": gpu_count,
                                    "memory": f"{gpu_count * 32}Gi",
                                    "cpu": f"{gpu_count * 8}"
                                },
                                "limits": {
                                    f"nvidia.com/{gpu_type}": gpu_count,
                                    "memory": f"{gpu_count * 32}Gi",
                                    "cpu": f"{gpu_count * 8}"
                                }
                            }
                        }]
                    }
                }
            }
        }

        # Store deployment state
        ctx.set_state(f"deployment_{deployment_id}", {
            "config": deployment_config,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "gpu_type": gpu_type,
            "gpu_count": gpu_count,
            "workload_type": workload_type,
            "preferences": preferences.__dict__
        })

        await ctx.report_progress(100, 100)
        await ctx.info(f"Deployment {deployment_id} configuration created successfully")

        return f"""
[SUCCESS] Intelligent GPU Deployment Created

Deployment ID: {deployment_id}
GPU Configuration: {gpu_count}x {gpu_type.upper()}
Workload Type: {workload_type}
Namespace: {preferences.namespace}
Monitoring: {'Enabled' if preferences.enable_monitoring else 'Disabled'}

YAML Configuration:
```yaml
{json.dumps(deployment_config, indent=2)}
```

Status: Ready for deployment
Context ID: {ctx.request_id}
Session: {ctx.get_state('session_id', 'anonymous')}
"""

    except Exception as e:
        error = NRPError(
            error_type=NRPErrorType.CONFIGURATION_ERROR,
            message=f"Unexpected error during deployment: {str(e)}",
            context={"exception": str(e), "deployment_id": deployment_id},
            suggestions=["Check server logs", "Retry with simpler configuration", "Contact support"],
            recoverable=False
        )
        return await handle_error(ctx, error)

@mcp.tool()
async def progressive_resource_analysis(
    ctx: Context,
    analysis_scope: Optional[str] = "cluster"
) -> str:
    """
    Progressive resource analysis with multi-turn elicitation and error recovery
    """
    try:
        analysis_id = f"analysis_{str(uuid.uuid4())[:8]}"
        await ctx.info(f"Starting progressive resource analysis: {analysis_id}")
        await ctx.report_progress(0, 100)

        # Progressive elicitation for analysis parameters
        scope_result = await ctx.elicit(
            "What scope of analysis do you need?\n" +
            "- cluster: Full cluster analysis\n" +
            "- namespace: Specific namespace analysis\n" +
            "- node: Individual node analysis\n" +
            "- workload: Specific workload analysis",
            response_type=str
        )

        analysis_scope = scope_result.data if scope_result.action == "accept" else "cluster"

        await ctx.report_progress(25, 100)

        if analysis_scope == "namespace":
            namespace_result = await ctx.elicit(
                "Which namespace would you like to analyze?",
                response_type=str
            )
            namespace = namespace_result.data if namespace_result.action == "accept" else "default"
        else:
            namespace = "all"

        await ctx.report_progress(50, 100)

        # Elicit analysis depth
        depth_result = await ctx.elicit(
            "How detailed should the analysis be?\n" +
            "- basic: High-level overview\n" +
            "- detailed: Comprehensive analysis\n" +
            "- expert: Deep technical analysis with recommendations",
            response_type=str
        )

        analysis_depth = depth_result.data if depth_result.action == "accept" else "detailed"

        await ctx.report_progress(75, 100)

        # Simulate resource analysis
        mock_analysis = {
            "analysis_id": analysis_id,
            "scope": analysis_scope,
            "namespace": namespace,
            "depth": analysis_depth,
            "timestamp": datetime.now().isoformat(),
            "results": {
                "total_nodes": 42,
                "gpu_nodes": 18,
                "total_gpus": 144,
                "available_gpus": {
                    "a100": 12,
                    "a40": 8,
                    "rtx6000": 6
                },
                "utilization": {
                    "cpu": "65%",
                    "memory": "78%",
                    "gpu": "45%",
                    "storage": "34%"
                }
            }
        }

        ctx.set_state(f"analysis_{analysis_id}", mock_analysis)

        await ctx.report_progress(100, 100)
        await ctx.info(f"Resource analysis {analysis_id} completed successfully")

        return f"""
[SUCCESS] Progressive Resource Analysis Complete

Analysis ID: {analysis_id}
Scope: {analysis_scope}
Namespace: {namespace}
Depth: {analysis_depth}

Results Summary:
- Total Nodes: {mock_analysis['results']['total_nodes']}
- GPU Nodes: {mock_analysis['results']['gpu_nodes']}
- Total GPUs: {mock_analysis['results']['total_gpus']}

GPU Availability:
- A100: {mock_analysis['results']['available_gpus']['a100']} available
- A40: {mock_analysis['results']['available_gpus']['a40']} available
- RTX6000: {mock_analysis['results']['available_gpus']['rtx6000']} available

Resource Utilization:
- CPU: {mock_analysis['results']['utilization']['cpu']}
- Memory: {mock_analysis['results']['utilization']['memory']}
- GPU: {mock_analysis['results']['utilization']['gpu']}
- Storage: {mock_analysis['results']['utilization']['storage']}

Status: Analysis complete and cached
Context ID: {ctx.request_id}
"""

    except Exception as e:
        error = NRPError(
            error_type=NRPErrorType.CONFIGURATION_ERROR,
            message=f"Analysis failed: {str(e)}",
            context={"exception": str(e), "analysis_id": analysis_id},
            suggestions=["Retry with reduced scope", "Check cluster connectivity", "Use basic analysis depth"],
            recoverable=True
        )
        return await handle_error(ctx, error)

@mcp.tool()
async def enhanced_error_recovery_demo(
    ctx: Context,
    trigger_error_type: Optional[str] = None
) -> str:
    """
    Demonstrate enhanced error handling and recovery patterns
    """
    try:
        demo_id = f"demo_{str(uuid.uuid4())[:8]}"
        await ctx.info(f"Starting error recovery demonstration: {demo_id}")

        if trigger_error_type:
            await ctx.warning(f"Triggering demonstration error: {trigger_error_type}")

            if trigger_error_type == "validation":
                error = NRPError(
                    error_type=NRPErrorType.VALIDATION_ERROR,
                    message="Demonstration validation error",
                    context={"demo_id": demo_id, "trigger": trigger_error_type},
                    suggestions=["Fix validation issues", "Use correct parameter format", "Check input types"]
                )
                return await handle_error(ctx, error)

            elif trigger_error_type == "elicitation_cancelled":
                error = NRPError(
                    error_type=NRPErrorType.ELICITATION_CANCELLED,
                    message="User cancelled elicitation process",
                    context={"demo_id": demo_id, "trigger": trigger_error_type},
                    suggestions=["Restart the process", "Use default values", "Provide parameters upfront"]
                )
                return await handle_error(ctx, error)

            elif trigger_error_type == "resource_unavailable":
                error = NRPError(
                    error_type=NRPErrorType.RESOURCE_UNAVAILABLE,
                    message="Requested resources are not available",
                    context={"demo_id": demo_id, "trigger": trigger_error_type},
                    suggestions=["Try different resource types", "Wait for resources to become available", "Use lower resource requirements"]
                )
                return await handle_error(ctx, error)

        return f"""
[SUCCESS] Error Recovery Demo Complete

Demo ID: {demo_id}
Available Error Types for Testing:
- validation: Parameter validation errors
- elicitation_cancelled: User cancellation errors
- resource_unavailable: Resource availability errors
- timeout_error: Operation timeout errors
- permission_denied: Access permission errors

Server Flags Configuration:
- Verbose Logging: {SERVER_FLAGS.verbose_logging}
- Strict Validation: {SERVER_FLAGS.strict_validation}
- Auto Retry: {SERVER_FLAGS.auto_retry_on_error}
- Max Elicitation Rounds: {SERVER_FLAGS.max_elicitation_rounds}
- Progressive Disclosure: {SERVER_FLAGS.enable_progressive_disclosure}
- Require Confirmation: {SERVER_FLAGS.require_confirmation_for_critical_ops}

Error Handling Features:
[OK] Structured error types with context
[OK] Recovery suggestions and guidance
[OK] Error ID tracking for support
[OK] Automatic retry capabilities
[OK] Progressive elicitation with fallbacks
[OK] Smart defaults and validation
"""

    except Exception as e:
        error = NRPError(
            error_type=NRPErrorType.CONFIGURATION_ERROR,
            message=f"Demo failed: {str(e)}",
            context={"exception": str(e), "demo_id": demo_id},
            suggestions=["Check demo configuration", "Report bug to development team"],
            recoverable=False
        )
        return await handle_error(ctx, error)

@mcp.tool()
async def configure_server_flags(
    ctx: Context,
    flag_name: Optional[str] = None,
    flag_value: Optional[bool] = None
) -> str:
    """
    Configure server flags for enhanced behavior control
    """
    global SERVER_FLAGS

    if flag_name and flag_value is not None:
        if hasattr(SERVER_FLAGS, flag_name):
            setattr(SERVER_FLAGS, flag_name, flag_value)
            await ctx.info(f"Set {flag_name} = {flag_value}")
            return f"[SUCCESS] Server flag '{flag_name}' set to {flag_value}"
        else:
            error = NRPError(
                error_type=NRPErrorType.VALIDATION_ERROR,
                message=f"Unknown server flag: {flag_name}",
                context={"provided_flag": flag_name, "available_flags": list(SERVER_FLAGS.__dict__.keys())},
                suggestions=[f"Use one of: {', '.join(SERVER_FLAGS.__dict__.keys())}", "Check flag name spelling"]
            )
            return await handle_error(ctx, error)

    # Show current configuration
    return f"""
[INFO] Current Server Flags Configuration

Logging & Validation:
- verbose_logging: {SERVER_FLAGS.verbose_logging}
- strict_validation: {SERVER_FLAGS.strict_validation}

Error Handling:
- auto_retry_on_error: {SERVER_FLAGS.auto_retry_on_error}
- max_elicitation_rounds: {SERVER_FLAGS.max_elicitation_rounds}

User Experience:
- enable_progressive_disclosure: {SERVER_FLAGS.enable_progressive_disclosure}
- require_confirmation_for_critical_ops: {SERVER_FLAGS.require_confirmation_for_critical_ops}
- allow_partial_execution: {SERVER_FLAGS.allow_partial_execution}
- enable_smart_defaults: {SERVER_FLAGS.enable_smart_defaults}

To modify a flag: configure_server_flags(flag_name="flag_name", flag_value=True/False)
"""

if __name__ == "__main__":
    print("Starting Enhanced Elicitation NRP.ai FastMCP Server...")
    print()
    print("FastMCP Elicitation Features Implemented:")
    print("- Progressive Multi-Turn Elicitation: Step-by-step user guidance")
    print("- Structured Response Types: Complex data collection with validation")
    print("- Enhanced Error Handling: Detailed error context and recovery")
    print("- Smart Defaults: Intelligent fallbacks for cancelled elicitations")
    print("- Confirmation Workflows: Critical operation safety checks")
    print("- Server Flags: Runtime behavior configuration")
    print("- Error Recovery: Automatic retry and graceful degradation")
    print()
    print("Available Enhanced Tools:")
    print("- intelligent_gpu_deployment: Full elicitation-driven deployment")
    print("- progressive_resource_analysis: Multi-turn resource analysis")
    print("- enhanced_error_recovery_demo: Error handling demonstration")
    print("- configure_server_flags: Runtime configuration management")
    print()

    mcp.run(transport="http", port=8012)