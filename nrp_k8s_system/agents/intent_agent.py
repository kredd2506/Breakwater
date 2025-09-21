#!/usr/bin/env python3
"""
Intent Agent with GLM-V Integration
==================================

Advanced intent classification agent that uses GLM-V's tool calling capabilities
to intelligently route user requests and gather additional context when needed.

Features:
- GLM-V powered intent classification
- Tool calling for command discovery and validation
- Integration with Navigator/Extractor/Infogent architecture
- Adaptive clarification requests
- Context-aware routing decisions
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from ..core.glm_client import GLMVClient, init_glm_client, K8S_TOOLS, CLARIFICATION_TOOLS
from ..core.nrp_init import init_chat_model
from ..routers.intent_classifier import UserIntent, RouterDecision
from ..utils.validation import sanitize_input
from ..systems import k8s_operations


class IntentConfidence(Enum):
    """Intent classification confidence levels."""
    HIGH = "high"       # > 0.8
    MEDIUM = "medium"   # 0.6 - 0.8
    LOW = "low"         # 0.4 - 0.6
    UNCLEAR = "unclear" # < 0.4


@dataclass
class AgentDecision:
    """Enhanced decision structure from intent agent."""
    intent: UserIntent
    confidence: IntentConfidence
    reasoning: str
    suggested_actions: List[str]
    tool_calls: List[Dict[str, Any]]
    clarification_needed: bool
    context_gathered: Dict[str, Any]


class IntentAgent:
    """
    Advanced intent classification agent using GLM-V.

    This agent combines traditional intent classification with tool calling
    to provide more accurate routing and proactive assistance.
    """

    def __init__(self):
        self.glm_client = init_glm_client()
        self.fallback_client = init_chat_model()

    def analyze_intent(self, user_input: str) -> AgentDecision:
        """
        Analyze user intent using GLM-V with tool calling capabilities.

        Args:
            user_input: Raw user input string

        Returns:
            AgentDecision with comprehensive analysis
        """
        clean_input = sanitize_input(user_input)

        if self.glm_client:
            try:
                return self._analyze_with_glm(clean_input)
            except Exception as e:
                print(f"[!] GLM-V analysis failed: {e}")
                return self._fallback_analysis(clean_input)
        else:
            print("[*] Using fallback analysis (GLM-V not available)")
            return self._fallback_analysis(clean_input)

    def _analyze_with_glm(self, user_input: str) -> AgentDecision:
        """Analyze using GLM-V with tool calling."""

        # Prepare the system prompt for intent analysis
        system_prompt = """You are an intelligent router for an NRP (National Research Platform) + Kubernetes system.
Your job is to analyze user input and determine the best course of action.

CLASSIFICATION RULES:
1. COMMAND: Direct Kubernetes operations (list, get, describe, delete, create, logs, etc.)
2. EXPLANATION: Documentation, guidance, how-to questions, best practices
3. UNCLEAR: Ambiguous or insufficient information

AVAILABLE TOOLS:
- list_k8s_resources: Check what resources exist
- describe_k8s_resource: Get details about specific resources
- get_pod_logs: Retrieve pod logs
- search_nrp_docs: Search documentation
- request_clarification: Ask for clarification

DECISION PROCESS:
1. Classify the intent (command vs explanation vs unclear)
2. If it's a command but missing details (like resource names), use tools to discover available resources
3. If it's unclear, use request_clarification tool
4. Provide confidence level and suggested actions

Be proactive: if user says "show me my pods" and you're not sure which pods exist,
call list_k8s_resources to find out, then provide a more specific response."""

        user_prompt = f"""
Analyze this user input and determine the best response strategy:

User Input: "{user_input}"

Classify the intent, determine confidence level, and if helpful, use available tools to gather context or provide clarification.
"""

        try:
            # Use native OpenAI client for tool calling
            native_client = self.glm_client.get_native_client()

            response = native_client.chat.completions.create(
                model=self.glm_client.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=K8S_TOOLS + CLARIFICATION_TOOLS,
                tool_choice="auto",
                max_tokens=self.glm_client.config.max_tokens,
                temperature=0.3  # Lower temperature for more consistent classification
            )

            return self._process_glm_response(response, user_input)

        except Exception as e:
            print(f"[!] GLM-V tool calling failed: {e}")
            return self._fallback_analysis(user_input)

    def _process_glm_response(self, response, user_input: str) -> AgentDecision:
        """Process GLM-V response with tool calls."""

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        # Execute tool calls if any
        context_gathered = {}
        executed_tools = []

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                result = self._execute_tool(tool_name, args)
                context_gathered[tool_name] = result
                executed_tools.append({
                    "name": tool_name,
                    "args": args,
                    "result": result
                })

            except Exception as e:
                print(f"[!] Tool execution failed for {tool_call.function.name}: {e}")
                context_gathered[tool_call.function.name] = f"Error: {e}"

        # Extract intent from response content or infer from tools
        intent, confidence, reasoning, suggestions = self._extract_intent_from_response(
            message.content, executed_tools, user_input
        )

        return AgentDecision(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            suggested_actions=suggestions,
            tool_calls=executed_tools,
            clarification_needed=confidence == IntentConfidence.UNCLEAR,
            context_gathered=context_gathered
        )

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool call and return the result."""

        if tool_name == "list_k8s_resources":
            resource_type = args.get("resource_type")
            # Map to appropriate k8s_operations function
            if resource_type == "pods":
                return k8s_operations.list_pods()
            elif resource_type == "services":
                return k8s_operations.list_services()
            elif resource_type == "deployments":
                return k8s_operations.list_deployments()
            elif resource_type == "jobs":
                return k8s_operations.list_jobs()
            elif resource_type == "configmaps":
                return k8s_operations.list_configmaps()
            elif resource_type == "secrets":
                return k8s_operations.list_secrets()
            elif resource_type == "pvcs":
                return k8s_operations.list_pvcs()
            else:
                return f"Unsupported resource type: {resource_type}"

        elif tool_name == "describe_k8s_resource":
            resource_type = args.get("resource_type")
            resource_name = args.get("resource_name")
            # Map to appropriate describe function
            if resource_type == "pod":
                return k8s_operations.describe_pod(resource_name)
            elif resource_type == "service":
                return k8s_operations.describe_service(resource_name)
            elif resource_type == "deployment":
                return k8s_operations.describe_deployment(resource_name)
            elif resource_type == "job":
                return k8s_operations.describe_job(resource_name)
            elif resource_type == "configmap":
                return k8s_operations.describe_configmap(resource_name)
            elif resource_type == "secret":
                return k8s_operations.describe_secret(resource_name)
            elif resource_type == "pvc":
                return k8s_operations.describe_pvc(resource_name)
            else:
                return f"Unsupported resource type: {resource_type}"

        elif tool_name == "get_pod_logs":
            pod_name = args.get("pod_name")
            lines = args.get("lines", 100)
            return k8s_operations.pod_logs(pod_name, tail_lines=lines)

        elif tool_name == "search_nrp_docs":
            query = args.get("query")
            topic = args.get("topic")
            # This would integrate with the Navigator/Extractor pattern
            return self._search_docs(query, topic)

        elif tool_name == "request_clarification":
            return {
                "type": args.get("clarification_type"),
                "suggestions": args.get("suggestions", []),
                "context": args.get("context", "")
            }

        else:
            return f"Unknown tool: {tool_name}"

    def _search_docs(self, query: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Search NRP documentation using Navigator/Extractor pattern."""
        # This will integrate with the existing infogent architecture
        return {
            "query": query,
            "topic": topic,
            "results": "Documentation search would be implemented here",
            "note": "Integration with Navigator/Extractor/Infogent pending"
        }

    def _extract_intent_from_response(self, content: str, tool_calls: List[Dict], user_input: str) -> Tuple[UserIntent, IntentConfidence, str, List[str]]:
        """Extract intent classification from GLM response."""

        # Analyze tool calls to infer intent
        if any(tool["name"] in ["list_k8s_resources", "describe_k8s_resource", "get_pod_logs"] for tool in tool_calls):
            intent = UserIntent.COMMAND
            confidence = IntentConfidence.HIGH
            reasoning = "GLM-V agent used K8s tools, indicating command intent"
            suggestions = [f"Execute {tool['name']} with gathered context" for tool in tool_calls]

        elif any(tool["name"] == "search_nrp_docs" for tool in tool_calls):
            intent = UserIntent.EXPLANATION
            confidence = IntentConfidence.HIGH
            reasoning = "GLM-V agent searched documentation, indicating explanation request"
            suggestions = ["Provide comprehensive explanation using search results"]

        elif any(tool["name"] == "request_clarification" for tool in tool_calls):
            intent = UserIntent.UNCLEAR
            confidence = IntentConfidence.UNCLEAR
            reasoning = "GLM-V agent requested clarification due to ambiguous input"
            clarification_data = next((tool["result"] for tool in tool_calls if tool["name"] == "request_clarification"), {})
            suggestions = clarification_data.get("suggestions", ["Please provide more specific information"])

        else:
            # Fallback to content analysis
            intent, confidence, reasoning, suggestions = self._analyze_content(content, user_input)

        return intent, confidence, reasoning, suggestions

    def _analyze_content(self, content: str, user_input: str) -> Tuple[UserIntent, IntentConfidence, str, List[str]]:
        """Analyze response content for intent classification."""
        content_lower = (content or "").lower()
        input_lower = user_input.lower()

        # Command indicators
        command_keywords = ['kubectl', 'list', 'get', 'describe', 'delete', 'create', 'apply', 'logs', 'exec']
        command_score = sum(1 for kw in command_keywords if kw in input_lower)

        # Explanation indicators
        question_keywords = ['how', 'what', 'why', 'explain', 'guide', 'best practice', 'tutorial']
        question_score = sum(1 for kw in question_keywords if kw in input_lower)

        if command_score > question_score and command_score > 0:
            return (
                UserIntent.COMMAND,
                IntentConfidence.MEDIUM,
                f"Contains command indicators: {command_score} matches",
                ["Execute the Kubernetes command", "Verify resource exists first"]
            )
        elif question_score > 0:
            return (
                UserIntent.EXPLANATION,
                IntentConfidence.MEDIUM,
                f"Contains question indicators: {question_score} matches",
                ["Provide detailed explanation", "Include relevant examples"]
            )
        else:
            return (
                UserIntent.UNCLEAR,
                IntentConfidence.UNCLEAR,
                "No clear intent indicators found",
                ["Request clarification from user", "Provide examples of valid requests"]
            )

    def _fallback_analysis(self, user_input: str) -> AgentDecision:
        """Fallback analysis using traditional classification."""
        try:
            # Use existing intent classifier as fallback
            from ..routers.intent_classifier import classify_user_intent

            decision = classify_user_intent(user_input)

            # Convert to AgentDecision format
            confidence_map = {
                (0.8, 1.0): IntentConfidence.HIGH,
                (0.6, 0.8): IntentConfidence.MEDIUM,
                (0.4, 0.6): IntentConfidence.LOW,
                (0.0, 0.4): IntentConfidence.UNCLEAR
            }

            confidence = IntentConfidence.UNCLEAR
            for (min_conf, max_conf), conf_level in confidence_map.items():
                if min_conf <= decision.confidence < max_conf:
                    confidence = conf_level
                    break

            return AgentDecision(
                intent=decision.intent,
                confidence=confidence,
                reasoning=f"Fallback analysis: {decision.reasoning}",
                suggested_actions=[decision.suggested_handler],
                tool_calls=[],
                clarification_needed=confidence == IntentConfidence.UNCLEAR,
                context_gathered={}
            )

        except Exception as e:
            # Ultimate fallback
            return AgentDecision(
                intent=UserIntent.UNCLEAR,
                confidence=IntentConfidence.UNCLEAR,
                reasoning=f"Analysis failed: {e}",
                suggested_actions=["Manual review required"],
                tool_calls=[],
                clarification_needed=True,
                context_gathered={}
            )

    def should_request_clarification(self, decision: AgentDecision) -> bool:
        """Determine if clarification should be requested."""
        return (
            decision.clarification_needed or
            decision.confidence == IntentConfidence.UNCLEAR or
            (decision.confidence == IntentConfidence.LOW and not decision.tool_calls)
        )

    def format_clarification_request(self, decision: AgentDecision) -> str:
        """Format a clarification request for the user."""
        if decision.tool_calls and any(tool["name"] == "request_clarification" for tool in decision.tool_calls):
            # Use GLM-V generated clarification
            clarification_tool = next(tool for tool in decision.tool_calls if tool["name"] == "request_clarification")
            result = clarification_tool.get("result", {})

            clarification_type = result.get("type", "unclear_intent")
            suggestions = result.get("suggestions", [])
            context = result.get("context", "")

            msg = f"I need clarification about your request.\n\n"
            if context:
                msg += f"Context: {context}\n\n"

            msg += "Here are some suggestions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                msg += f"{i}. {suggestion}\n"

            return msg
        else:
            # Fallback clarification
            return f"""
I'm not sure about your request: "{decision.reasoning}"

Please try being more specific. For example:

**For Commands:**
- "list pods in gsoc namespace"
- "describe deployment myapp"
- "show logs for pod xyz"

**For Explanations:**
- "How do I request GPUs for my pod?"
- "What are best practices for storage?"
- "How do I troubleshoot failed deployments?"
"""


def init_intent_agent() -> IntentAgent:
    """Initialize the intent agent."""
    return IntentAgent()