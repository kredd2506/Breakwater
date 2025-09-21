#!/usr/bin/env python3
"""
Agent Type Definitions
=====================

Defines the core agent types and interfaces for the NRP K8s System.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


class IntentType(Enum):
    """Types of user intents."""
    QUESTION = "question"           # Information/explanation request → INFOGENT Agent
    CODE_REQUEST = "code_request"   # Template/example generation → Code Generator Agent
    COMMAND = "command"             # K8s operations → K8s Operations Agent
    UNCLEAR = "unclear"             # Needs clarification


class ConfidenceLevel(Enum):
    """Confidence levels for agent decisions."""
    HIGH = "high"       # > 0.8 - Execute directly
    MEDIUM = "medium"   # 0.6-0.8 - Execute with confirmation
    LOW = "low"         # 0.4-0.6 - Request clarification
    UNCLEAR = "unclear" # < 0.4 - Route to clarification


@dataclass
class AgentRequest:
    """Standard request format for all agents."""
    user_input: str
    intent_type: IntentType
    confidence: ConfidenceLevel
    context: Dict[str, Any]


@dataclass
class AgentResponse:
    """Standard response format from all agents."""
    success: bool
    content: str
    agent_type: str
    confidence: ConfidenceLevel
    metadata: Dict[str, Any]
    follow_up_suggestions: List[str]


class BaseAgent(ABC):
    """Base interface for all agents."""

    @abstractmethod
    def can_handle(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the request."""
        pass

    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process the request and return response."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        pass