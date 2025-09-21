#!/usr/bin/env python3
"""
Agent Orchestrator
==================

Clean, modular orchestrator that coordinates the three specialist agents:

1. Intent Router - Pure intent classification and routing
2. INFOGENT Agent - Information gathering with Navigator→Extractor→Aggregator
3. Code Generator Agent - Template creation with NRP examples
4. K8s Operations Agent - Confidence-gated Kubernetes operations

Architecture:
User Input → Intent Router → Specialist Agent → Response
"""

from typing import Dict, Any, List, Optional, Tuple
from .agent_types import IntentType, ConfidenceLevel, AgentRequest, AgentResponse
from .intent_router import IntentRouter, init_intent_router
from .fast_infogent_agent import FastInfogentAgent, init_fast_infogent_agent
from .code_generator import CodeGeneratorAgent, init_code_generator
from .k8s_operations_agent import K8sOperationsAgent, init_k8s_operations_agent
from ..utils.config import Config
from ..utils.validation import sanitize_input


class AgentOrchestrator:
    """
    Clean orchestrator for the NRP K8s agent system.

    Flow:
    1. Sanitize and validate input
    2. Route through Intent Router for classification
    3. Dispatch to appropriate specialist agent
    4. Format and return response

    Each agent is specialized and modular:
    - Intent Router: Pure routing decisions
    - INFOGENT: Information gathering with research
    - Code Generator: Template creation with examples
    - K8s Operations: Confidence-gated command execution
    """

    def __init__(self):
        # Initialize specialist agents
        self.intent_router = init_intent_router()
        self.infogent_agent = init_fast_infogent_agent()  # Use fast version
        self.code_generator = init_code_generator()
        self.k8s_operations = init_k8s_operations_agent()

        # Agent registry for routing
        self.agents = {
            IntentType.QUESTION: self.infogent_agent,
            IntentType.CODE_REQUEST: self.code_generator,
            IntentType.COMMAND: self.k8s_operations
        }

        print("[Orchestrator] Initialized with 4 agents")

    def process_request(self, user_input: str) -> Tuple[str, bool]:
        """
        Process user request through the agent system.

        Args:
            user_input: Raw user input

        Returns:
            Tuple of (response_content, success_flag)
        """
        try:
            # Setup configuration
            Config.setup()

            # Sanitize input
            clean_input = sanitize_input(user_input)
            if not clean_input:
                return "Please provide a valid input.", False

            print(f"[Orchestrator] Processing: {clean_input}")

            # Step 1: Intent classification and routing
            agent_request = self.intent_router.classify_intent(clean_input)

            # Display routing decision
            routing_summary = self.intent_router.get_routing_summary(agent_request)
            print(routing_summary)

            # Step 2: Handle unclear intents
            if self.intent_router.should_clarify(agent_request):
                clarification = self.intent_router.generate_clarification(agent_request)
                return clarification, True

            # Step 3: Dispatch to specialist agent
            if agent_request.intent_type not in self.agents:
                return f"No agent available for intent: {agent_request.intent_type.value}", False

            specialist_agent = self.agents[agent_request.intent_type]

            # Verify agent can handle the request
            if not specialist_agent.can_handle(agent_request):
                return f"Agent cannot handle this request type", False

            # Process with specialist agent
            agent_response = specialist_agent.process(agent_request)

            # Step 4: Format final response
            final_response = self._format_final_response(agent_response, agent_request)

            return final_response, agent_response.success

        except Exception as e:
            error_msg = f"System error: {str(e)}"
            print(f"[!] Orchestrator error: {error_msg}")
            return error_msg, False

    def _format_final_response(self, agent_response: AgentResponse,
                              original_request: AgentRequest) -> str:
        """Format the final response with metadata and suggestions."""

        response_parts = []

        # Add main response content
        response_parts.append(agent_response.content)

        # Add agent metadata if useful
        if agent_response.metadata and not agent_response.success:
            metadata_str = self._format_metadata(agent_response.metadata)
            if metadata_str:
                response_parts.append(f"\n**Technical Details:**\n{metadata_str}")

        # Add follow-up suggestions
        if agent_response.follow_up_suggestions:
            suggestions = "\n".join(f"- {suggestion}"
                                  for suggestion in agent_response.follow_up_suggestions[:3])
            response_parts.append(f"\n**What's next?**\n{suggestions}")

        # Add system info for debugging (only on failures)
        if not agent_response.success and agent_response.metadata.get("error"):
            response_parts.append(f"\n*Handled by: {agent_response.agent_type} Agent*")

        return "\n".join(response_parts)

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for display."""
        formatted_items = []

        for key, value in metadata.items():
            if key == "error":
                continue  # Handle errors separately

            # Format specific metadata types
            if key == "sources_consulted":
                formatted_items.append(f"Sources consulted: {value}")
            elif key == "execution_time":
                formatted_items.append(f"Execution time: {value:.2f}s")
            elif key == "template_used":
                formatted_items.append(f"Template used: {value}")
            elif key == "operation":
                formatted_items.append(f"Operation: {value}")
            elif isinstance(value, (list, dict)) and len(str(value)) < 100:
                formatted_items.append(f"{key}: {value}")

        return "\n".join(formatted_items)

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system."""
        return {
            "orchestrator": "active",
            "agents": {
                "intent_router": {
                    "status": "active",
                    "glm_v_available": bool(self.intent_router.glm_client),
                    "fallback_model": "gemma3" if not self.intent_router.glm_client else None,
                    "model_used": "GLM-V (glm-4v-plus)" if self.intent_router.glm_client else "gemma3"
                },
                "infogent": {
                    "status": "active",
                    "capabilities": len(self.infogent_agent.get_capabilities())
                },
                "code_generator": {
                    "status": "active",
                    "templates_loaded": len(self.code_generator.templates)
                },
                "k8s_operations": {
                    "status": "active",
                    "operations_available": len(self.k8s_operations.operation_map)
                }
            }
        }

    def get_available_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all agents."""
        return {
            "infogent": self.infogent_agent.get_capabilities(),
            "code_generator": self.code_generator.get_capabilities(),
            "k8s_operations": self.k8s_operations.get_capabilities()
        }

    def interactive_mode(self):
        """Run the orchestrator in interactive mode."""
        print("~ NRP K8s Agent System")
        print("=" * 40)
        print("Modular agent system with specialized handlers:")
        print("- Questions -> INFOGENT Agent (research & explanation)")
        print("- Code/Templates -> Code Generator Agent (YAML creation)")
        print("- Operations -> K8s Operations Agent (kubectl commands)")
        print()
        print("Type your request or 'quit' to exit.")
        print()

        while True:
            try:
                user_input = input("\n> nrp-k8s> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                if user_input.lower() in ['status', 'system']:
                    status = self.get_system_status()
                    print(f"\n[System Status]\n{self._format_status(status)}")
                    continue

                if user_input.lower() in ['help', '?']:
                    self._show_help()
                    continue

                # Process the request
                response, success = self.process_request(user_input)

                if success:
                    print(f"\n[+] {response}")
                else:
                    print(f"\n[-] {response}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[-] Unexpected error: {str(e)}")

    def _format_status(self, status: Dict[str, Any]) -> str:
        """Format system status for display."""
        lines = [f"Orchestrator: {status['orchestrator']}"]

        for agent_name, agent_info in status['agents'].items():
            lines.append(f"{agent_name}: {agent_info['status']}")

        return "\n".join(lines)

    def _show_help(self):
        """Show help information."""
        capabilities = self.get_available_capabilities()
        status = self.get_system_status()
        intent_status = status['agents']['intent_router']

        help_text = f"""
~ NRP K8s Agent System - Help

**AGENT TYPES:**

1. **INFOGENT Agent** (Questions & Research)
{chr(10).join(f"   - {cap}" for cap in capabilities['infogent'][:3])}

2. **Code Generator Agent** (Templates & Examples)
{chr(10).join(f"   - {cap}" for cap in capabilities['code_generator'][:3])}

3. **K8s Operations Agent** (Commands & Operations)
{chr(10).join(f"   - {cap}" for cap in capabilities['k8s_operations'][:3])}

**INTENT CLASSIFICATION:**
  Model: {intent_status.get('model_used', 'unknown')}
  GLM-V Status: {'[Active]' if intent_status.get('glm_v_available') else '[Not configured]'}

**EXAMPLES:**

Questions:
  "How do I request GPUs on NRP?"
  "What are the storage options?"
  "Explain Kubernetes networking"

Code/Templates:
  "Create a GPU deployment YAML"
  "Show me ingress template"
  "Generate service configuration"

Operations:
  "list my pods"
  "describe deployment myapp"
  "delete pod xyz"

**COMMANDS:**
  status - Show system status
  help/? - Show this help
  quit/exit/q - Exit system

**GLM-V CONFIGURATION:**
To enable GLM-V for better intent classification:
  export GLM_API_KEY=your_glm_api_key
  export GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
  export GLM_MODEL=glm-4v-plus
"""
        print(help_text)


def init_orchestrator() -> AgentOrchestrator:
    """Initialize the agent orchestrator."""
    return AgentOrchestrator()


# Compatibility functions for existing router interface
def route_user_request(user_input: str) -> Tuple[str, bool]:
    """
    Compatibility function for existing router interface.
    Routes through the new orchestrator system.
    """
    orchestrator = init_orchestrator()
    return orchestrator.process_request(user_input)


def interactive_mode():
    """
    Compatibility function for existing interactive mode.
    Uses the new orchestrator system.
    """
    orchestrator = init_orchestrator()
    orchestrator.interactive_mode()