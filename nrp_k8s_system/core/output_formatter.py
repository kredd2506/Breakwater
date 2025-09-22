"""
NRP Kubernetes Agent Output Formatter

Implements the standardized output format specification for consistent,
safety-focused, and user-friendly responses across all system components.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .format_config import format_config


class Stage(Enum):
    """System workflow stages"""
    POLICY_EDUCATION = (1, "Policy Education & Safety Briefing")
    YAML_GENERATION = (2, "Compliant YAML Generation")
    KUBERNETES_EXECUTION = (3, "Kubernetes Deployment Execution")

    def __init__(self, number: int, name: str):
        self.number = number
        self.name = name


class Route(Enum):
    """Request routing types"""
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    YAML_GENERATION = "YAML_GENERATION"
    CRUD_OPERATION = "CRUD_OPERATION"
    HYBRID = "HYBRID"


class ConfidenceLevel(Enum):
    """Intent classification confidence"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "CRITICAL"


@dataclass
class Warning:
    """Represents a system warning"""
    level: str  # "CRITICAL" or "IMPORTANT"
    message: str
    impact: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class AnalysisSummary:
    """System analysis summary"""
    route: Route
    intent_confidence: ConfidenceLevel
    specialists_consulted: List[str]
    risk_assessment: Optional[RiskLevel] = None
    compliance_score: Optional[int] = None
    confidence_score: Optional[int] = None


@dataclass
class Resource:
    """Related resource link"""
    title: str
    explanation: str
    url: Optional[str] = None


class OutputFormatter:
    """Standardized output formatter for NRP Kubernetes Agent"""

    @staticmethod
    def format_header(stage: Optional[Stage] = None, total_stages: int = 3, custom_title: str = None) -> str:
        """Format standard response header"""
        if stage:
            title = f"[STAGE {stage.number}/{total_stages}] {stage.name}"
        elif custom_title:
            title = custom_title
        else:
            title = "NRP KUBERNETES AGENT RESPONSE"

        box_chars = format_config.get_box_chars()
        header_width = format_config.get_header_width()

        # Calculate padding for title
        title_padding = header_width - 2 - len(title)
        if title_padding < 0:
            title_padding = 0

        header = f"{box_chars['top_left']}{box_chars['horizontal']} NRP KUBERNETES AGENT RESPONSE "
        header += f"{box_chars['horizontal'] * (header_width - 32)}{box_chars['top_right']}\n"
        header += f"{box_chars['vertical']} {title:<{header_width-2}} {box_chars['vertical']}\n"
        header += f"{box_chars['bottom_left']}{box_chars['horizontal'] * (header_width-2)}{box_chars['bottom_right']}\n"
        return header

    @staticmethod
    def format_warnings(warnings: List[Warning]) -> str:
        """Format critical warnings and important notices"""
        if not warnings:
            return ""

        output = ""
        critical_warnings = [w for w in warnings if w.level == "CRITICAL"]
        important_notices = [w for w in warnings if w.level == "IMPORTANT"]

        critical_symbol = format_config.get_symbol("critical_warning")
        notice_symbol = format_config.get_symbol("important_notice")
        critical_color = format_config.get_color("critical")
        warning_color = format_config.get_color("warning")
        reset_color = format_config.get_color("reset")

        if critical_warnings:
            output += f"{critical_color}{critical_symbol} CRITICAL WARNINGS{reset_color}\n"
            for warning in critical_warnings:
                output += f"- {warning.message}\n"
                if warning.impact:
                    output += f"  Impact: {warning.impact}\n"
                if warning.recommendation:
                    output += f"  Action: {warning.recommendation}\n"
            output += "\n"

        if important_notices:
            output += f"{warning_color}{notice_symbol}  IMPORTANT NOTICES{reset_color}\n"
            for notice in important_notices:
                output += f"- {notice.message}\n"
                if notice.impact:
                    output += f"  Impact: {notice.impact}\n"
                if notice.recommendation:
                    output += f"  Recommendation: {notice.recommendation}\n"
            output += "\n"

        return output

    @staticmethod
    def format_analysis_summary(analysis: AnalysisSummary) -> str:
        """Format analysis summary section"""
        symbol = format_config.get_symbol("analysis_summary")
        info_color = format_config.get_color("info")
        reset_color = format_config.get_color("reset")

        output = f"{info_color}{symbol} ANALYSIS SUMMARY{reset_color}\n"
        output += f"Route: {analysis.route.value}\n"
        output += f"Intent Confidence: {analysis.intent_confidence.value}\n"
        output += f"Specialists Consulted: {', '.join(analysis.specialists_consulted)}\n"

        if analysis.risk_assessment:
            output += f"Risk Assessment: {analysis.risk_assessment.value} risk for violations\n"
        if analysis.compliance_score:
            output += f"Compliance Score: {analysis.compliance_score}/100\n"
        if analysis.confidence_score:
            output += f"Confidence Score: {analysis.confidence_score}%\n"

        return output + "\n"

    @staticmethod
    def format_resources(resources: List[Resource]) -> str:
        """Format related resources section"""
        if not resources or not format_config.should_show_section("resources", bool(resources)):
            return ""

        symbol = format_config.get_symbol("related_resources")
        info_color = format_config.get_color("info")
        reset_color = format_config.get_color("reset")

        output = f"{info_color}{symbol} RELATED RESOURCES{reset_color}\n"
        for resource in resources:
            if resource.url:
                output += f"- {resource.title}: {resource.explanation}\n"
                output += f"  {resource.url}\n"
            else:
                output += f"- {resource.title}: {resource.explanation}\n"
        return output + "\n"

    @staticmethod
    def format_next_steps(steps: List[str], approval_prompt: Optional[str] = None) -> str:
        """Format next steps section"""
        symbol = format_config.get_symbol("next_steps")
        info_color = format_config.get_color("info")
        reset_color = format_config.get_color("reset")

        output = f"{info_color}{symbol} NEXT STEPS{reset_color}\n"
        for i, step in enumerate(steps, 1):
            output += f"{i}. {step}\n"
        output += "\n"

        if approval_prompt and format_config.should_show_section("approval_prompt", bool(approval_prompt)):
            output += f"{approval_prompt}\n"

        return output

    @staticmethod
    def format_policy_education(
        resource_type: str,
        policy_requirements: List[str],
        critical_restrictions: List[str],
        compliance_essentials: Dict[str, Any],
        analysis: AnalysisSummary,
        resources: List[Resource],
        understanding_check: List[str]
    ) -> str:
        """Format Stage 1: Policy Education output"""
        output = OutputFormatter.format_header(Stage.POLICY_EDUCATION)
        output += "\n"

        output += f"⚠️  POLICY REQUIREMENTS FOR {resource_type}\n"
        for req in policy_requirements:
            output += f"- {req}\n"
        output += "\n"

        output += "🚨 CRITICAL RESTRICTIONS\n"
        for restriction in critical_restrictions:
            output += f"- {restriction}\n"
        output += "\n"

        output += "💡 NRP COMPLIANCE ESSENTIALS\n"
        if "required_labels" in compliance_essentials:
            output += "Required Labels:\n"
            for label, value in compliance_essentials["required_labels"].items():
                output += f"  {label}: \"{value}\"\n"
            output += "\n"

        if "resource_limits" in compliance_essentials:
            limits = compliance_essentials["resource_limits"]
            output += "Required Resource Limits:\n"
            output += f"  CPU: {limits.get('cpu', 'N/A')} | "
            output += f"Memory: {limits.get('memory', 'N/A')} | "
            output += f"Storage: {limits.get('storage', 'N/A')}\n\n"

        if "network_policies" in compliance_essentials:
            output += "Network Policies:\n"
            output += f"  {compliance_essentials['network_policies']}\n\n"

        output += OutputFormatter.format_analysis_summary(analysis)
        output += OutputFormatter.format_resources(resources)

        output += "🎯 UNDERSTANDING CHECK\n"
        output += "To proceed safely, you must understand:\n"
        for i, check in enumerate(understanding_check, 1):
            output += f"{i}. {check}\n"
        output += "\n"
        output += "Type \"I understand these requirements\" to proceed to template generation.\n"

        return output

    @staticmethod
    def format_yaml_generation(
        yaml_content: str,
        template_used: str,
        warnings: List[Warning],
        analysis: AnalysisSummary,
        resources: List[Resource],
        review_points: List[str]
    ) -> str:
        """Format Stage 2: YAML Generation output"""
        output = OutputFormatter.format_header(Stage.YAML_GENERATION)
        output += "\n"

        output += "✅ POLICY COMPLIANCE VERIFIED\n"
        output += "All NRP requirements incorporated into generated configuration.\n\n"

        output += "📝 GENERATED YAML CONFIGURATION\n"
        output += "```yaml\n"
        output += yaml_content
        output += "\n```\n\n"

        output += OutputFormatter.format_warnings(warnings)

        analysis_with_template = f"Template Used: {template_used}\n" + OutputFormatter.format_analysis_summary(analysis)
        output += analysis_with_template

        output += OutputFormatter.format_resources(resources)

        output += "🎯 REVIEW AND APPROVAL\n"
        output += "Please review the generated configuration:\n\n"
        for point in review_points:
            output += f"- {point}\n"
        output += "\n"
        output += "Type \"okay\" to proceed to deployment, or describe changes needed.\n"

        return output

    @staticmethod
    def format_kubernetes_execution(
        operation: str,
        resource_type: str,
        resource_name: str,
        namespace: str,
        status: str,
        validation_results: Dict[str, bool],
        deployment_results: Dict[str, Any],
        analysis: AnalysisSummary,
        monitoring_resources: List[Resource],
        next_steps: List[str],
        template_learning: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format Stage 3: Kubernetes Execution output"""
        output = OutputFormatter.format_header(Stage.KUBERNETES_EXECUTION)
        output += "\n"

        output += "🔒 FINAL SAFETY VALIDATION\n"
        for check, passed in validation_results.items():
            symbol = "✅" if passed else "❌"
            output += f"{symbol} {check}\n"
        output += "\n"

        output += "🚀 DEPLOYMENT RESULTS\n"
        output += f"Operation: {operation} {resource_type}/{resource_name}\n"
        output += f"Namespace: {namespace}\n"
        output += f"Status: {status}\n"
        output += "Resource Details:\n\n"

        for key, value in deployment_results.items():
            output += f"{key}: {value}\n"
        output += "\n"

        output += OutputFormatter.format_analysis_summary(analysis)

        if monitoring_resources:
            output += "📚 MONITORING RESOURCES\n"
            for resource in monitoring_resources:
                output += f"- {resource.title}: {resource.explanation}\n"
                if resource.url:
                    output += f"  {resource.url}\n"
            output += "\n"

        output += OutputFormatter.format_next_steps(next_steps)

        if template_learning:
            output += "📖 TEMPLATE LEARNING\n"
            output += "This successful deployment pattern has been saved for future use.\n"
            output += f"Template ID: {template_learning.get('template_id', 'auto-generated')}\n"
            output += f"Reusability Score: {template_learning.get('reusability_score', 'N/A')}\n"

        return output

    @staticmethod
    def format_knowledge_response(
        answer: str,
        key_policies: List[str],
        practical_examples: List[str],
        common_pitfalls: List[str],
        analysis: AnalysisSummary,
        resources: List[Resource]
    ) -> str:
        """Format knowledge query response"""
        output = OutputFormatter.format_header(custom_title="KNOWLEDGE RESPONSE")
        output += "\n"

        output += "📖 KNOWLEDGE RESPONSE\n"
        output += f"{answer}\n\n"

        if key_policies:
            output += "🔍 KEY POLICIES\n"
            for policy in key_policies:
                output += f"- {policy}\n"
            output += "\n"

        if practical_examples:
            output += "💡 PRACTICAL EXAMPLES\n"
            for example in practical_examples:
                output += f"{example}\n\n"

        if common_pitfalls:
            output += "⚠️  COMMON PITFALLS\n"
            for pitfall in common_pitfalls:
                output += f"- {pitfall}\n"
            output += "\n"

        output += OutputFormatter.format_analysis_summary(analysis)
        output += OutputFormatter.format_resources(resources)

        return output

    @staticmethod
    def format_crud_operation(
        command_executed: str,
        operation_result: str,
        resource_status: str,
        performance_impact: Optional[str],
        analysis: AnalysisSummary,
        resources: List[Resource]
    ) -> str:
        """Format CRUD operation response"""
        output = OutputFormatter.format_header(custom_title="CLUSTER OPERATION RESULTS")
        output += "\n"

        output += "⚡ CLUSTER OPERATION RESULTS\n"
        output += f"Command Executed: {command_executed}\n"
        output += f"Operation Result: {operation_result}\n"
        output += f"Resource Status:\n{resource_status}\n"

        if performance_impact:
            output += f"Performance Impact:\n{performance_impact}\n"
        output += "\n"

        output += OutputFormatter.format_analysis_summary(analysis)
        output += OutputFormatter.format_resources(resources)

        return output

    @staticmethod
    def format_blocking_error(
        issue_description: str,
        policy_violated: str,
        risk_level: RiskLevel,
        required_actions: List[str]
    ) -> str:
        """Format blocking error response"""
        output = "🔴 DEPLOYMENT BLOCKED\n"
        output += f"Critical Issue: {issue_description}\n"
        output += f"Policy Violated: {policy_violated}\n"
        output += f"Risk Level: {risk_level.value}\n"
        output += "Required Actions:\n\n"

        for action in required_actions:
            output += f"- {action}\n"

        output += "\nCannot proceed until these issues are resolved.\n"
        return output