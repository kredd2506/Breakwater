#!/usr/bin/env python3
"""
Ultimate Advanced Infogent Server with GLM-4.5V
==============================================
Combines our painfully developed navigator-extractor-aggregator architecture
with GLM-4.5V multimodal AI for comprehensive NRP K8s responses.

Architecture:
- Navigator: Discovers and maps documentation structure
- Extractor: Processes content with intelligent parsing
- Aggregator: Organizes and synthesizes information
- GLM-4.5V: Generates comprehensive explanations with examples
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

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))
# Add the nrp_k8s_system path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import our advanced components
try:
    from core.tools.advanced_infogent_server import (
        WebNavigator, ContentExtractor, ContentAggregator,
        ContentType, ContentItem
    )
    INFOGENT_AVAILABLE = True
    print("[OK] Advanced infogent components loaded")
except ImportError as e:
    print(f"[WARNING] Could not import infogent components: {e}")
    INFOGENT_AVAILABLE = False

# Import NRP knowledge bases
try:
    from cache.nrp_ultra_complete_anchor_db import search_ultra_complete_anchors, NRP_ULTRA_COMPLETE_ANCHORS
    NRP_KNOWLEDGE_AVAILABLE = True
    print(f"[OK] NRP knowledge base loaded: {len(NRP_ULTRA_COMPLETE_ANCHORS)} pages")
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

# K8s Integration
try:
    from kubernetes import client, config
    try:
        config.load_incluster_config()
        print("[OK] Using in-cluster Kubernetes configuration")
    except:
        try:
            config.load_kube_config()
            print("[OK] Using local kubectl configuration")
        except:
            print("[WARNING] No Kubernetes configuration found")

    k8s_v1 = client.CoreV1Api()
    k8s_apps_v1 = client.AppsV1Api()
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    print("[WARNING] Kubernetes client not available")

# FastMCP Server
mcp = FastMCP("Ultimate Advanced NRP K8s Infogent Server")

# =============================================================================
# ENHANCED INFOGENT AGENTS WITH GLM-4.5V
# =============================================================================

class AdvancedNavigator:
    """Enhanced Navigator with GLM-4.5V intelligence"""

    @staticmethod
    async def intelligent_discovery(query: str, context: str = "") -> Dict[str, Any]:
        """Use GLM-4.5V to intelligently discover relevant content"""
        if not GLM_V_AVAILABLE:
            return {"error": "GLM-4.5V not available for intelligent discovery"}

        try:
            discovery_prompt = f"""You are an expert NRP Nautilus documentation navigator.

Query: "{query}"
Context: "{context}"

Your task is to identify the most relevant documentation sections and concepts for this query. Consider:
1. Specific technical requirements (GPU types, storage, networking)
2. User experience level (beginner vs advanced concepts needed)
3. Related concepts that provide complete understanding
4. Common troubleshooting scenarios

Respond with a JSON object containing:
{{
    "primary_topics": ["list of main topics"],
    "secondary_topics": ["related concepts"],
    "technical_depth": "basic|intermediate|advanced",
    "keywords": ["key terms for precise search"]
}}"""

            response = await glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are an expert NRP documentation navigator. Respond only with valid JSON."},
                    {"role": "user", "content": discovery_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            nav_guidance = json.loads(response.choices[0].message.content)
            return {
                "status": "success",
                "navigation_guidance": nav_guidance,
                "enhanced_keywords": nav_guidance.get("keywords", []),
                "technical_depth": nav_guidance.get("technical_depth", "intermediate")
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback": "basic navigation"
            }

class AdvancedExtractor:
    """Enhanced Extractor with contextual intelligence"""

    @staticmethod
    async def intelligent_extraction(url: str, query: str, nav_guidance: Dict) -> Dict[str, Any]:
        """Extract content with query-specific intelligence"""
        if not NRP_KNOWLEDGE_AVAILABLE:
            return {"error": "NRP knowledge base not available"}

        try:
            # Enhanced search based on navigation guidance
            enhanced_query = query
            if nav_guidance.get("enhanced_keywords"):
                enhanced_query = query + " " + " ".join(nav_guidance["enhanced_keywords"])

            # Special handling for specific GPU types
            if any(gpu in query.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                enhanced_query += " special GPU type specific"

            # Find precise matches
            matches = search_ultra_complete_anchors(enhanced_query)

            if matches:
                best_match = matches[0]

                # Prefer special GPU sections for specific GPU requests
                if any(gpu in query.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                    for match in matches:
                        if 'special' in match['anchor'].lower():
                            best_match = match
                            break

                return {
                    "status": "success",
                    "precise_match": best_match,
                    "exact_url": best_match['url'],
                    "relevance_score": best_match['relevance'],
                    "alternative_matches": matches[1:6],  # Top 5 alternatives
                    "extraction_method": "intelligent_anchor_matching"
                }
            else:
                return {
                    "status": "no_matches",
                    "fallback_url": "https://nrp.ai/documentation/",
                    "extraction_method": "fallback"
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fallback_url": "https://nrp.ai/documentation/"
            }

class AdvancedAggregator:
    """Enhanced Aggregator with GLM-4.5V synthesis"""

    @staticmethod
    async def intelligent_synthesis(query: str, extraction_result: Dict, nav_guidance: Dict) -> str:
        """Synthesize comprehensive response using GLM-4.5V"""
        if not GLM_V_AVAILABLE:
            return "GLM-4.5V not available for intelligent synthesis"

        try:
            # Build context from extraction results
            precise_url = extraction_result.get("exact_url", "https://nrp.ai/documentation/")
            match_info = extraction_result.get("precise_match", {})
            technical_depth = nav_guidance.get("technical_depth", "intermediate")

            # Enhanced prompt based on technical depth and query type
            gpu_specific_guidance = ""
            if any(gpu in query.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                gpu_specific_guidance = """

CRITICAL GPU-SPECIFIC REQUIREMENTS:
- Include exact resource specification syntax: nvidia.com/a100, nvidia.com/h100, etc.
- Explain differences between specific GPU types vs generic GPU requests
- Detail resource limits, availability constraints, and scheduling considerations
- Provide performance characteristics and optimal use cases
- Include node selection strategies for specific GPU types"""

            depth_guidance = {
                "basic": "Focus on step-by-step instructions with simple explanations",
                "intermediate": "Provide comprehensive guidance with examples and best practices",
                "advanced": "Include advanced configurations, troubleshooting, and optimization techniques"
            }.get(technical_depth, "Provide comprehensive guidance")

            synthesis_prompt = f"""You are an expert NRP Nautilus platform specialist. Generate a comprehensive, detailed response for this query: "{query}"

DOCUMENTATION CONTEXT:
- Precise Link: {precise_url}
- Page: {match_info.get('page', 'NRP Documentation').replace('_', ' ').title()}
- Section: {match_info.get('anchor', 'General').replace('-', ' ').title()}

RESPONSE REQUIREMENTS:
{depth_guidance}

MUST INCLUDE:
1. Clear, detailed explanation of the topic
2. Step-by-step instructions when applicable
3. Complete YAML/code examples with proper syntax
4. Best practices and common pitfalls with warnings
5. Related concepts and prerequisites
6. Comprehensive troubleshooting guidance
7. Resource requirements and platform-specific considerations{gpu_specific_guidance}

QUALITY STANDARDS:
- Use your 65,536 token context for comprehensive coverage
- Provide actionable, practical guidance beyond just documentation links
- Include specific examples relevant to NRP Nautilus platform
- Address both immediate needs and related concepts for complete understanding

Generate a response that combines precision with comprehensive educational value."""

            response = await glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are an expert NRP Nautilus Kubernetes platform specialist with deep knowledge of all NRP documentation, policies, and best practices. Generate comprehensive, actionable responses with examples and detailed guidance."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )

            comprehensive_explanation = response.choices[0].message.content

            # Format the final enhanced response
            return f"""# NRP Nautilus Documentation - Advanced Infogent Response

## Precise Documentation Match
**Direct Link**: {precise_url}
**Query**: {query}
**Technical Depth**: {technical_depth.title()}

## Comprehensive Expert Analysis
{comprehensive_explanation}

## Documentation Navigation
- Primary Source: {precise_url}
- Alternative References: {len(extraction_result.get('alternative_matches', []))} related sections found
- Complete NRP Documentation: https://nrp.ai/documentation/

---
*Response generated by Advanced Infogent Architecture (Navigator-Extractor-Aggregator)*
*Powered by GLM-4.5V multimodal AI with 65,536 token context*
*Ultra-comprehensive anchor database: {len(NRP_COMPLETE_ANCHORS) if NRP_KNOWLEDGE_AVAILABLE else 'N/A'} pages analyzed*"""

        except Exception as e:
            return f"""# Error in Advanced Synthesis

An error occurred during intelligent synthesis: {str(e)}

**Fallback Information:**
- Query: {query}
- Documentation: {precise_url}
- Please check the direct link for detailed information.

*Advanced Infogent Architecture error - falling back to basic response*"""

# =============================================================================
# MAIN INTELLIGENT K8S QUERY TOOL
# =============================================================================

class QueryParams(BaseModel):
    query: str = Field(description="Natural language query about NRP Nautilus or Kubernetes")
    context: str = Field(default="", description="Additional context for the query")

@mcp.tool()
async def advanced_intelligent_k8s_query(params: QueryParams) -> str:
    """
    Advanced intelligent K8s query processing using Navigator-Extractor-Aggregator
    architecture with GLM-4.5V multimodal AI.

    This is our painfully developed infogent architecture that provides:
    - Intelligent navigation and discovery
    - Precise content extraction
    - Comprehensive synthesis with examples and warnings
    """

    print(f"[INFOGENT] Processing advanced query: {params.query[:50]}...")

    try:
        # Step 1: Advanced Navigation with GLM-4.5V
        print("[NAVIGATOR] Analyzing query for intelligent discovery...")
        nav_result = await AdvancedNavigator.intelligent_discovery(params.query, params.context)

        if nav_result.get("status") == "error":
            print(f"[NAVIGATOR] Warning: {nav_result.get('error')}")
            nav_guidance = {"technical_depth": "intermediate", "enhanced_keywords": []}
        else:
            nav_guidance = nav_result.get("navigation_guidance", {})

        # Step 2: Advanced Extraction with Enhanced Matching
        print("[EXTRACTOR] Performing intelligent content extraction...")
        extraction_result = await AdvancedExtractor.intelligent_extraction(
            "https://nrp.ai/documentation/", params.query, nav_guidance
        )

        if extraction_result.get("status") == "error":
            print(f"[EXTRACTOR] Warning: {extraction_result.get('error')}")

        # Step 3: Advanced Aggregation with GLM-4.5V Synthesis
        print("[AGGREGATOR] Synthesizing comprehensive response...")
        final_response = await AdvancedAggregator.intelligent_synthesis(
            params.query, extraction_result, nav_guidance
        )

        print("[INFOGENT] Advanced processing complete")
        return final_response

    except Exception as e:
        error_response = f"""# Advanced Infogent Error

An error occurred in the advanced infogent processing pipeline:
{str(e)}

**System Status:**
- Navigator-Extractor-Aggregator: {'Available' if INFOGENT_AVAILABLE else 'Unavailable'}
- GLM-4.5V Integration: {'Available' if GLM_V_AVAILABLE else 'Unavailable'}
- NRP Knowledge Base: {'Available' if NRP_KNOWLEDGE_AVAILABLE else 'Unavailable'}

**Fallback:** Please check https://nrp.ai/documentation/ for manual reference.

*This error indicates an issue with our advanced infogent architecture*"""

        print(f"[INFOGENT] Error: {str(e)}")
        return error_response

# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ULTIMATE ADVANCED NRP K8s INFOGENT SERVER")
    print("Navigator-Extractor-Aggregator + GLM-4.5V Architecture")
    print("=" * 70)

    print(f"[STATUS] Infogent Components: {'OK' if INFOGENT_AVAILABLE else 'FAIL'}")
    print(f"[STATUS] GLM-4.5V Integration: {'OK' if GLM_V_AVAILABLE else 'FAIL'}")
    print(f"[STATUS] NRP Knowledge Base: {'OK' if NRP_KNOWLEDGE_AVAILABLE else 'FAIL'}")
    print(f"[STATUS] Kubernetes Client: {'OK' if K8S_AVAILABLE else 'FAIL'}")

    if not all([INFOGENT_AVAILABLE, GLM_V_AVAILABLE, NRP_KNOWLEDGE_AVAILABLE]):
        print("\n[WARNING] Some components unavailable - functionality may be limited")

    print("\n[STARTING] Advanced infogent server on port 8026...")
    mcp.run(port=8026)