#!/usr/bin/env python3
"""
INFOGENT Bridge for Intent Agent Integration
==========================================

Integrates the Intent Agent with the existing Navigator → Extractor → Aggregator
architecture from the INFOGENT system for enhanced information discovery.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .intent_agent import IntentAgent, AgentDecision, IntentConfidence
from ..routers.intent_classifier import UserIntent
from ..systems.qain import Controller, Navigator, Extractor, Aggregator, Query


@dataclass
class InfogentRequest:
    """Request structure for INFOGENT system integration."""
    query: str
    intent: UserIntent
    confidence: IntentConfidence
    context: Dict[str, Any]
    search_type: str  # "documentation", "troubleshooting", "best_practices", etc.


@dataclass
class EnhancedResponse:
    """Enhanced response combining intent classification with INFOGENT results."""
    original_decision: AgentDecision
    infogent_results: Optional[Dict[str, Any]]
    final_recommendation: str
    confidence_boost: float
    additional_context: Dict[str, Any]


class InfogentBridge:
    """
    Bridge between Intent Agent and INFOGENT system.

    This class enhances intent classification by leveraging the Navigator/Extractor/Aggregator
    pattern when additional information is needed, especially for explanation requests.
    """

    def __init__(self):
        self.intent_agent = IntentAgent()
        self.infogent_controller = Controller()

    def analyze_with_infogent(self, user_input: str) -> EnhancedResponse:
        """
        Perform intent analysis enhanced with INFOGENT system capabilities.

        Args:
            user_input: Raw user input string

        Returns:
            EnhancedResponse with comprehensive analysis and recommendations
        """
        # First, get initial intent classification
        initial_decision = self.intent_agent.analyze_intent(user_input)

        # Determine if INFOGENT enhancement is needed
        if self._should_use_infogent(initial_decision):
            infogent_request = self._create_infogent_request(user_input, initial_decision)
            infogent_results = self._query_infogent(infogent_request)

            # Enhance the decision with INFOGENT results
            enhanced_response = self._enhance_decision(initial_decision, infogent_results)
            return enhanced_response
        else:
            # Return decision without INFOGENT enhancement
            return EnhancedResponse(
                original_decision=initial_decision,
                infogent_results=None,
                final_recommendation=self._generate_recommendation(initial_decision),
                confidence_boost=0.0,
                additional_context={}
            )

    def _should_use_infogent(self, decision: AgentDecision) -> bool:
        """Determine if INFOGENT system should be used to enhance the decision."""
        return (
            # Use for explanation requests
            decision.intent == UserIntent.EXPLANATION or
            # Use when confidence is low and we need more context
            decision.confidence in [IntentConfidence.LOW, IntentConfidence.UNCLEAR] or
            # Use when clarification is needed but we might find answers
            (decision.clarification_needed and "how" in decision.reasoning.lower())
        )

    def _create_infogent_request(self, user_input: str, decision: AgentDecision) -> InfogentRequest:
        """Create an INFOGENT request based on the intent analysis."""

        # Extract search terms and determine search type
        search_type = self._determine_search_type(user_input, decision)

        # Enhance query with context from tool calls
        enhanced_query = self._enhance_query(user_input, decision)

        return InfogentRequest(
            query=enhanced_query,
            intent=decision.intent,
            confidence=decision.confidence,
            context=decision.context_gathered,
            search_type=search_type
        )

    def _determine_search_type(self, user_input: str, decision: AgentDecision) -> str:
        """Determine the type of search to perform in INFOGENT."""
        input_lower = user_input.lower()

        # Map keywords to search types
        search_type_keywords = {
            "documentation": ["docs", "documentation", "manual", "guide"],
            "troubleshooting": ["error", "problem", "issue", "troubleshoot", "debug", "fix"],
            "best_practices": ["best practice", "recommendation", "should", "optimal", "advice"],
            "gpu": ["gpu", "graphics", "cuda", "nvidia"],
            "storage": ["storage", "volume", "pvc", "persistent", "disk"],
            "networking": ["network", "service", "ingress", "port", "connection"],
            "security": ["security", "rbac", "permission", "auth", "ssl", "tls"]
        }

        for search_type, keywords in search_type_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return search_type

        # Default based on intent
        if decision.intent == UserIntent.EXPLANATION:
            return "documentation"
        else:
            return "general"

    def _enhance_query(self, user_input: str, decision: AgentDecision) -> str:
        """Enhance the search query with context from intent analysis."""
        enhanced_query = user_input

        # Add K8s context if this is a command that failed
        if decision.intent == UserIntent.COMMAND and decision.confidence == IntentConfidence.LOW:
            enhanced_query += " kubernetes NRP Nautilus"

        # Add specific context based on tool calls
        for tool_call in decision.tool_calls:
            if tool_call["name"] == "list_k8s_resources":
                resource_type = tool_call.get("args", {}).get("resource_type", "")
                enhanced_query += f" {resource_type} NRP"

        # Add clarification context
        if decision.clarification_needed:
            enhanced_query += " tutorial example guide"

        return enhanced_query

    def _query_infogent(self, request: InfogentRequest) -> Optional[Dict[str, Any]]:
        """Query the INFOGENT system for additional context."""
        try:
            # Create query for INFOGENT
            query = Query(q=request.query)

            # Use INFOGENT Controller to orchestrate the pipeline
            result = self.infogent_controller.run(query)

            return {
                "search_query": request.query,
                "search_type": request.search_type,
                "results": result,
                "urls_searched": getattr(result, 'sources', []),
                "facts_extracted": getattr(result, 'facts', []),
                "confidence": getattr(result, 'confidence', 0.5)
            }

        except Exception as e:
            print(f"[!] INFOGENT query failed: {e}")
            return None

    def _enhance_decision(self, original_decision: AgentDecision, infogent_results: Optional[Dict[str, Any]]) -> EnhancedResponse:
        """Enhance the original decision with INFOGENT results."""
        if not infogent_results:
            return EnhancedResponse(
                original_decision=original_decision,
                infogent_results=None,
                final_recommendation=self._generate_recommendation(original_decision),
                confidence_boost=0.0,
                additional_context={}
            )

        # Calculate confidence boost based on INFOGENT results quality
        confidence_boost = self._calculate_confidence_boost(infogent_results)

        # Generate enhanced recommendation
        final_recommendation = self._generate_enhanced_recommendation(
            original_decision, infogent_results
        )

        # Extract additional context
        additional_context = {
            "sources": infogent_results.get("urls_searched", []),
            "facts": infogent_results.get("facts_extracted", []),
            "search_confidence": infogent_results.get("confidence", 0.0)
        }

        return EnhancedResponse(
            original_decision=original_decision,
            infogent_results=infogent_results,
            final_recommendation=final_recommendation,
            confidence_boost=confidence_boost,
            additional_context=additional_context
        )

    def _calculate_confidence_boost(self, infogent_results: Dict[str, Any]) -> float:
        """Calculate how much INFOGENT results boost our confidence."""
        if not infogent_results:
            return 0.0

        # Factors that increase confidence
        factors = []

        # Number of relevant results
        results_count = len(infogent_results.get("results", []))
        if results_count > 0:
            factors.append(min(0.2, results_count * 0.05))

        # Quality of extracted facts
        facts_count = len(infogent_results.get("facts_extracted", []))
        if facts_count > 0:
            factors.append(min(0.15, facts_count * 0.03))

        # INFOGENT's own confidence
        search_confidence = infogent_results.get("confidence", 0.0)
        factors.append(search_confidence * 0.25)

        return sum(factors)

    def _generate_recommendation(self, decision: AgentDecision) -> str:
        """Generate a recommendation based on intent decision alone."""
        if decision.intent == UserIntent.COMMAND:
            if decision.confidence == IntentConfidence.HIGH:
                return "Execute the Kubernetes command using the K8s operations handler."
            else:
                return "Verify the command details and available resources before execution."

        elif decision.intent == UserIntent.EXPLANATION:
            return "Provide comprehensive explanation using NRP documentation and examples."

        else:
            return "Request clarification from the user with specific examples."

    def _generate_enhanced_recommendation(self, decision: AgentDecision, infogent_results: Dict[str, Any]) -> str:
        """Generate enhanced recommendation using both intent analysis and INFOGENT results."""
        base_recommendation = self._generate_recommendation(decision)

        if not infogent_results or not infogent_results.get("results"):
            return base_recommendation

        # Enhance with INFOGENT findings
        facts = infogent_results.get("facts_extracted", [])
        sources = infogent_results.get("urls_searched", [])

        enhancement = ""
        if facts:
            enhancement += f" Found {len(facts)} relevant facts from documentation."

        if sources:
            enhancement += f" Consulted {len(sources)} authoritative sources."

        enhanced_recommendation = base_recommendation + enhancement

        # Add specific guidance based on search type
        search_type = infogent_results.get("search_type", "general")
        if search_type == "troubleshooting":
            enhanced_recommendation += " Focus on diagnostic steps and common solutions."
        elif search_type == "best_practices":
            enhanced_recommendation += " Emphasize recommended approaches and potential pitfalls."
        elif search_type in ["gpu", "storage", "networking"]:
            enhanced_recommendation += f" Include {search_type}-specific configuration examples."

        return enhanced_recommendation


# Remove stub classes since we're using the actual INFOGENT implementation


def init_infogent_bridge() -> InfogentBridge:
    """Initialize the INFOGENT bridge."""
    return InfogentBridge()