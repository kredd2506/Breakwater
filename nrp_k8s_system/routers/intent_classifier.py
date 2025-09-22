#!/usr/bin/env python3
"""
Intent Classification Module for NRP K8s System
===============================================

Classifies user input to determine if it's a command or explanation request.
Uses LLM-based classification with keyword-based fallback.
"""

import json
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

from ..core.nrp_init import init_chat_model
from ..utils.validation import sanitize_input


class UserIntent(Enum):
    COMMAND = "command"        # K8s operational commands (list, get, create, etc.)
    EXPLANATION = "explanation" # Documentation, how-to questions
    UNCLEAR = "unclear"        # Ambiguous intent


@dataclass
class RouterDecision:
    intent: UserIntent
    confidence: float
    reasoning: str
    suggested_handler: str


def classify_user_intent(user_input: str) -> RouterDecision:
    """
    Classify user input to determine if it's a command or explanation request.

    Args:
        user_input: Raw user input string

    Returns:
        RouterDecision with classification results
    """
    # Sanitize input first
    clean_input = sanitize_input(user_input)

    try:
        print("[*] Analyzing user intent...")
        chat_model = init_chat_model()

        classification_prompt = f"""
You are an intelligent router for an NRP (National Research Platform) + Kubernetes system.
Analyze the user input and classify their intent.

User Input: "{clean_input}"

INTENT CATEGORIES:
1. COMMAND: User wants to execute a Kubernetes operation
   - Examples: "list pods", "get my services", "delete pod xyz", "show deployments"
   - Keywords: list, get, show, delete, create, apply, describe, logs, exec
   - Action-oriented requests for current cluster state or operations

2. EXPLANATION: User wants documentation, guidance, or how-to information
   - Examples: "How do I request GPUs?", "What are best practices for storage?"
   - Questions about setup, configuration, troubleshooting, best practices
   - Learning-oriented requests for knowledge and guidance

Respond with JSON only:
{{
    "intent": "command" or "explanation" or "unclear",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification decision",
    "suggested_handler": "k8s_operations" or "nrp_hybrid" or "clarification_needed"
}}
"""

        response = chat_model.invoke(classification_prompt)

        # Parse JSON response
        try:
            result = json.loads(response.content.strip())
            return RouterDecision(
                intent=UserIntent(result["intent"]),
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                suggested_handler=result["suggested_handler"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[!] Error parsing classification result: {e}")
            return _fallback_classification(clean_input)

    except Exception as e:
        print(f"[!] Error in intent classification: {e}")
        return _fallback_classification(clean_input)


def _fallback_classification(user_input: str) -> RouterDecision:
    """
    Fallback classification using simple keyword matching.

    Args:
        user_input: Clean user input string

    Returns:
        RouterDecision based on keyword analysis
    """
    input_lower = user_input.lower()

    # Command keywords
    command_keywords = [
        'list', 'get', 'show', 'describe', 'delete', 'create', 'apply',
        'exec', 'logs', 'scale', 'restart', 'rollout', 'port-forward',
        'deploy', 'remove', 'pod', 'deployment', 'events', 'permissions',
        'template', 'yaml'
    ]

    # Question keywords
    question_keywords = [
        'how', 'what', 'why', 'when', 'where', 'best practice',
        'guide', 'tutorial', 'help', 'explain', 'setup', 'configure',
        'can i', 'should i', 'is it safe', 'allowed', 'policy'
    ]

    command_score = sum(1 for kw in command_keywords if kw in input_lower)
    question_score = sum(1 for kw in question_keywords if kw in input_lower)

    if command_score > question_score:
        matching_keywords = [kw for kw in command_keywords if kw in input_lower]
        return RouterDecision(
            intent=UserIntent.COMMAND,
            confidence=0.7,
            reasoning=f"Contains command keywords: {matching_keywords}",
            suggested_handler="k8s_operations"
        )
    elif question_score > 0:
        matching_keywords = [kw for kw in question_keywords if kw in input_lower]
        return RouterDecision(
            intent=UserIntent.EXPLANATION,
            confidence=0.7,
            reasoning=f"Contains question keywords: {matching_keywords}",
            suggested_handler="nrp_hybrid"
        )
    else:
        return RouterDecision(
            intent=UserIntent.UNCLEAR,
            confidence=0.3,
            reasoning="No clear indicators of command or question intent",
            suggested_handler="clarification_needed"
        )


def get_classification_confidence_threshold() -> float:
    """Get the minimum confidence threshold for classification decisions."""
    return 0.6


def should_request_clarification(decision: RouterDecision) -> bool:
    """Determine if clarification should be requested from user."""
    return (decision.intent == UserIntent.UNCLEAR or
            decision.confidence < get_classification_confidence_threshold())