#!/usr/bin/env python3
"""
Kubernetes Operations Agent
===========================

Handles Kubernetes operations with confidence-based gating. This agent:

1. Executes kubectl-style operations (list, describe, delete, create)
2. Uses confidence levels to gate dangerous operations
3. Provides safety checks and confirmations
4. Integrates with existing Python K8s API functions
5. Offers operation previews and rollback guidance

Confidence Gating:
- HIGH: Execute immediately
- MEDIUM: Show preview, ask for confirmation
- LOW: Request clarification of parameters
- UNCLEAR: Refuse operation, suggest alternatives
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .agent_types import BaseAgent, AgentRequest, AgentResponse, IntentType, ConfidenceLevel
from ..systems import k8s_operations
from ..utils.validation import sanitize_input


class OperationType(Enum):
    """Types of Kubernetes operations."""
    READ = "read"           # list, get, describe, logs - Safe operations
    WRITE = "write"         # create, apply, patch - Modify operations
    DELETE = "delete"       # delete, remove - Destructive operations
    EXEC = "exec"           # exec, port-forward - Interactive operations


class SafetyLevel(Enum):
    """Safety levels for operations."""
    SAFE = "safe"           # Read-only operations
    MODERATE = "moderate"   # Create/update operations
    DANGEROUS = "dangerous" # Delete/destructive operations
    CRITICAL = "critical"   # Cluster-wide or system operations


@dataclass
class Operation:
    """Kubernetes operation definition."""
    command: str
    operation_type: OperationType
    safety_level: SafetyLevel
    function_name: str
    parameters: Dict[str, Any]
    description: str
    preview: str


@dataclass
class OperationResult:
    """Result of executing a Kubernetes operation."""
    success: bool
    output: str
    operation: Operation
    execution_time: float
    warnings: List[str]


class K8sOperationsAgent(BaseAgent):
    """
    Kubernetes Operations Agent with confidence-based safety gating.

    Safety Matrix:
    - HIGH confidence + SAFE operation → Execute immediately
    - HIGH confidence + MODERATE operation → Execute with logging
    - HIGH confidence + DANGEROUS operation → Show preview, confirm
    - MEDIUM confidence + any → Show preview, confirm
    - LOW confidence → Request clarification
    - UNCLEAR → Refuse, suggest alternatives
    """

    def __init__(self):
        self.operation_map = self._build_operation_map()
        self.safety_policies = self._load_safety_policies()

    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        return request.intent_type == IntentType.COMMAND

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process Kubernetes operation request with confidence gating.

        Flow:
        1. Parse command to identify operation and parameters
        2. Apply confidence-based safety gating
        3. Execute operation if approved
        4. Return result with safety information
        """
        try:
            print(f"[K8s Operations] Processing: {request.user_input}")

            # Step 1: Parse command
            operation = self._parse_command(request.user_input)
            if not operation:
                return self._handle_unknown_command(request)

            # Step 2: Apply safety gating
            gate_result = self._apply_safety_gate(operation, request.confidence)

            if gate_result["action"] == "deny":
                return self._handle_denied_operation(operation, gate_result, request)
            elif gate_result["action"] == "confirm":
                return self._handle_confirmation_needed(operation, gate_result, request)
            elif gate_result["action"] == "execute":
                # Step 3: Execute operation
                result = self._execute_operation(operation)
                return self._format_success_response(result, request)

        except Exception as e:
            print(f"[!] K8s operation failed: {e}")
            return AgentResponse(
                success=False,
                content=f"Operation failed: {str(e)}",
                agent_type="K8s Operations",
                confidence=ConfidenceLevel.LOW,
                metadata={"error": str(e)},
                follow_up_suggestions=["Check your command syntax", "Verify resource exists"]
            )

    def _build_operation_map(self) -> Dict[str, Operation]:
        """Build mapping of commands to operations."""

        operations = {
            # READ operations (SAFE)
            "list pods": Operation(
                command="list pods",
                operation_type=OperationType.READ,
                safety_level=SafetyLevel.SAFE,
                function_name="list_pods",
                parameters={},
                description="List all pods in current namespace",
                preview="kubectl get pods"
            ),
            "list deployments": Operation(
                command="list deployments",
                operation_type=OperationType.READ,
                safety_level=SafetyLevel.SAFE,
                function_name="list_deployments",
                parameters={},
                description="List all deployments in current namespace",
                preview="kubectl get deployments"
            ),
            "list services": Operation(
                command="list services",
                operation_type=OperationType.READ,
                safety_level=SafetyLevel.SAFE,
                function_name="list_services",
                parameters={},
                description="List all services in current namespace",
                preview="kubectl get services"
            ),
            "describe pod": Operation(
                command="describe pod",
                operation_type=OperationType.READ,
                safety_level=SafetyLevel.SAFE,
                function_name="describe_pod",
                parameters={"name": ""},
                description="Describe a specific pod",
                preview="kubectl describe pod <name>"
            ),
            "pod logs": Operation(
                command="pod logs",
                operation_type=OperationType.READ,
                safety_level=SafetyLevel.SAFE,
                function_name="pod_logs",
                parameters={"name": "", "tail_lines": 100},
                description="Get logs from a pod",
                preview="kubectl logs <name>"
            ),

            # DELETE operations (DANGEROUS)
            "delete pod": Operation(
                command="delete pod",
                operation_type=OperationType.DELETE,
                safety_level=SafetyLevel.DANGEROUS,
                function_name="delete_pod",
                parameters={"name": ""},
                description="Delete a specific pod",
                preview="kubectl delete pod <name>"
            ),
            "delete deployment": Operation(
                command="delete deployment",
                operation_type=OperationType.DELETE,
                safety_level=SafetyLevel.DANGEROUS,
                function_name="delete_deployment",
                parameters={"name": ""},
                description="Delete a deployment and its pods",
                preview="kubectl delete deployment <name>"
            ),

            # WRITE operations (MODERATE)
            "create pod": Operation(
                command="create pod",
                operation_type=OperationType.WRITE,
                safety_level=SafetyLevel.MODERATE,
                function_name="create_pod_programmatic",
                parameters={"name": "", "image": ""},
                description="Create a new pod",
                preview="kubectl run <name> --image=<image>"
            ),
        }

        return operations

    def _load_safety_policies(self) -> Dict[str, Dict[str, str]]:
        """Load safety policies for confidence-operation combinations."""

        return {
            # HIGH confidence policies
            "high": {
                "safe": "execute",      # Execute immediately
                "moderate": "execute",  # Execute with logging
                "dangerous": "confirm", # Show preview, confirm
                "critical": "confirm"   # Always confirm critical ops
            },
            # MEDIUM confidence policies
            "medium": {
                "safe": "execute",      # Execute safe operations
                "moderate": "confirm",  # Confirm moderate operations
                "dangerous": "confirm", # Confirm dangerous operations
                "critical": "deny"      # Deny critical operations
            },
            # LOW confidence policies
            "low": {
                "safe": "confirm",      # Confirm even safe operations
                "moderate": "deny",     # Deny moderate operations
                "dangerous": "deny",    # Deny dangerous operations
                "critical": "deny"      # Deny critical operations
            },
            # UNCLEAR confidence policies
            "unclear": {
                "safe": "deny",         # Deny all operations
                "moderate": "deny",
                "dangerous": "deny",
                "critical": "deny"
            }
        }

    def _parse_command(self, user_input: str) -> Optional[Operation]:
        """Parse user input to identify Kubernetes operation."""

        clean_input = sanitize_input(user_input).lower()

        # Direct command matching
        for command, operation in self.operation_map.items():
            if command in clean_input:
                # Extract parameters if needed
                parsed_operation = self._extract_parameters(operation, clean_input)
                return parsed_operation

        # Pattern-based matching
        patterns = {
            r"list\s+(pods?|po)": "list pods",
            r"list\s+(deployments?|deploy)": "list deployments",
            r"list\s+(services?|svc)": "list services",
            r"describe\s+pod\s+(\w+)": "describe pod",
            r"delete\s+pod\s+(\w+)": "delete pod",
            r"delete\s+deployment\s+(\w+)": "delete deployment",
            r"logs?\s+(\w+)": "pod logs",
            r"get\s+pods?": "list pods",
            r"get\s+deployments?": "list deployments",
            r"get\s+services?": "list services"
        }

        for pattern, command in patterns.items():
            match = re.search(pattern, clean_input)
            if match:
                operation = self.operation_map[command].copy() if command in self.operation_map else None
                if operation and match.groups():
                    # Extract resource name from pattern
                    resource_name = match.group(1)
                    operation.parameters["name"] = resource_name
                return operation

        return None

    def _extract_parameters(self, operation: Operation, user_input: str) -> Operation:
        """Extract parameters from user input for the operation."""

        # Create a copy to avoid modifying the original
        parsed_operation = Operation(
            command=operation.command,
            operation_type=operation.operation_type,
            safety_level=operation.safety_level,
            function_name=operation.function_name,
            parameters=operation.parameters.copy(),
            description=operation.description,
            preview=operation.preview
        )

        # Extract resource names
        if "name" in parsed_operation.parameters:
            # Look for resource name after the command
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ["pod", "deployment", "service"] and i + 1 < len(words):
                    parsed_operation.parameters["name"] = words[i + 1]
                    break

        # Extract other parameters
        if "image" in parsed_operation.parameters:
            image_match = re.search(r"image[=:]?\s*(\S+)", user_input)
            if image_match:
                parsed_operation.parameters["image"] = image_match.group(1)

        return parsed_operation

    def _apply_safety_gate(self, operation: Operation, confidence: ConfidenceLevel) -> Dict[str, Any]:
        """Apply confidence-based safety gating."""

        confidence_key = confidence.value
        safety_key = operation.safety_level.value

        # Get policy decision
        action = self.safety_policies[confidence_key][safety_key]

        # Generate reasoning
        reasoning = f"Confidence: {confidence_key}, Safety: {safety_key} → {action}"

        # Add operation-specific warnings
        warnings = []
        if operation.safety_level == SafetyLevel.DANGEROUS:
            warnings.append("⚠️  This is a destructive operation")
        if operation.operation_type == OperationType.DELETE:
            warnings.append("⚠️  This will permanently delete resources")

        return {
            "action": action,
            "reasoning": reasoning,
            "warnings": warnings,
            "requires_confirmation": action == "confirm"
        }

    def _execute_operation(self, operation: Operation) -> OperationResult:
        """Execute the Kubernetes operation."""

        import time
        start_time = time.time()

        try:
            # Get the function from k8s_operations module
            function = getattr(k8s_operations, operation.function_name)

            # Prepare parameters
            params = {k: v for k, v in operation.parameters.items() if v}

            # Execute the function
            if params:
                if operation.function_name in ["describe_pod", "describe_deployment", "delete_pod", "delete_deployment"]:
                    # Functions that take a name parameter
                    if "name" in params:
                        result = function(params["name"])
                    else:
                        result = "Error: Resource name required"
                elif operation.function_name == "pod_logs":
                    # Pod logs function
                    result = function(params.get("name"), params.get("tail_lines", 100))
                elif operation.function_name == "create_pod_programmatic":
                    # Create pod function
                    result = function(
                        name=params.get("name", "test-pod"),
                        image=params.get("image", "nginx")
                    )
                else:
                    result = function()
            else:
                result = function()

            execution_time = time.time() - start_time

            return OperationResult(
                success=True,
                output=str(result) if result else "Operation completed successfully",
                operation=operation,
                execution_time=execution_time,
                warnings=[]
            )

        except Exception as e:
            execution_time = time.time() - start_time

            return OperationResult(
                success=False,
                output=f"Operation failed: {str(e)}",
                operation=operation,
                execution_time=execution_time,
                warnings=[f"Error: {str(e)}"]
            )

    def _handle_unknown_command(self, request: AgentRequest) -> AgentResponse:
        """Handle unknown commands."""

        available_commands = list(self.operation_map.keys())

        content = f"""Unknown Kubernetes command: "{request.user_input}"

**Available Commands:**
{chr(10).join(f"- {cmd}" for cmd in available_commands)}

**Examples:**
- "list pods" - Show all pods
- "describe pod mypod" - Get pod details
- "delete pod mypod" - Remove a pod
- "pod logs mypod" - Show pod logs

**Tip:** Use specific resource names for describe/delete operations."""

        return AgentResponse(
            success=False,
            content=content,
            agent_type="K8s Operations",
            confidence=ConfidenceLevel.LOW,
            metadata={"available_commands": available_commands},
            follow_up_suggestions=[
                "Try 'list pods' to see available resources",
                "Use 'describe pod <name>' for details",
                "Check command syntax"
            ]
        )

    def _handle_denied_operation(self, operation: Operation, gate_result: Dict[str, Any],
                                request: AgentRequest) -> AgentResponse:
        """Handle operations that are denied by safety gate."""

        content = f"""Operation denied for safety reasons.

**Command:** {operation.command}
**Reason:** {gate_result['reasoning']}
**Safety Level:** {operation.safety_level.value}

{chr(10).join(gate_result['warnings'])}

**Suggestions:**
- Be more specific about the resource name
- Use a safer alternative command
- Increase confidence by providing more details"""

        return AgentResponse(
            success=False,
            content=content,
            agent_type="K8s Operations",
            confidence=request.confidence,
            metadata={
                "operation": operation.command,
                "safety_level": operation.safety_level.value,
                "denial_reason": gate_result['reasoning']
            },
            follow_up_suggestions=[
                "Try a list command first to see available resources",
                "Be more specific about what you want to do",
                "Use describe before delete operations"
            ]
        )

    def _handle_confirmation_needed(self, operation: Operation, gate_result: Dict[str, Any],
                                   request: AgentRequest) -> AgentResponse:
        """Handle operations that need confirmation."""

        # Format parameters for preview
        param_str = ", ".join(f"{k}={v}" for k, v in operation.parameters.items() if v)

        content = f"""Confirmation required for this operation.

**Operation:** {operation.description}
**Command Preview:** {operation.preview}
**Parameters:** {param_str if param_str else 'None'}

{chr(10).join(gate_result['warnings'])}

**To proceed:**
1. Review the operation details above
2. Confirm by saying "yes, execute" or "confirm"
3. Cancel by saying "no" or "cancel"

**Safety Info:**
- Type: {operation.operation_type.value}
- Safety Level: {operation.safety_level.value}
- Confidence: {request.confidence.value}"""

        return AgentResponse(
            success=True,  # Success because we handled the request (pending confirmation)
            content=content,
            agent_type="K8s Operations",
            confidence=request.confidence,
            metadata={
                "operation": operation.command,
                "requires_confirmation": True,
                "safety_level": operation.safety_level.value,
                "preview": operation.preview
            },
            follow_up_suggestions=[
                "Say 'yes, execute' to proceed",
                "Say 'no' to cancel",
                "Ask for more details about the operation"
            ]
        )

    def _format_success_response(self, result: OperationResult,
                               request: AgentRequest) -> AgentResponse:
        """Format successful operation response."""

        content = f"""**Operation Completed Successfully**

**Command:** {result.operation.description}
**Execution Time:** {result.execution_time:.2f} seconds

**Output:**
```
{result.output}
```

{chr(10).join(f"⚠️  {warning}" for warning in result.warnings) if result.warnings else ""}"""

        return AgentResponse(
            success=result.success,
            content=content,
            agent_type="K8s Operations",
            confidence=request.confidence,
            metadata={
                "operation": result.operation.command,
                "execution_time": result.execution_time,
                "operation_type": result.operation.operation_type.value,
                "safety_level": result.operation.safety_level.value
            },
            follow_up_suggestions=self._generate_follow_up_suggestions(result.operation)
        )

    def _generate_follow_up_suggestions(self, operation: Operation) -> List[str]:
        """Generate contextual follow-up suggestions."""

        suggestions = []

        if operation.operation_type == OperationType.READ:
            if "list" in operation.command:
                suggestions.extend([
                    "Use 'describe <resource> <name>' for details",
                    "Try 'logs <pod-name>' to see pod logs"
                ])
            elif "describe" in operation.command:
                suggestions.extend([
                    "Use 'logs <pod-name>' if it's a pod",
                    "Check related resources"
                ])

        elif operation.operation_type == OperationType.DELETE:
            suggestions.extend([
                "Verify the resource was deleted with 'list'",
                "Check if dependent resources need cleanup"
            ])

        elif operation.operation_type == OperationType.WRITE:
            suggestions.extend([
                "Use 'list' to verify creation",
                "Use 'describe' to check status"
            ])

        # Generic suggestions
        suggestions.extend([
            "Need help with other operations?",
            "Want to see related resources?"
        ])

        return suggestions[:3]  # Limit to 3 suggestions

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "Execute Kubernetes read operations (list, describe, logs)",
            "Execute write operations with safety confirmation",
            "Execute delete operations with confidence gating",
            "Provide operation previews and safety warnings",
            "Generate contextual follow-up suggestions",
            "Integrate with existing Python K8s API functions"
        ]


def init_k8s_operations_agent() -> K8sOperationsAgent:
    """Initialize the K8s operations agent."""
    return K8sOperationsAgent()