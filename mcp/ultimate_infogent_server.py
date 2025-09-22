#!/usr/bin/env python3
"""
Ultimate Infogent Server - Navigator-Extractor-Aggregator + GLM-4.5V
===================================================================
This is our painfully developed infogent architecture with GLM-4.5V integration.

Architecture Components:
1. Navigator: Intelligent discovery and routing using GLM-4.5V
2. Extractor: Precise content extraction from comprehensive anchor database
3. Aggregator: Synthesis of comprehensive responses with examples and warnings
"""

import os
import sys
import json
import uuid
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import NRP knowledge bases
try:
    from cache.nrp_ultra_complete_anchor_db import search_complete_anchors, NRP_COMPLETE_ANCHORS
    NRP_KNOWLEDGE_AVAILABLE = True
    print(f"[OK] NRP knowledge base loaded: {len(NRP_COMPLETE_ANCHORS)} pages")
except ImportError as e:
    print(f"[WARNING] Could not import NRP knowledge: {e}")
    NRP_KNOWLEDGE_AVAILABLE = False

# GLM-4.5V Integration
try:
    from dotenv import load_dotenv
    load_dotenv()
    from openai import AsyncOpenAI

    glm_client = AsyncOpenAI(
        api_key=os.getenv("NRP_API_KEY"),
        base_url=os.getenv("NRP_BASE_URL", "https://ellm.nrp-nautilus.io/v1")
    )
    GLM_V_AVAILABLE = True
    print("[OK] GLM-4.5V multimodal client initialized")
except ImportError as e:
    print(f"[WARNING] GLM-4.5V not available: {e}")
    GLM_V_AVAILABLE = False
    glm_client = None

# FastMCP Server
mcp = FastMCP("Ultimate Infogent NRP K8s Server")

# =============================================================================
# INFOGENT ARCHITECTURE: NAVIGATOR-EXTRACTOR-AGGREGATOR
# =============================================================================

class IntelligentNavigator:
    """Navigator Agent: Analyzes queries and provides intelligent routing"""

    @staticmethod
    async def analyze_query(query: str, context: str = "") -> Dict[str, Any]:
        """Use GLM-4.5V to analyze query and provide navigation guidance"""
        if not GLM_V_AVAILABLE:
            return {
                "status": "fallback",
                "technical_depth": "intermediate",
                "query_type": "general",
                "enhanced_keywords": []
            }

        try:
            navigation_prompt = f"""Analyze this NRP Nautilus query and provide navigation guidance:

Query: "{query}"
Context: "{context}"

Analyze and respond with JSON containing:
{{
    "technical_depth": "basic|intermediate|advanced",
    "query_type": "gpu_specific|storage|networking|general|kubernetes_ops",
    "specific_requirements": ["list key technical requirements"],
    "enhanced_keywords": ["search optimization keywords"],
    "user_intent": "learning|troubleshooting|implementation|reference"
}}

Consider:
- GPU-specific queries (A100, H100, etc.) need special handling
- Technical depth determines explanation complexity
- Enhanced keywords improve search precision"""

            response = await glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are an expert navigator for NRP documentation. Respond only with valid JSON."},
                    {"role": "user", "content": navigation_prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )

            nav_analysis = json.loads(response.choices[0].message.content)
            nav_analysis["status"] = "success"
            return nav_analysis

        except Exception as e:
            print(f"[NAVIGATOR] Error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "technical_depth": "intermediate",
                "query_type": "general",
                "enhanced_keywords": []
            }

class PrecisionExtractor:
    """Extractor Agent: Finds precise documentation matches"""

    @staticmethod
    async def extract_precise_match(query: str, nav_analysis: Dict) -> Dict[str, Any]:
        """Extract precise documentation match based on navigation analysis"""
        if not NRP_KNOWLEDGE_AVAILABLE:
            return {
                "status": "error",
                "error": "NRP knowledge base not available",
                "fallback_url": "https://nrp.ai/documentation/"
            }

        try:
            # Build enhanced search query
            enhanced_query = query

            # Add navigation keywords
            if nav_analysis.get("enhanced_keywords"):
                enhanced_query += " " + " ".join(nav_analysis["enhanced_keywords"])

            # Special handling for GPU-specific queries
            if nav_analysis.get("query_type") == "gpu_specific" or any(gpu in query.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                enhanced_query += " special GPU type specific"

            # Search for matches
            matches = search_complete_anchors(enhanced_query)

            if matches:
                best_match = matches[0]

                # Advanced matching: prefer special GPU sections for GPU queries
                if nav_analysis.get("query_type") == "gpu_specific":
                    for match in matches:
                        if any(keyword in match['anchor'].lower() for keyword in ['special', 'specific', 'type']):
                            best_match = match
                            break

                return {
                    "status": "success",
                    "precise_match": best_match,
                    "exact_url": best_match['url'],
                    "relevance_score": best_match['relevance'],
                    "alternative_matches": matches[1:5],
                    "search_strategy": "enhanced_with_navigation"
                }
            else:
                return {
                    "status": "no_matches",
                    "fallback_url": "https://nrp.ai/documentation/",
                    "search_query": enhanced_query
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_url": "https://nrp.ai/documentation/"
            }

class ComprehensiveAggregator:
    """Aggregator Agent: Synthesizes comprehensive responses with GLM-4.5V"""

    @staticmethod
    async def synthesize_response(query: str, nav_analysis: Dict, extraction_result: Dict) -> str:
        """Generate comprehensive response using all infogent intelligence"""
        if not GLM_V_AVAILABLE:
            return f"""# Basic Response (GLM-4.5V Unavailable)

Query: {query}
Documentation: {extraction_result.get('exact_url', 'https://nrp.ai/documentation/')}

Please visit the documentation link for detailed information.

*Navigator-Extractor-Aggregator pipeline active, but GLM-4.5V synthesis unavailable*"""

        try:
            # Extract context from results
            precise_url = extraction_result.get("exact_url", "https://nrp.ai/documentation/")
            match_info = extraction_result.get("precise_match", {})
            technical_depth = nav_analysis.get("technical_depth", "intermediate")
            query_type = nav_analysis.get("query_type", "general")
            user_intent = nav_analysis.get("user_intent", "learning")

            # Build specialized guidance based on query type
            specialized_guidance = ""
            if query_type == "gpu_specific":
                specialized_guidance = """

CRITICAL GPU SPECIFICATIONS:
- MUST include exact resource syntax: nvidia.com/a100, nvidia.com/h100, nvidia.com/v100, nvidia.com/rtx4090
- Explain node selection and GPU type differences
- Detail resource limits, quotas, and availability constraints
- Include scheduling considerations and performance characteristics
- Provide troubleshooting for GPU allocation failures"""

            elif query_type == "storage":
                specialized_guidance = """

STORAGE REQUIREMENTS:
- Detail PVC specifications and storage class options
- Include volume mounting examples and permissions
- Explain persistent vs ephemeral storage trade-offs
- Provide backup and data persistence strategies"""

            elif query_type == "networking":
                specialized_guidance = """

NETWORKING SPECIFICATIONS:
- Include service types and ingress configuration
- Detail port management and security considerations
- Explain load balancing and traffic routing
- Provide DNS and external access patterns"""

            # Adapt depth based on user intent and technical level
            depth_instructions = {
                "basic": "Focus on step-by-step instructions with simple explanations and minimal prerequisites",
                "intermediate": "Provide comprehensive guidance with examples, best practices, and moderate detail",
                "advanced": "Include advanced configurations, optimization techniques, and comprehensive troubleshooting"
            }.get(technical_depth, "Provide comprehensive guidance")

            intent_focus = {
                "learning": "Focus on educational value with clear explanations and learning progression",
                "troubleshooting": "Emphasize problem diagnosis, common issues, and step-by-step resolution",
                "implementation": "Provide ready-to-use configurations with practical examples",
                "reference": "Include comprehensive technical details and all relevant options"
            }.get(user_intent, "Provide practical guidance")

            # Generate comprehensive synthesis
            synthesis_prompt = f"""You are an expert NRP Nautilus platform specialist. Generate a comprehensive response for: "{query}"

CONTEXT ANALYSIS:
- Technical Depth: {technical_depth}
- Query Type: {query_type}
- User Intent: {user_intent}
- Precise Documentation: {precise_url}
- Page Context: {match_info.get('page', 'NRP Documentation').replace('_', ' ').title()}
- Section Context: {match_info.get('anchor', 'General').replace('-', ' ').title()}

RESPONSE REQUIREMENTS:
{depth_instructions}
{intent_focus}

MUST INCLUDE:
1. Clear, detailed explanation of the topic
2. Complete step-by-step instructions when applicable
3. Full YAML/code examples with correct syntax and formatting
4. Best practices with specific warnings about common pitfalls
5. Related concepts and prerequisite knowledge
6. Comprehensive troubleshooting guidance with specific error scenarios
7. Platform-specific considerations for NRP Nautilus{specialized_guidance}

QUALITY STANDARDS:
- Leverage your 65,536 token context for depth and completeness
- Provide actionable guidance that goes beyond documentation
- Include specific, tested examples relevant to NRP Nautilus
- Address both immediate query and related concepts for complete understanding
- Use clear formatting with proper sections and code blocks

Generate a response that represents the pinnacle of technical documentation assistance."""

            response = await glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are the ultimate NRP Nautilus Kubernetes platform expert with comprehensive knowledge of all documentation, policies, and best practices. Generate responses that set the gold standard for technical assistance."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            comprehensive_response = response.choices[0].message.content

            # Format final infogent response
            return f"""# NRP Nautilus Documentation - Infogent Architecture Response

## Query Analysis
**Query**: {query}
**Technical Depth**: {technical_depth.title()}
**Query Type**: {query_type.replace('_', ' ').title()}
**User Intent**: {user_intent.title()}

## Precise Documentation Match
**Direct Link**: {precise_url}
**Page Context**: {match_info.get('page', 'NRP Documentation').replace('_', ' ').title()}
**Section Context**: {match_info.get('anchor', 'General').replace('-', ' ').title()}
**Relevance Score**: {extraction_result.get('relevance_score', 'N/A')}

## Comprehensive Expert Response
{comprehensive_response}

## Navigation Intelligence
- **Search Strategy**: {extraction_result.get('search_strategy', 'Standard')}
- **Alternative References**: {len(extraction_result.get('alternative_matches', []))} related sections available
- **Knowledge Base Coverage**: {len(NRP_COMPLETE_ANCHORS) if NRP_KNOWLEDGE_AVAILABLE else 'N/A'} pages analyzed

---
*Response generated by Advanced Infogent Architecture*
*🧭 Navigator → 🔍 Extractor → 📝 Aggregator pipeline*
*Powered by GLM-4.5V multimodal AI (65,536 token context)*"""

        except Exception as e:
            return f"""# Infogent Synthesis Error

An error occurred during comprehensive response generation: {str(e)}

**Query**: {query}
**Precise Documentation**: {precise_url}
**Navigation Analysis**: {nav_analysis.get('status', 'Unknown')}
**Extraction Status**: {extraction_result.get('status', 'Unknown')}

**Fallback**: Please check the documentation link above for detailed information.

*Error in Navigator-Extractor-Aggregator synthesis pipeline*"""

# =============================================================================
# MAIN INFOGENT QUERY TOOL
# =============================================================================

class QueryParams(BaseModel):
    query: str = Field(description="Natural language query about NRP Nautilus or Kubernetes")
    context: str = Field(default="", description="Additional context for the query")

@mcp.tool()
async def infogent_intelligent_query(params: QueryParams) -> str:
    """
    Ultimate infogent query processing using Navigator-Extractor-Aggregator architecture.

    This is our painfully developed multi-agent system that provides:
    🧭 Navigator: Intelligent query analysis and routing
    🔍 Extractor: Precise documentation matching
    📝 Aggregator: Comprehensive synthesis with GLM-4.5V
    """

    print(f"[INFOGENT] Starting Navigator-Extractor-Aggregator pipeline...")
    print(f"[INFOGENT] Query: {params.query[:50]}...")

    try:
        # Stage 1: Navigator - Intelligent Query Analysis
        print("[🧭 NAVIGATOR] Analyzing query intelligence...")
        nav_analysis = await IntelligentNavigator.analyze_query(params.query, params.context)

        if nav_analysis.get("status") == "error":
            print(f"[🧭 NAVIGATOR] Warning: {nav_analysis.get('error')}")
        else:
            print(f"[🧭 NAVIGATOR] Analysis complete - Depth: {nav_analysis.get('technical_depth')}, Type: {nav_analysis.get('query_type')}")

        # Stage 2: Extractor - Precise Content Extraction
        print("[🔍 EXTRACTOR] Extracting precise documentation match...")
        extraction_result = await PrecisionExtractor.extract_precise_match(params.query, nav_analysis)

        if extraction_result.get("status") == "success":
            print(f"[🔍 EXTRACTOR] Match found - Relevance: {extraction_result.get('relevance_score')}")
        else:
            print(f"[🔍 EXTRACTOR] {extraction_result.get('status', 'Unknown')}: {extraction_result.get('error', 'No matches')}")

        # Stage 3: Aggregator - Comprehensive Synthesis
        print("[📝 AGGREGATOR] Synthesizing comprehensive response...")
        final_response = await ComprehensiveAggregator.synthesize_response(
            params.query, nav_analysis, extraction_result
        )

        print("[INFOGENT] Pipeline complete - Navigator → Extractor → Aggregator")
        return final_response

    except Exception as e:
        error_response = f"""# Infogent Pipeline Error

Critical error in Navigator-Extractor-Aggregator architecture: {str(e)}

**Pipeline Status:**
🧭 Navigator: Advanced query analysis with GLM-4.5V
🔍 Extractor: Precision matching with {len(NRP_COMPLETE_ANCHORS) if NRP_KNOWLEDGE_AVAILABLE else 'N/A'} page database
📝 Aggregator: Comprehensive synthesis with multimodal AI

**System Health:**
- GLM-4.5V Integration: {'✓ Available' if GLM_V_AVAILABLE else '✗ Unavailable'}
- NRP Knowledge Base: {'✓ Available' if NRP_KNOWLEDGE_AVAILABLE else '✗ Unavailable'}

**Emergency Fallback**: https://nrp.ai/documentation/

*This represents a failure of our advanced infogent architecture*"""

        print(f"[INFOGENT] CRITICAL ERROR: {str(e)}")
        return error_response

# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 ULTIMATE INFOGENT SERVER - NAVIGATOR-EXTRACTOR-AGGREGATOR")
    print("Painfully Developed Multi-Agent Architecture + GLM-4.5V")
    print("=" * 80)

    print("\n[COMPONENT STATUS]")
    print(f"🧭 Navigator (GLM-4.5V Analysis): {'✓ Available' if GLM_V_AVAILABLE else '✗ Unavailable'}")
    print(f"🔍 Extractor (Precision Matching): {'✓ Available' if NRP_KNOWLEDGE_AVAILABLE else '✗ Unavailable'}")
    print(f"📝 Aggregator (GLM-4.5V Synthesis): {'✓ Available' if GLM_V_AVAILABLE else '✗ Unavailable'}")

    if NRP_KNOWLEDGE_AVAILABLE:
        print(f"📊 Knowledge Base: {len(NRP_COMPLETE_ANCHORS)} pages, comprehensive anchor coverage")

    if not all([GLM_V_AVAILABLE, NRP_KNOWLEDGE_AVAILABLE]):
        print("\n⚠️  [WARNING] Some components unavailable - infogent functionality may be limited")
    else:
        print("\n✅ [SUCCESS] Full infogent architecture operational")

    print(f"\n[STARTING] Ultimate infogent server on port 8026...")
    mcp.run(port=8026)