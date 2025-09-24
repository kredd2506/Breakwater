#!/usr/bin/env python3
"""
Intent Router Agent
==================

Pure intent classification and routing agent. This agent's only job is to:
1. Analyze user input to determine intent type
2. Assign confidence level
3. Route to appropriate specialist agent

Does NOT execute any operations - only routing decisions.
"""

import re
from typing import Dict, Any, Tuple
from .agent_types import IntentType, ConfidenceLevel, AgentRequest
from ..core.glm_client import GLMVClient, init_glm_client
from ..core.nrp_init import init_chat_model
from ..utils.validation import sanitize_input


class IntentRouter:
    """
    Pure intent classification and routing agent.

    Determines which specialist agent should handle the request:
    - QUESTION → INFOGENT Agent (information gathering)
    - CODE_REQUEST → Code Generator Agent (template creation)
    - COMMAND → K8s Operations Agent (kubectl operations)
    - UNCLEAR → Clarification needed
    """

    def __init__(self):
        self.glm_client = init_glm_client()
        self.fallback_client = init_chat_model()

        # Prefer GLM-V for intent classification
        if self.glm_client:
            print("[Intent Router] Using GLM-V for intent classification")
        else:
            print("[Intent Router] GLM-V not available, using fallback (gemma3)")

    def classify_intent(self, user_input: str) -> AgentRequest:
        """
        Classify user intent and create AgentRequest for routing.

        Args:
            user_input: Raw user input

        Returns:
            AgentRequest with intent classification
        """
        clean_input = sanitize_input(user_input)

        if self.glm_client:
            try:
                return self._classify_with_glm(clean_input)
            except Exception as e:
                print(f"[!] GLM-V classification failed: {e}")
                return self._classify_with_fallback(clean_input)
        else:
            return self._classify_with_fallback(clean_input)

    def _classify_with_glm(self, user_input: str) -> AgentRequest:
        """Classify using GLM-V for better accuracy."""

        system_prompt = """You are an intent classifier for an NRP Kubernetes system.
Classify the user's intent into exactly ONE of these categories:

1. QUESTION: User wants information, explanations, documentation, best practices
   - Examples: "How do I request GPUs?", "What are storage options?", "Explain ingress"

2. CODE_REQUEST: User wants YAML templates, configuration examples, deployment code
   - Examples: "Create a deployment YAML", "Show me GPU pod template", "Generate ingress config"

3. COMMAND: User wants to execute Kubernetes operations (list, describe, delete, create)
   - Examples: "list my pods", "describe deployment xyz", "delete service abc", "create namespace"

4. UNCLEAR: Intent is ambiguous or unclear

Respond with JSON only:
{
    "intent": "QUESTION|CODE_REQUEST|COMMAND|UNCLEAR",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "keywords": ["extracted", "keywords"]
}"""

        user_prompt = f'Classify this input: "{user_input}"'

        try:
            response = self.glm_client.client.invoke(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}]
            )

            response_content = response.content.strip()

            # Handle GLM-V response format with wrapper tokens
            if response_content.startswith('<|begin_of_box|>'):
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    response_content = response_content[json_start:json_end]

            import json
            result = json.loads(response_content)

            intent_type = IntentType(result["intent"].lower())
            confidence_level = self._map_confidence(result["confidence"])

            return AgentRequest(
                user_input=user_input,
                intent_type=intent_type,
                confidence=confidence_level,
                context={
                    "reasoning": result["reasoning"],
                    "keywords": result.get("keywords", []),
                    "classifier": "glm-v"
                }
            )

        except Exception as e:
            print(f"[!] GLM-V parsing failed: {e}")
            return self._classify_with_fallback(user_input)

    def _classify_with_fallback(self, user_input: str) -> AgentRequest:
        """Fallback classification using keyword analysis."""

        input_lower = user_input.lower()

        # Define keyword patterns for each intent type
        patterns = {
            IntentType.COMMAND: {
                'keywords': ['list', 'get', 'describe', 'delete', 'create', 'apply',
                           'logs', 'exec', 'scale', 'restart', 'rollout', 'port-forward'],
                'patterns': [r'\b(kubectl|k8s)\b', r'\bmy (pods|services|deployments)\b',
                           r'\b(describe|get|delete|list)\s+(pod|service|deployment|job|configmap|secret|pvc)\b',
                           r'\b(pod|service|deployment)\s+\w+']
            },
            IntentType.CODE_REQUEST: {
                'keywords': ['yaml', 'template', 'example', 'generate', 'create yaml',
                           'show me', 'deployment config', 'manifest', 'configuration'],
                'patterns': [r'\b(yaml|template|example)\b', r'(show|create|generate).*(yaml|config|template)']
            },
            IntentType.QUESTION: {
                'keywords': ['how', 'what', 'why', 'when', 'where', 'explain', 'help',
                           'best practice', 'guide', 'tutorial', 'documentation', 'how do i',
                           'how to', 'shared memory', 'shm'],
                'patterns': [
                    r'\bhow\s+do\s+i\b',  # "How do I..." gets highest priority
                    r'\bhow\s+to\b',      # "How to..." also high priority
                    r'\b(how|what|why|when|where)\b',
                    r'\b(explain|help|guide)\b',
                    r'shared\s+memory',   # Specific shared memory questions
                    r'\bshm\b'            # Shared memory abbreviation
                ]
            }
        }

        # Score each intent type
        scores = {}
        matched_keywords = {}

        for intent_type, config in patterns.items():
            score = 0
            keywords = []

            # Keyword matching
            for keyword in config['keywords']:
                if keyword in input_lower:
                    score += 1
                    keywords.append(keyword)

            # Pattern matching (weighted higher)
            for pattern in config['patterns']:
                if re.search(pattern, input_lower):
                    # Give extra weight to specific pattern types
                    if intent_type == IntentType.COMMAND and any(cmd in pattern for cmd in ['describe', 'get', 'delete', 'list']):
                        score += 5  # Strong k8s command indicator
                    elif intent_type == IntentType.QUESTION and pattern in [r'\bhow\s+do\s+i\b', r'\bhow\s+to\b']:
                        score += 4  # Strong documentation question indicator
                    elif intent_type == IntentType.QUESTION and pattern in [r'shared\s+memory', r'\bshm\b']:
                        score += 3  # Specific documentation topic
                    else:
                        score += 2  # Standard pattern match
                    keywords.append(f"pattern:{pattern}")

            scores[intent_type] = score
            matched_keywords[intent_type] = keywords

        # Determine best match
        if not any(scores.values()):
            # No matches found
            intent_type = IntentType.UNCLEAR
            confidence = 0.2
            reasoning = "No clear intent indicators found"
            keywords = []
        else:
            # Get highest scoring intent
            intent_type = max(scores, key=scores.get)
            max_score = scores[intent_type]
            keywords = matched_keywords[intent_type]

            # Calculate confidence based on score and clarity
            total_possible = max(len(patterns[intent_type]['keywords']) +
                               len(patterns[intent_type]['patterns']) * 2, 1)
            confidence = min(0.9, max_score / total_possible + 0.3)

            reasoning = f"Matched {max_score} indicators: {', '.join(keywords[:3])}"

        confidence_level = self._map_confidence(confidence)

        return AgentRequest(
            user_input=user_input,
            intent_type=intent_type,
            confidence=confidence_level,
            context={
                "reasoning": reasoning,
                "keywords": keywords,
                "classifier": "fallback",
                "scores": {k.value: v for k, v in scores.items()}
            }
        )

    def _map_confidence(self, confidence_score: float) -> ConfidenceLevel:
        """Map numeric confidence to confidence level enum."""
        if confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCLEAR

    def should_clarify(self, request: AgentRequest) -> bool:
        """Determine if clarification is needed before routing."""
        return (
            request.intent_type == IntentType.UNCLEAR or
            request.confidence == ConfidenceLevel.UNCLEAR or
            (request.confidence == ConfidenceLevel.LOW and
             not request.context.get("keywords"))
        )

    def generate_clarification(self, request: AgentRequest) -> str:
        """Generate clarification request for unclear intents."""

        if request.intent_type == IntentType.UNCLEAR:
            return """I'm not sure what you'd like to do. Please specify:

**For Information/Questions:**
- "How do I request GPUs on NRP?"
- "What are the storage options?"
- "Explain Kubernetes networking"

**For Code/Templates:**
- "Create a GPU deployment YAML"
- "Show me ingress template"
- "Generate service configuration"

**For Operations:**
- "list my pods"
- "describe deployment myapp"
- "delete service xyz"
"""

        reasoning = request.context.get("reasoning", "")
        keywords = request.context.get("keywords", [])

        return f"""Your request is unclear. {reasoning}

Based on the keywords I found: {', '.join(keywords[:3]) if keywords else 'none'}

Please be more specific:
- For **questions**: Start with "How", "What", "Explain"
- For **code/templates**: Use "create", "generate", "show me YAML"
- For **operations**: Use "list", "describe", "delete", "get"
"""

    def get_routing_summary(self, request: AgentRequest) -> str:
        """Get a summary of the routing decision."""
        agent_map = {
            IntentType.QUESTION: "INFOGENT Agent (information gathering)",
            IntentType.CODE_REQUEST: "Code Generator Agent (template creation)",
            IntentType.COMMAND: "K8s Operations Agent (kubectl operations)",
            IntentType.UNCLEAR: "Clarification needed"
        }

        agent_target = agent_map.get(request.intent_type, "Unknown")

        return f"""[Intent Router]
Intent: {request.intent_type.value}
Confidence: {request.confidence.value}
Routing to: {agent_target}
Reasoning: {request.context.get('reasoning', 'N/A')}"""


def init_intent_router() -> IntentRouter:
    """Initialize the intent router."""
    return IntentRouter()