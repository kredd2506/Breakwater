#!/usr/bin/env python3
"""
Comprehensive MCP System Tests
=============================
Tests all MCP functionality with Unicode-safe output
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime

# Ensure UTF-8 encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    from knowledge_buffer import knowledge_buffer
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def call_mcp_endpoint(path, data=None):
    """Make HTTP call to MCP server"""
    try:
        url = f"http://localhost:8025{path}"
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def test_mcp_functionality():
    """Run comprehensive MCP tests"""
    print("=" * 60)
    print("COMPREHENSIVE MCP SYSTEM TESTS")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()

    try:
        # Test server connection
        print("1. Testing server connection...")
        response = call_mcp_endpoint("/")
        if "error" not in response:
            print("   [SUCCESS] Connected to MCP server")
        else:
            print(f"   [ERROR] Connection failed: {response.get('error', 'Unknown error')}")
        print()

        # Test available tools/endpoints
        print("2. Testing available endpoints...")
        endpoints = ["/tools", "/status", "/health"]
        for endpoint in endpoints:
            response = call_mcp_endpoint(endpoint)
            if "error" not in response:
                print(f"   [SUCCESS] {endpoint}: OK")
            else:
                print(f"   [ERROR] {endpoint}: {response.get('error', 'Failed')}")
        print()

        # Test K8s operations
        print("3. Testing Kubernetes Operations...")
        k8s_tests = [
            "list my pods",
            "get deployments",
            "describe services",
            "show cluster info"
        ]

        for query in k8s_tests:
            print(f"   Testing: '{query}'")
            response = call_mcp_endpoint("/run_k8s_command", {"query": query})

            if "error" not in response:
                response_text = str(response).replace('\n', ' ')[:100] + "..."
                print(f"   [SUCCESS] Response: {response_text}")

                # Log to knowledge buffer
                knowledge_buffer.add_conversation(
                    query=query,
                    intent="COMMAND",
                    response=str(response),
                    success=True,
                    metadata={"k8s_operation": True}
                )
            else:
                print(f"   [ERROR] {response.get('error', 'Unknown error')[:100]}...")
                knowledge_buffer.add_conversation(
                    query=query,
                    intent="COMMAND",
                    response=f"Error: {response.get('error', 'Unknown error')}",
                    success=False,
                    metadata={"k8s_operation": True}
                )
        print()

        # Test documentation queries
        print("4. Testing Documentation Queries...")
        doc_tests = [
            "How do I request A100 GPUs?",
            "Show me storage examples",
            "What are the YAML templates?",
            "Help with networking setup"
        ]

        for query in doc_tests:
            print(f"   Testing: '{query}'")
            response = call_mcp_endpoint("/get_documentation", {"query": query})

            if "error" not in response:
                response_text = str(response).replace('\n', ' ')[:100] + "..."
                print(f"   [SUCCESS] Response: {response_text}")

                knowledge_buffer.add_conversation(
                    query=query,
                    intent="QUESTION",
                    response=str(response),
                    success=True,
                    metadata={"documentation": True}
                )
            else:
                print(f"   [ERROR] {response.get('error', 'Unknown error')[:100]}...")
                knowledge_buffer.add_conversation(
                    query=query,
                    intent="QUESTION",
                    response=f"Error: {response.get('error', 'Unknown error')}",
                    success=False,
                    metadata={"documentation": True}
                )
        print()

        # Test intent classification
        print("5. Testing Intent Classification...")
        intent_tests = [
            ("delete all pods", "COMMAND"),
            ("explain GPU allocation", "QUESTION"),
            ("quit system", "QUIT")
        ]

        for query, expected_intent in intent_tests:
            print(f"   Testing: '{query}' (expect: {expected_intent})")
            response = call_mcp_endpoint("/classify_intent", {"query": query})

            if "error" not in response:
                actual_intent = str(response).strip()
                if expected_intent.lower() in actual_intent.lower():
                    print(f"   [SUCCESS] Intent: {actual_intent}")
                else:
                    print(f"   [WARNING] Expected {expected_intent}, got {actual_intent}")
            else:
                print(f"   [ERROR] {response.get('error', 'Unknown error')[:100]}...")
        print()

        # Test knowledge buffer insights
        print("6. Testing Knowledge Buffer...")
        insights = knowledge_buffer.get_knowledge_insights()
        print(f"   Total queries: {insights['conversation_stats']['total_queries']}")
        print(f"   Success rate: {insights['conversation_stats']['success_rate']:.2%}")
        print(f"   Top topics: {list(insights['top_topics'][:3]) if insights['top_topics'] else 'None'}")
        print()

        # Final summary
        print("7. Test Summary")
        print(f"   Server connection: Tested")
        print(f"   K8s operations: {len(k8s_tests)} tested")
        print(f"   Documentation: {len(doc_tests)} tested")
        print(f"   Intent classification: {len(intent_tests)} tested")
        print(f"   Knowledge tracking: Active")
        print()
        print("=" * 60)
        print("COMPREHENSIVE TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_mcp_functionality()
    sys.exit(0 if success else 1)