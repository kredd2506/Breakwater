"""
NRP K8s System Agents
====================

Modular agent-based architecture for intelligent K8s operations:

- Intent Router: Pure intent classification and routing
- INFOGENT Agent: Information gathering with Navigator→Extractor→Aggregator
- Code Generator Agent: Template creation with NRP examples
- K8s Operations Agent: Confidence-gated Kubernetes operations
- Orchestrator: Clean coordinator for all agents
"""

from .agent_types import IntentType, ConfidenceLevel, AgentRequest, AgentResponse, BaseAgent
from .intent_router import IntentRouter, init_intent_router
from .infogent_agent import InfogentAgent, init_infogent_agent
from .code_generator import CodeGeneratorAgent, init_code_generator
from .k8s_operations_agent import K8sOperationsAgent, init_k8s_operations_agent
from .orchestrator import AgentOrchestrator, init_orchestrator, route_user_request, interactive_mode

__all__ = [
    # Core types
    "IntentType",
    "ConfidenceLevel",
    "AgentRequest",
    "AgentResponse",
    "BaseAgent",

    # Agents
    "IntentRouter",
    "InfogentAgent",
    "CodeGeneratorAgent",
    "K8sOperationsAgent",
    "AgentOrchestrator",

    # Initialization functions
    "init_intent_router",
    "init_infogent_agent",
    "init_code_generator",
    "init_k8s_operations_agent",
    "init_orchestrator",

    # Compatibility functions
    "route_user_request",
    "interactive_mode"
]