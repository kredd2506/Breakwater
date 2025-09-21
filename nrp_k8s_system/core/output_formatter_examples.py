"""
NRP Output Formatter Usage Examples

Demonstrates how to use the modular output formatter in various scenarios.
This serves as both documentation and integration guide.
"""

from .output_formatter import (
    OutputFormatter, Stage, Route, ConfidenceLevel, RiskLevel,
    Warning, AnalysisSummary, Resource
)
from .format_config import format_config


def example_policy_education():
    """Example: Stage 1 - Policy Education Output"""

    # Create analysis summary
    analysis = AnalysisSummary(
        route=Route.YAML_GENERATION,
        intent_confidence=ConfidenceLevel.HIGH,
        specialists_consulted=["Security", "Policy", "Documentation"],
        risk_assessment=RiskLevel.MEDIUM
    )

    # Create related resources
    resources = [
        Resource(
            title="Kubernetes Pod Documentation",
            explanation="Essential for understanding pod configuration",
            url="https://kubernetes.io/docs/concepts/workloads/pods/"
        ),
        Resource(
            title="NRP Security Best Practices",
            explanation="Required reading for compliance"
        )
    ]

    # Generate formatted output
    output = OutputFormatter.format_policy_education(
        resource_type="Pod",
        policy_requirements=[
            "All pods must include resource limits for CPU and memory",
            "Security context must be non-root with specific UID/GID",
            "Network policies must restrict inter-pod communication"
        ],
        critical_restrictions=[
            "Host networking is strictly prohibited in production",
            "Privileged containers are not allowed without security approval",
            "External volume mounts require explicit policy exception"
        ],
        compliance_essentials={
            "required_labels": {
                "nrp.ai/project": "my-project",
                "nrp.ai/environment": "dev"
            },
            "resource_limits": {
                "cpu": "2",
                "memory": "4Gi",
                "storage": "10Gi"
            },
            "network_policies": "Default deny-all with explicit allow rules for required services"
        },
        analysis=analysis,
        resources=resources,
        understanding_check=[
            "Resource limits prevent cluster resource exhaustion",
            "Security contexts protect against privilege escalation",
            "Network policies implement zero-trust networking"
        ]
    )

    return output


def example_yaml_generation():
    """Example: Stage 2 - YAML Generation Output"""

    warnings = [
        Warning(
            level="IMPORTANT",
            message="Generated image tag uses 'latest' which is not recommended for production",
            impact="Deployments may be unpredictable",
            recommendation="Specify explicit version tags"
        )
    ]

    analysis = AnalysisSummary(
        route=Route.YAML_GENERATION,
        intent_confidence=ConfidenceLevel.HIGH,
        specialists_consulted=["Template", "Policy", "Security", "Validation"],
        compliance_score=92
    )

    resources = [
        Resource(
            title="Pod Production Guide",
            explanation="Best practices for production deployments"
        )
    ]

    yaml_content = """# NRP-Compliant Pod Configuration
# Auto-generated with policy enforcement
# Warnings: Using latest tag - consider explicit versioning

apiVersion: v1
kind: Pod
metadata:
  name: my-app
  labels:
    nrp.ai/project: "my-project"      # Required by NRP Policy
    nrp.ai/environment: "dev"         # Required by NRP Policy
  annotations:
    nrp.ai/compliance-verified: "true"
spec:
  containers:
  - name: app
    image: nginx:latest
    resources:
      limits:
        cpu: "2"
        memory: "4Gi"
      requests:
        cpu: "1"
        memory: "2Gi"
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000"""

    output = OutputFormatter.format_yaml_generation(
        yaml_content=yaml_content,
        template_used="Standard Pod Template v2.1",
        warnings=warnings,
        analysis=analysis,
        resources=resources,
        review_points=[
            "Verify the resource specifications meet your needs",
            "Confirm the NRP policy compliance annotations",
            "Check the security context settings"
        ]
    )

    return output


def example_knowledge_query():
    """Example: Knowledge Query Response"""

    analysis = AnalysisSummary(
        route=Route.KNOWLEDGE_QUERY,
        intent_confidence=ConfidenceLevel.HIGH,
        specialists_consulted=["Documentation", "Policy"]
    )

    resources = [
        Resource(
            title="NRP GPU Request Documentation",
            explanation="Complete guide for requesting GPU resources",
            url="https://docs.nrp-nautilus.io/gpu-requests"
        )
    ]

    output = OutputFormatter.format_knowledge_response(
        answer="To request GPUs in NRP, you need to specify GPU resources in your pod specification using the 'nvidia.com/gpu' resource type. The cluster supports NVIDIA V100, RTX 2080Ti, and A100 GPUs with specific node selectors for each type.",
        key_policies=[
            "GPU requests require justification and project approval",
            "Maximum 4 GPUs per pod unless pre-approved for larger allocations",
            "GPU pods must include resource limits to prevent cluster exhaustion"
        ],
        practical_examples=[
            "```yaml\nresources:\n  limits:\n    nvidia.com/gpu: 1\n  requests:\n    nvidia.com/gpu: 1\n```"
        ],
        common_pitfalls=[
            "Forgetting to include GPU drivers in container image",
            "Not setting appropriate CPU/memory ratios for GPU workloads",
            "Using incorrect node selectors for specific GPU types"
        ],
        analysis=analysis,
        resources=resources
    )

    return output


def example_blocking_error():
    """Example: Blocking Error Response"""

    output = OutputFormatter.format_blocking_error(
        issue_description="Pod specification requests privileged access without security approval",
        policy_violated="NRP Security Policy Section 4.2: Privileged Container Restrictions",
        risk_level=RiskLevel.CRITICAL,
        required_actions=[
            "Remove 'privileged: true' from security context",
            "Submit security exception request if privileged access is required",
            "Implement alternative solution using specific capabilities instead"
        ]
    )

    return output


def example_custom_configuration():
    """Example: Customizing the output format"""

    # Enable colors
    format_config.enable_colors(True)

    # Customize symbols
    format_config.customize_symbol("critical_warning", "⛔")
    format_config.customize_symbol("next_steps", "📍")

    # Add a custom specialist
    format_config.add_specialist("Performance")

    # Save the configuration
    format_config.save_config()

    # Now generate output with custom formatting
    warnings = [
        Warning(level="CRITICAL", message="High severity security issue detected")
    ]

    output = OutputFormatter.format_warnings(warnings)
    return f"Custom formatted output:\n{output}"


def demo_all_formats():
    """Demonstrate all output formats"""

    print("=== NRP Output Formatter Demo ===\n")

    print("1. Policy Education Stage:")
    print(example_policy_education())
    print("\n" + "="*60 + "\n")

    print("2. YAML Generation Stage:")
    print(example_yaml_generation())
    print("\n" + "="*60 + "\n")

    print("3. Knowledge Query:")
    print(example_knowledge_query())
    print("\n" + "="*60 + "\n")

    print("4. Blocking Error:")
    print(example_blocking_error())
    print("\n" + "="*60 + "\n")

    print("5. Custom Configuration:")
    print(example_custom_configuration())


if __name__ == "__main__":
    demo_all_formats()