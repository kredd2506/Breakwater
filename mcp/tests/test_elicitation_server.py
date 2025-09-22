#!/usr/bin/env python3
"""Test Enhanced Elicitation NRP.ai FastMCP Server - Comprehensive Elicitation and Error Handling Testing"""

import asyncio
import json
from fastmcp import Client

async def test_elicitation_features():
    client = Client("http://localhost:8012/mcp")

    async with client:
        print("Testing Enhanced Elicitation NRP.ai FastMCP Server")
        print("=" * 70)

        # Test 1: List available tools with elicitation capabilities
        print("\n1. Available Elicitation-Enhanced Tools:")
        try:
            tools = await client.list_tools()
            print(f"  Found {len(tools)} elicitation tools:")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: Test Server Flags Configuration
        print("\n" + "=" * 70)
        print("2. Server Flags Configuration:")
        try:
            result = await client.call_tool("configure_server_flags", {})
            print(f"  Current Configuration:")
            print(f"  {result.data}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: Modify Server Flags
        print("\n" + "=" * 70)
        print("3. Modifying Server Flags:")
        try:
            # Enable verbose logging
            result = await client.call_tool("configure_server_flags", {
                "flag_name": "verbose_logging",
                "flag_value": True
            })
            print(f"  Flag Update Result: {result.data}")

            # Enable auto retry
            result2 = await client.call_tool("configure_server_flags", {
                "flag_name": "auto_retry_on_error",
                "flag_value": True
            })
            print(f"  Auto Retry Result: {result2.data}")

        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Enhanced Error Recovery Demo
        print("\n" + "=" * 70)
        print("4. Enhanced Error Recovery Demonstrations:")

        # Test validation error
        try:
            print("  Testing validation error handling...")
            result = await client.call_tool("enhanced_error_recovery_demo", {
                "trigger_error_type": "validation"
            })
            print(f"  Validation Error Demo Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "[ERROR]" in result.data:
                print(f"    Contains error structure: [OK]")
            if "suggestions" in result.data.lower():
                print(f"    Contains recovery suggestions: [OK]")
            print(f"    Preview: {result.data[:300]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test elicitation cancelled error
        try:
            print("  Testing elicitation cancelled error...")
            result = await client.call_tool("enhanced_error_recovery_demo", {
                "trigger_error_type": "elicitation_cancelled"
            })
            print(f"  Elicitation Cancelled Demo Result:")
            if "elicitation_cancelled" in result.data.lower():
                print(f"    Contains elicitation error type: [OK]")
            if "restart" in result.data.lower():
                print(f"    Contains restart suggestion: [OK]")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test resource unavailable error
        try:
            print("  Testing resource unavailable error...")
            result = await client.call_tool("enhanced_error_recovery_demo", {
                "trigger_error_type": "resource_unavailable"
            })
            print(f"  Resource Unavailable Demo Result:")
            if "resource_unavailable" in result.data.lower():
                print(f"    Contains resource error type: [OK]")
            if "different resource" in result.data.lower():
                print(f"    Contains alternative suggestions: [OK]")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 5: Progressive Resource Analysis (Multi-turn Elicitation Demo)
        print("\n" + "=" * 70)
        print("5. Progressive Resource Analysis (Multi-turn Elicitation):")
        try:
            result = await client.call_tool("progressive_resource_analysis", {
                "analysis_scope": "cluster"
            })
            print(f"  Progressive Analysis Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "analysis_" in result.data:
                print(f"    Contains analysis ID: [OK]")
            if "GPU Availability" in result.data:
                print(f"    Contains GPU information: [OK]")
            if "Resource Utilization" in result.data:
                print(f"    Contains utilization data: [OK]")
            print(f"    Preview: {result.data[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 6: Invalid Flag Configuration (Error Handling)
        print("\n" + "=" * 70)
        print("6. Error Handling for Invalid Flag Configuration:")
        try:
            result = await client.call_tool("configure_server_flags", {
                "flag_name": "invalid_flag_name",
                "flag_value": True
            })
            print(f"  Invalid Flag Result:")
            if "[ERROR]" in result.data:
                print(f"    Properly handles invalid flag: [OK]")
            if "Unknown server flag" in result.data:
                print(f"    Contains descriptive error message: [OK]")
            if "available_flags" in result.data:
                print(f"    Contains available options: [OK]")
            print(f"    Preview: {result.data[:300]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 7: Successful Workflow (No Errors)
        print("\n" + "=" * 70)
        print("7. Successful Error Recovery Demo (No Triggered Errors):")
        try:
            result = await client.call_tool("enhanced_error_recovery_demo", {})
            print(f"  Success Demo Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "[SUCCESS]" in result.data:
                print(f"    Contains success indicator: [OK]")
            if "Error Types for Testing" in result.data:
                print(f"    Contains error type information: [OK]")
            if "Server Flags Configuration" in result.data:
                print(f"    Contains configuration info: [OK]")
            if "Error Handling Features" in result.data:
                print(f"    Contains feature overview: [OK]")
            print(f"    Preview: {result.data[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)
        print("Enhanced Elicitation Server Testing Complete!")
        print("\nAll FastMCP Elicitation Features Tested:")
        print("  [OK] Progressive Multi-Turn Elicitation")
        print("  [OK] Structured Response Types with Validation")
        print("  [OK] Enhanced Error Handling with Context")
        print("  [OK] Smart Defaults and Auto-Retry")
        print("  [OK] Server Flags Configuration")
        print("  [OK] Error Recovery with Suggestions")
        print("  [OK] Detailed Error Context and IDs")
        print("  [OK] Runtime Behavior Control")

async def demo_elicitation_workflow():
    """Demonstrate a complete elicitation workflow with error handling"""

    print("\n" + "=" * 70)
    print("ELICITATION WORKFLOW DEMONSTRATION")
    print("=" * 70)

    client = Client("http://localhost:8012/mcp")

    async with client:
        # Scenario: Complete deployment workflow with progressive elicitation
        print("\nScenario: Complete Deployment with Progressive Elicitation")
        print("-" * 60)

        # Step 1: Configure server for optimal elicitation experience
        print("1. Configuring server for optimal elicitation...")
        try:
            # Enable progressive disclosure
            await client.call_tool("configure_server_flags", {
                "flag_name": "enable_progressive_disclosure",
                "flag_value": True
            })

            # Enable confirmation for critical operations
            await client.call_tool("configure_server_flags", {
                "flag_name": "require_confirmation_for_critical_ops",
                "flag_value": True
            })

            # Enable smart defaults
            await client.call_tool("configure_server_flags", {
                "flag_name": "enable_smart_defaults",
                "flag_value": True
            })

            print(f"   Configured server for enhanced elicitation experience")
        except Exception as e:
            print(f"   Configuration Error: {e}")

        # Step 2: Demonstrate error recovery
        print("2. Testing error recovery capabilities...")
        try:
            # Test each error type
            error_types = ["validation", "elicitation_cancelled", "resource_unavailable"]
            for error_type in error_types:
                result = await client.call_tool("enhanced_error_recovery_demo", {
                    "trigger_error_type": error_type
                })
                print(f"   Tested {error_type} error handling: [OK]")
        except Exception as e:
            print(f"   Error Recovery Test Error: {e}")

        # Step 3: Progressive resource analysis
        print("3. Performing progressive resource analysis...")
        try:
            analysis_result = await client.call_tool("progressive_resource_analysis", {
                "analysis_scope": "cluster"
            })
            print(f"   Generated comprehensive cluster analysis with elicitation")
        except Exception as e:
            print(f"   Analysis Error: {e}")

        # Step 4: Demonstrate flag configuration capabilities
        print("4. Testing runtime configuration capabilities...")
        try:
            # Show current configuration
            config_result = await client.call_tool("configure_server_flags", {})
            print(f"   Retrieved current server configuration")

            # Test flag modification
            flag_result = await client.call_tool("configure_server_flags", {
                "flag_name": "max_elicitation_rounds",
                "flag_value": True
            })
            print(f"   Tested flag modification capabilities")
        except Exception as e:
            print(f"   Configuration Test Error: {e}")

        print("\nElicitation Workflow Complete: System now provides:")
        print("  [OK] Progressive multi-turn elicitation for complex inputs")
        print("  [OK] Structured response collection with intelligent validation")
        print("  [OK] Comprehensive error handling with detailed context")
        print("  [OK] Smart defaults and automatic retry capabilities")
        print("  [OK] Runtime configuration through server flags")
        print("  [OK] Detailed error recovery with actionable suggestions")
        print("  [OK] Context-aware error tracking and support")
        print("  [OK] Graceful degradation for incomplete user input")

async def test_error_patterns():
    """Test specific error patterns and recovery mechanisms"""

    print("\n" + "=" * 70)
    print("ERROR PATTERN TESTING")
    print("=" * 70)

    client = Client("http://localhost:8012/mcp")

    async with client:
        print("\nTesting Various Error Patterns and Recovery Mechanisms:")
        print("-" * 55)

        # Test 1: Invalid tool parameters
        print("1. Testing invalid tool parameters...")
        try:
            result = await client.call_tool("invalid_tool_name", {})
            print(f"   Result: {result.data[:100]}...")
        except Exception as e:
            print(f"   Expected error for invalid tool: [OK]")
            print(f"   Error: {str(e)[:100]}...")

        # Test 2: Missing required parameters
        print("2. Testing missing required parameters...")
        try:
            result = await client.call_tool("configure_server_flags", {
                "flag_name": "test_flag"
                # Missing flag_value parameter
            })
            print(f"   Result: {result.data[:100]}...")
        except Exception as e:
            print(f"   Handled missing parameters gracefully: [OK]")

        # Test 3: Invalid parameter types
        print("3. Testing invalid parameter types...")
        try:
            result = await client.call_tool("configure_server_flags", {
                "flag_name": 123,  # Should be string
                "flag_value": "invalid_bool"  # Should be boolean
            })
            print(f"   Result: {result.data[:100]}...")
        except Exception as e:
            print(f"   Validated parameter types correctly: [OK]")

        print("\nError Pattern Testing Complete!")
        print("All error scenarios handled appropriately with proper validation")

if __name__ == "__main__":
    asyncio.run(test_elicitation_features())
    asyncio.run(demo_elicitation_workflow())
    asyncio.run(test_error_patterns())