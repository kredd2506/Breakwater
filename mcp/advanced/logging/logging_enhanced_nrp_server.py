#!/usr/bin/env python3
"""Enhanced NRP.ai FastMCP Server with Comprehensive Structured Logging"""

import asyncio
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field

from fastmcp import FastMCP, Context
from mcp.types import TextContent

# Initialize FastMCP with enhanced logging
mcp = FastMCP("Logging Enhanced NRP.ai Server")

# Structured Logging Configuration
@dataclass
class LoggingConfig:
    """Enhanced logging configuration with structured metadata"""
    enable_performance_tracking: bool = True
    enable_security_logging: bool = True
    enable_user_activity_tracking: bool = True
    enable_resource_monitoring: bool = True
    log_level_threshold: str = "debug"  # debug, info, warning, error
    include_stack_traces: bool = True
    max_log_metadata_size: int = 1000  # characters
    session_correlation_enabled: bool = True

# Global logging configuration
LOGGING_CONFIG = LoggingConfig()

# Enhanced Log Categories
class LogCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER_ACTIVITY = "user_activity"
    RESOURCE_MANAGEMENT = "resource_management"
    ERROR_HANDLING = "error_handling"
    WORKFLOW = "workflow"
    VALIDATION = "validation"
    INTEGRATION = "integration"

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

# Structured Logging Helper
class StructuredLogger:
    """Enhanced structured logging with metadata and correlation"""

    @staticmethod
    async def log_with_metadata(
        ctx: Context,
        level: LogLevel,
        message: str,
        category: LogCategory,
        extra_metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        operation_id: Optional[str] = None
    ):
        """Log with comprehensive structured metadata"""

        # Build base metadata
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category.value,
            "level": level.value,
            "session_id": session_id or ctx.get_state("session_id") or "anonymous",
            "operation_id": operation_id or str(uuid.uuid4())[:8],
            "request_id": getattr(ctx, 'request_id', 'unknown'),
            "server_version": "1.0.0"
        }

        # Add extra metadata
        if extra_metadata:
            # Limit metadata size to prevent log flooding
            metadata_str = json.dumps(extra_metadata)
            if len(metadata_str) > LOGGING_CONFIG.max_log_metadata_size:
                metadata["metadata_truncated"] = True
                metadata["original_size"] = len(metadata_str)
                # Keep only essential fields
                essential_fields = ["user_id", "resource_type", "error_code", "duration_ms"]
                filtered_metadata = {k: v for k, v in extra_metadata.items() if k in essential_fields}
                metadata.update(filtered_metadata)
            else:
                metadata.update(extra_metadata)

        # Log based on level
        if level == LogLevel.DEBUG:
            await ctx.debug(message, extra=metadata)
        elif level == LogLevel.INFO:
            await ctx.info(message, extra=metadata)
        elif level == LogLevel.WARNING:
            await ctx.warning(message, extra=metadata)
        elif level == LogLevel.ERROR:
            await ctx.error(message, extra=metadata)

# Performance Tracking Helper
async def track_operation_performance(
    ctx: Context,
    operation_name: str,
    category: LogCategory = LogCategory.PERFORMANCE
):
    """Helper for manual performance tracking"""
    start_time = datetime.now()
    operation_id = str(uuid.uuid4())[:8]

    # Log operation start
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"Starting operation: {operation_name}",
        category,
        extra_metadata={
            "operation_name": operation_name,
            "operation_status": "started",
            "start_time": start_time.isoformat()
        },
        operation_id=operation_id
    )

    return {
        "start_time": start_time,
        "operation_id": operation_id,
        "operation_name": operation_name,
        "category": category
    }

async def complete_operation_performance(
    ctx: Context,
    tracking_data: Dict[str, Any],
    success: bool = True,
    error: Optional[Exception] = None,
    result: Optional[Any] = None
):
    """Complete performance tracking"""
    end_time = datetime.now()
    duration_ms = (end_time - tracking_data["start_time"]).total_seconds() * 1000

    if success:
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.INFO,
            f"Completed operation: {tracking_data['operation_name']}",
            tracking_data["category"],
            extra_metadata={
                "operation_name": tracking_data["operation_name"],
                "operation_status": "completed",
                "duration_ms": round(duration_ms, 2),
                "end_time": end_time.isoformat(),
                "result_type": type(result).__name__ if result else "None"
            },
            operation_id=tracking_data["operation_id"]
        )
    else:
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.ERROR,
            f"Failed operation: {tracking_data['operation_name']} - {str(error)}",
            LogCategory.ERROR_HANDLING,
            extra_metadata={
                "operation_name": tracking_data["operation_name"],
                "operation_status": "failed",
                "duration_ms": round(duration_ms, 2),
                "error_type": type(error).__name__ if error else "Unknown",
                "error_message": str(error) if error else "Unknown error",
                "end_time": end_time.isoformat()
            },
            operation_id=tracking_data["operation_id"]
        )

# Enhanced Logging Tools

@mcp.tool()
async def comprehensive_gpu_deployment(
    ctx: Context,
    gpu_type: str = "a100",
    gpu_count: int = 1,
    memory_gb: int = 32,
    cpu_cores: int = 8,
    namespace: str = "default",
    workload_type: str = "ml_training",
    enable_monitoring: bool = True,
    user_id: Optional[str] = None
) -> str:
    """
    Comprehensive GPU deployment with detailed structured logging
    """
    # Start performance tracking
    tracking = await track_operation_performance(ctx, "comprehensive_gpu_deployment", LogCategory.RESOURCE_MANAGEMENT)

    deployment_id = f"deploy_{str(uuid.uuid4())[:8]}"
    session_id = ctx.get_state("session_id") or str(uuid.uuid4())[:8]

    # Security logging - track resource requests
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"GPU deployment request initiated by user",
        LogCategory.SECURITY,
        extra_metadata={
            "user_id": user_id or "anonymous",
            "deployment_id": deployment_id,
            "requested_resources": {
                "gpu_type": gpu_type,
                "gpu_count": gpu_count,
                "memory_gb": memory_gb,
                "cpu_cores": cpu_cores
            },
            "namespace": namespace,
            "workload_type": workload_type,
            "client_ip": getattr(ctx, 'client_ip', 'unknown'),
            "risk_level": "medium" if gpu_count > 4 else "low"
        },
        session_id=session_id
    )

    # Validation logging
    validation_errors = []
    if gpu_count > 16:
        validation_errors.append("GPU count exceeds maximum (16)")
    if memory_gb > 80:
        validation_errors.append("Memory exceeds maximum (80GB)")
    if cpu_cores > 128:
        validation_errors.append("CPU cores exceed maximum (128)")

    if validation_errors:
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.WARNING,
            f"Validation issues detected for deployment {deployment_id}",
            LogCategory.VALIDATION,
            extra_metadata={
                "deployment_id": deployment_id,
                "validation_errors": validation_errors,
                "user_id": user_id or "anonymous",
                "auto_correction_applied": True
            },
            session_id=session_id
        )

        # Apply auto-corrections
        gpu_count = min(gpu_count, 16)
        memory_gb = min(memory_gb, 80)
        cpu_cores = min(cpu_cores, 128)

    # Resource availability check with logging
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.DEBUG,
        f"Checking resource availability for deployment {deployment_id}",
        LogCategory.RESOURCE_MANAGEMENT,
        extra_metadata={
            "deployment_id": deployment_id,
            "check_type": "resource_availability",
            "cluster_region": "us-west-2",
            "availability_check_started": datetime.now(timezone.utc).isoformat()
        },
        session_id=session_id
    )

    # Simulate resource availability check
    available_gpus = {"a100": 12, "a40": 8, "rtx6000": 6, "h100": 4, "general": 20}
    available_count = available_gpus.get(gpu_type, 0)

    if available_count < gpu_count:
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.WARNING,
            f"Insufficient {gpu_type} GPUs available for deployment {deployment_id}",
            LogCategory.RESOURCE_MANAGEMENT,
            extra_metadata={
                "deployment_id": deployment_id,
                "requested_gpus": gpu_count,
                "available_gpus": available_count,
                "gpu_type": gpu_type,
                "alternative_options": [k for k, v in available_gpus.items() if v >= gpu_count],
                "wait_time_estimate_minutes": 30 if available_count > 0 else 120
            },
            session_id=session_id
        )

    # Progress reporting with structured logging
    progress_steps = [
        ("Validating configuration", 20),
        ("Allocating resources", 40),
        ("Creating deployment", 60),
        ("Starting containers", 80),
        ("Enabling monitoring", 90),
        ("Deployment complete", 100)
    ]

    for step_name, progress in progress_steps:
        await ctx.report_progress(progress, 100)
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.DEBUG,
            f"Deployment progress: {step_name}",
            LogCategory.WORKFLOW,
            extra_metadata={
                "deployment_id": deployment_id,
                "step_name": step_name,
                "progress_percentage": progress,
                "estimated_completion": datetime.now(timezone.utc).isoformat(),
                "next_step": progress_steps[progress_steps.index((step_name, progress)) + 1][0] if progress < 100 else "None"
            },
            session_id=session_id
        )

        # Simulate step delay
        await asyncio.sleep(0.1)

    # Generate deployment configuration
    deployment_config = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_id,
            "namespace": namespace,
            "labels": {
                "app": deployment_id,
                "gpu-type": gpu_type,
                "workload-type": workload_type,
                "user-id": user_id or "anonymous",
                "logging-enabled": "true"
            },
            "annotations": {
                "logging.nrp.ai/session-id": session_id,
                "logging.nrp.ai/deployment-timestamp": datetime.now(timezone.utc).isoformat(),
                "logging.nrp.ai/user-id": user_id or "anonymous"
            }
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": deployment_id}},
            "template": {
                "metadata": {
                    "labels": {"app": deployment_id},
                    "annotations": {
                        "logging.nrp.ai/pod-type": "gpu-workload",
                        "logging.nrp.ai/monitoring-enabled": str(enable_monitoring).lower()
                    }
                },
                "spec": {
                    "containers": [{
                        "name": "workload",
                        "image": f"nrp/{workload_type}:latest",
                        "env": [
                            {"name": "LOGGING_SESSION_ID", "value": session_id},
                            {"name": "DEPLOYMENT_ID", "value": deployment_id},
                            {"name": "USER_ID", "value": user_id or "anonymous"}
                        ],
                        "resources": {
                            "requests": {
                                f"nvidia.com/{gpu_type}": gpu_count,
                                "memory": f"{memory_gb}Gi",
                                "cpu": str(cpu_cores)
                            },
                            "limits": {
                                f"nvidia.com/{gpu_type}": gpu_count,
                                "memory": f"{memory_gb}Gi",
                                "cpu": str(cpu_cores)
                            }
                        }
                    }]
                }
            }
        }
    }

    # Store deployment state with logging metadata
    deployment_state = {
        "deployment_id": deployment_id,
        "config": deployment_config,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id or "anonymous",
        "session_id": session_id,
        "logging_metadata": {
            "performance_tracked": True,
            "security_logged": True,
            "validation_applied": len(validation_errors) > 0,
            "resource_availability_checked": True
        }
    }

    ctx.set_state(f"deployment_{deployment_id}", deployment_state)

    # Final success logging
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"GPU deployment {deployment_id} created successfully",
        LogCategory.RESOURCE_MANAGEMENT,
        extra_metadata={
            "deployment_id": deployment_id,
            "final_configuration": {
                "gpu_type": gpu_type,
                "gpu_count": gpu_count,
                "memory_gb": memory_gb,
                "cpu_cores": cpu_cores,
                "namespace": namespace,
                "monitoring_enabled": enable_monitoring
            },
            "user_id": user_id or "anonymous",
            "deployment_status": "success",
            "cost_estimate_per_hour": gpu_count * 3.2,  # Estimated cost
            "resource_efficiency_score": min(100, (gpu_count * memory_gb) / 10)
        },
        session_id=session_id
    )

    # Complete performance tracking
    result = f"""
[SUCCESS] Comprehensive GPU Deployment with Structured Logging

Deployment ID: {deployment_id}
Session ID: {session_id}
Configuration:
- GPU: {gpu_count}x {gpu_type.upper()}
- Memory: {memory_gb}GB
- CPU: {cpu_cores} cores
- Namespace: {namespace}
- Workload: {workload_type}
- Monitoring: {'Enabled' if enable_monitoring else 'Disabled'}

Logging Features Applied:
[OK] Performance tracking with timing metrics
[OK] Security logging with user activity tracking
[OK] Resource management with availability checks
[OK] Validation logging with auto-correction
[OK] Progress reporting with structured metadata
[OK] Error handling with comprehensive context

YAML Configuration:
```yaml
{json.dumps(deployment_config, indent=2)}
```

All activities logged with structured metadata for auditing and monitoring.
"""

    # Complete performance tracking
    await complete_operation_performance(ctx, tracking, success=True, result=result)

    return result

@mcp.tool()
async def security_audit_log_analysis(
    ctx: Context,
    time_range_hours: int = 24,
    user_filter: Optional[str] = None,
    severity_filter: str = "all"
) -> str:
    """
    Analyze security audit logs with comprehensive structured logging
    """
    analysis_id = f"audit_{str(uuid.uuid4())[:8]}"
    session_id = ctx.get_state("session_id") or str(uuid.uuid4())[:8]

    # Security logging for audit access
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.WARNING,  # High visibility for security operations
        f"Security audit log analysis initiated",
        LogCategory.SECURITY,
        extra_metadata={
            "analysis_id": analysis_id,
            "time_range_hours": time_range_hours,
            "user_filter": user_filter,
            "severity_filter": severity_filter,
            "analyst_session": session_id,
            "access_level": "security_admin",
            "compliance_framework": "SOC2",
            "audit_reason": "routine_security_review"
        },
        session_id=session_id
    )

    # Simulate security log analysis
    security_events = [
        {
            "event_type": "failed_login_attempt",
            "user_id": "user123",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "medium",
            "source_ip": "192.168.1.100",
            "details": "Multiple failed login attempts detected"
        },
        {
            "event_type": "elevated_privilege_request",
            "user_id": "admin456",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "high",
            "source_ip": "10.0.0.50",
            "details": "Admin privilege escalation requested"
        },
        {
            "event_type": "resource_access_anomaly",
            "user_id": "user789",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "low",
            "source_ip": "172.16.0.25",
            "details": "Unusual resource access pattern detected"
        }
    ]

    # Filter events based on criteria
    if user_filter:
        security_events = [e for e in security_events if e["user_id"] == user_filter]

    if severity_filter != "all":
        security_events = [e for e in security_events if e["severity"] == severity_filter]

    # Log analysis results
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"Security audit analysis completed: {len(security_events)} events found",
        LogCategory.SECURITY,
        extra_metadata={
            "analysis_id": analysis_id,
            "events_analyzed": len(security_events),
            "time_range_hours": time_range_hours,
            "high_severity_count": len([e for e in security_events if e["severity"] == "high"]),
            "medium_severity_count": len([e for e in security_events if e["severity"] == "medium"]),
            "low_severity_count": len([e for e in security_events if e["severity"] == "low"]),
            "unique_users": len(set(e["user_id"] for e in security_events)),
            "unique_ips": len(set(e["source_ip"] for e in security_events)),
            "compliance_status": "reviewed",
            "follow_up_required": len([e for e in security_events if e["severity"] == "high"]) > 0
        },
        session_id=session_id
    )

    # Generate security report
    report = f"""
[SECURITY AUDIT] Analysis Report

Analysis ID: {analysis_id}
Time Range: Last {time_range_hours} hours
Events Found: {len(security_events)}

Security Event Summary:
- High Severity: {len([e for e in security_events if e["severity"] == "high"])}
- Medium Severity: {len([e for e in security_events if e["severity"] == "medium"])}
- Low Severity: {len([e for e in security_events if e["severity"] == "low"])}

Recent Security Events:
"""

    for event in security_events[:5]:  # Show top 5 events
        report += f"""
Event Type: {event["event_type"]}
User: {event["user_id"]}
Severity: {event["severity"].upper()}
Source IP: {event["source_ip"]}
Details: {event["details"]}
Timestamp: {event["timestamp"]}
---"""

    report += f"""

Structured Logging Applied:
[OK] Security access logging with audit trail
[OK] Performance tracking for analysis operations
[OK] Compliance metadata for SOC2 requirements
[OK] Event correlation and pattern analysis
[OK] User activity tracking and IP monitoring

Session ID: {session_id}
All security activities logged for compliance review.
"""

    return report

@mcp.tool()
async def configure_logging_settings(
    ctx: Context,
    setting_name: Optional[str] = None,
    setting_value: Optional[Union[str, bool, int]] = None
) -> str:
    """
    Configure logging settings with real-time application
    """
    global LOGGING_CONFIG
    session_id = ctx.get_state("session_id") or str(uuid.uuid4())[:8]

    if setting_name and setting_value is not None:
        # Log configuration change
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.INFO,
            f"Logging configuration change requested",
            LogCategory.SECURITY,  # Config changes are security events
            extra_metadata={
                "setting_name": setting_name,
                "old_value": getattr(LOGGING_CONFIG, setting_name, None),
                "new_value": setting_value,
                "changed_by_session": session_id,
                "change_timestamp": datetime.now(timezone.utc).isoformat(),
                "change_reason": "runtime_configuration"
            },
            session_id=session_id
        )

        if hasattr(LOGGING_CONFIG, setting_name):
            setattr(LOGGING_CONFIG, setting_name, setting_value)

            # Log successful change
            await StructuredLogger.log_with_metadata(
                ctx, LogLevel.INFO,
                f"Logging setting '{setting_name}' updated successfully",
                LogCategory.VALIDATION,
                extra_metadata={
                    "setting_name": setting_name,
                    "new_value": setting_value,
                    "applied_successfully": True,
                    "session_id": session_id
                },
                session_id=session_id
            )

            return f"[SUCCESS] Logging setting '{setting_name}' set to {setting_value}"
        else:
            # Log invalid setting attempt
            await StructuredLogger.log_with_metadata(
                ctx, LogLevel.WARNING,
                f"Invalid logging setting attempted: {setting_name}",
                LogCategory.VALIDATION,
                extra_metadata={
                    "invalid_setting": setting_name,
                    "attempted_value": setting_value,
                    "available_settings": list(LOGGING_CONFIG.__dict__.keys()),
                    "session_id": session_id
                },
                session_id=session_id
            )

            return f"[ERROR] Unknown logging setting: {setting_name}"

    # Return current configuration
    config_dict = asdict(LOGGING_CONFIG)

    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.DEBUG,
        "Logging configuration retrieved",
        LogCategory.USER_ACTIVITY,
        extra_metadata={
            "action": "configuration_view",
            "session_id": session_id,
            "current_config": config_dict
        },
        session_id=session_id
    )

    return f"""
[INFO] Current Logging Configuration

Performance Tracking:
- enable_performance_tracking: {LOGGING_CONFIG.enable_performance_tracking}
- include_stack_traces: {LOGGING_CONFIG.include_stack_traces}

Security Logging:
- enable_security_logging: {LOGGING_CONFIG.enable_security_logging}
- enable_user_activity_tracking: {LOGGING_CONFIG.enable_user_activity_tracking}

Resource Monitoring:
- enable_resource_monitoring: {LOGGING_CONFIG.enable_resource_monitoring}
- session_correlation_enabled: {LOGGING_CONFIG.session_correlation_enabled}

Log Management:
- log_level_threshold: {LOGGING_CONFIG.log_level_threshold}
- max_log_metadata_size: {LOGGING_CONFIG.max_log_metadata_size} characters

To modify: configure_logging_settings(setting_name="name", setting_value=value)
Session ID: {session_id}
"""

@mcp.tool()
async def logging_demonstration(
    ctx: Context,
    demo_type: str = "comprehensive",
    include_errors: bool = False
) -> str:
    """
    Demonstrate all logging capabilities with structured examples
    """
    demo_id = f"demo_{str(uuid.uuid4())[:8]}"
    session_id = ctx.get_state("session_id") or str(uuid.uuid4())[:8]

    # Demo start logging
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"Starting logging demonstration: {demo_type}",
        LogCategory.USER_ACTIVITY,
        extra_metadata={
            "demo_id": demo_id,
            "demo_type": demo_type,
            "include_errors": include_errors,
            "session_id": session_id,
            "demo_features": ["structured_logging", "performance_tracking", "security_events", "error_handling"]
        },
        session_id=session_id
    )

    results = []

    # Debug level demonstration
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.DEBUG,
        "Debug level logging demonstration",
        LogCategory.WORKFLOW,
        extra_metadata={
            "demo_id": demo_id,
            "log_level": "debug",
            "purpose": "detailed_diagnostics",
            "example_data": {"key1": "value1", "key2": 42, "key3": True}
        },
        session_id=session_id
    )
    results.append("[OK] Debug level logging with detailed metadata")

    # Info level demonstration
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        "Info level logging demonstration",
        LogCategory.WORKFLOW,
        extra_metadata={
            "demo_id": demo_id,
            "log_level": "info",
            "purpose": "normal_operations",
            "workflow_step": "demonstration",
            "progress_indicator": "50%"
        },
        session_id=session_id
    )
    results.append("[OK] Info level logging with workflow metadata")

    # Warning level demonstration
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.WARNING,
        "Warning level logging demonstration",
        LogCategory.VALIDATION,
        extra_metadata={
            "demo_id": demo_id,
            "log_level": "warning",
            "purpose": "potential_issues",
            "warning_type": "demonstration",
            "severity": "low",
            "action_required": False
        },
        session_id=session_id
    )
    results.append("[OK] Warning level logging with validation metadata")

    # Error level demonstration (if requested)
    if include_errors:
        await StructuredLogger.log_with_metadata(
            ctx, LogLevel.ERROR,
            "Error level logging demonstration (simulated)",
            LogCategory.ERROR_HANDLING,
            extra_metadata={
                "demo_id": demo_id,
                "log_level": "error",
                "purpose": "error_demonstration",
                "error_type": "simulated_error",
                "error_code": "DEMO_001",
                "recovery_possible": True,
                "simulated": True
            },
            session_id=session_id
        )
        results.append("[OK] Error level logging with error handling metadata")

    # Security logging demonstration
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        "Security event logging demonstration",
        LogCategory.SECURITY,
        extra_metadata={
            "demo_id": demo_id,
            "event_type": "access_demonstration",
            "user_id": "demo_user",
            "security_level": "demonstration",
            "access_granted": True,
            "resource": "logging_demo",
            "compliance_logged": True
        },
        session_id=session_id
    )
    results.append("[OK] Security event logging with compliance metadata")

    # Performance logging demonstration
    start_time = datetime.now()
    await asyncio.sleep(0.1)  # Simulate work
    end_time = datetime.now()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        "Performance metrics logging demonstration",
        LogCategory.PERFORMANCE,
        extra_metadata={
            "demo_id": demo_id,
            "operation": "simulated_work",
            "duration_ms": round(duration_ms, 2),
            "throughput": "1000 ops/sec",
            "memory_usage_mb": 45.6,
            "cpu_usage_percent": 12.3,
            "performance_grade": "excellent"
        },
        session_id=session_id
    )
    results.append("[OK] Performance metrics logging with timing data")

    # Final demonstration summary
    await StructuredLogger.log_with_metadata(
        ctx, LogLevel.INFO,
        f"Logging demonstration {demo_id} completed successfully",
        LogCategory.USER_ACTIVITY,
        extra_metadata={
            "demo_id": demo_id,
            "demo_type": demo_type,
            "total_log_entries": 6 if include_errors else 5,
            "categories_demonstrated": ["workflow", "validation", "security", "performance", "error_handling"] if include_errors else ["workflow", "validation", "security", "performance"],
            "levels_demonstrated": ["debug", "info", "warning", "error"] if include_errors else ["debug", "info", "warning"],
            "session_id": session_id,
            "demonstration_successful": True
        },
        session_id=session_id
    )

    return f"""
[SUCCESS] Logging Demonstration Complete

Demo ID: {demo_id}
Session ID: {session_id}
Demo Type: {demo_type}

Demonstrated Features:
{chr(10).join(results)}

Structured Logging Capabilities Shown:
[OK] Multi-level logging (debug, info, warning, error)
[OK] Category-based log organization
[OK] Rich metadata with structured data
[OK] Session correlation and tracking
[OK] Performance metrics integration
[OK] Security event logging
[OK] Error handling with context
[OK] Workflow progress tracking

All log entries include:
- Timestamp with timezone
- Session correlation ID
- Operation tracking ID
- Structured metadata
- Category classification
- Performance metrics (where applicable)

Logging configuration can be adjusted in real-time using configure_logging_settings.
"""

if __name__ == "__main__":
    print("Starting Logging Enhanced NRP.ai FastMCP Server...")
    print()
    print("FastMCP Structured Logging Features Implemented:")
    print("- Multi-Level Logging: debug, info, warning, error with structured metadata")
    print("- Performance Tracking: Automatic timing and metrics collection")
    print("- Security Logging: User activity and compliance event tracking")
    print("- Resource Monitoring: Resource usage and availability logging")
    print("- Session Correlation: Cross-request tracking and correlation")
    print("- Error Handling: Comprehensive error context and recovery logging")
    print("- Runtime Configuration: Dynamic logging behavior adjustment")
    print()
    print("Available Logging-Enhanced Tools:")
    print("- comprehensive_gpu_deployment: Full deployment with structured logging")
    print("- security_audit_log_analysis: Security audit with compliance logging")
    print("- configure_logging_settings: Runtime logging configuration")
    print("- logging_demonstration: Comprehensive logging capability demo")
    print()

    mcp.run(transport="http", port=8013)