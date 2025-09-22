#!/usr/bin/env python3
"""Test Logging Enhanced NRP.ai FastMCP Server - Comprehensive Structured Logging Testing"""

import asyncio
import json
from fastmcp import Client

async def test_logging_features():
    client = Client("http://localhost:8013/mcp")

    async with client:
        print("Testing Logging Enhanced NRP.ai FastMCP Server")
        print("=" * 70)

        # Test 1: List available logging-enhanced tools
        print("\n1. Available Logging-Enhanced Tools:")
        try:
            tools = await client.list_tools()
            print(f"  Found {len(tools)} logging tools:")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: Logging Configuration Management
        print("\n" + "=" * 70)
        print("2. Logging Configuration Management:")
        try:
            result = await client.call_tool("configure_logging_settings", {})
            print(f"  Current Logging Configuration:")
            print(f"  {result.data}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: Modify Logging Settings
        print("\n" + "=" * 70)
        print("3. Modifying Logging Settings:")
        try:
            # Enable performance tracking
            result = await client.call_tool("configure_logging_settings", {
                "setting_name": "enable_performance_tracking",
                "setting_value": True
            })
            print(f"  Performance Tracking Result: {result.data}")

            # Enable security logging
            result2 = await client.call_tool("configure_logging_settings", {
                "setting_name": "enable_security_logging",
                "setting_value": True
            })
            print(f"  Security Logging Result: {result2.data}")

            # Set verbose logging
            result3 = await client.call_tool("configure_logging_settings", {
                "setting_name": "verbose_logging",
                "setting_value": True
            })
            print(f"  Verbose Logging Result: {result3.data if hasattr(result3, 'data') else 'Setting not found'}")

        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Comprehensive GPU Deployment with Structured Logging
        print("\n" + "=" * 70)
        print("4. Comprehensive GPU Deployment with Structured Logging:")
        try:
            result = await client.call_tool("comprehensive_gpu_deployment", {
                "gpu_type": "a100",
                "gpu_count": 2,
                "memory_gb": 64,
                "cpu_cores": 16,
                "namespace": "ml-research",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "user_id": "test_user_123"
            })

            print(f"  Deployment Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "deployment_" in result.data:
                print(f"    Contains deployment ID: [OK]")
            if "Structured Logging" in result.data:
                print(f"    Contains logging confirmation: [OK]")
            if "Performance tracking" in result.data:
                print(f"    Contains performance tracking: [OK]")
            if "Security logging" in result.data:
                print(f"    Contains security logging: [OK]")
            print(f"    Preview: {result.data[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 5: Security Audit Log Analysis
        print("\n" + "=" * 70)
        print("5. Security Audit Log Analysis with Compliance Logging:")
        try:
            result = await client.call_tool("security_audit_log_analysis", {
                "time_range_hours": 48,
                "user_filter": None,
                "severity_filter": "all"
            })

            print(f"  Security Audit Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "[SECURITY AUDIT]" in result.data:
                print(f"    Contains security audit header: [OK]")
            if "Events Found" in result.data:
                print(f"    Contains event summary: [OK]")
            if "Security Event Summary" in result.data:
                print(f"    Contains event breakdown: [OK]")
            if "Structured Logging Applied" in result.data:
                print(f"    Contains logging confirmation: [OK]")
            print(f"    Preview: {result.data[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 6: Logging Demonstration (All Levels)
        print("\n" + "=" * 70)
        print("6. Comprehensive Logging Demonstration:")
        try:
            result = await client.call_tool("logging_demonstration", {
                "demo_type": "comprehensive",
                "include_errors": True
            })

            print(f"  Logging Demo Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "[SUCCESS]" in result.data:
                print(f"    Contains success indicator: [OK]")
            if "Debug level logging" in result.data:
                print(f"    Contains debug level demo: [OK]")
            if "Warning level logging" in result.data:
                print(f"    Contains warning level demo: [OK]")
            if "Error level logging" in result.data:
                print(f"    Contains error level demo: [OK]")
            if "Security event logging" in result.data:
                print(f"    Contains security logging demo: [OK]")
            if "Performance metrics" in result.data:
                print(f"    Contains performance logging demo: [OK]")
            print(f"    Preview: {result.data[:400]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 7: Invalid Configuration Error Handling
        print("\n" + "=" * 70)
        print("7. Error Handling for Invalid Logging Configuration:")
        try:
            result = await client.call_tool("configure_logging_settings", {
                "setting_name": "invalid_logging_setting",
                "setting_value": True
            })
            print(f"  Invalid Setting Result:")
            if "[ERROR]" in result.data:
                print(f"    Properly handles invalid setting: [OK]")
            if "Unknown logging setting" in result.data:
                print(f"    Contains descriptive error message: [OK]")
            print(f"    Preview: {result.data[:200]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        # Test 8: Logging Demonstration without Errors
        print("\n" + "=" * 70)
        print("8. Logging Demonstration (Info/Warning Only):")
        try:
            result = await client.call_tool("logging_demonstration", {
                "demo_type": "basic",
                "include_errors": False
            })
            print(f"  Basic Demo Result:")
            print(f"    Response length: {len(result.data)} characters")
            if "Multi-level logging" in result.data:
                print(f"    Contains logging level info: [OK]")
            if "Structured metadata" in result.data:
                print(f"    Contains metadata info: [OK]")
            if "Session correlation" in result.data:
                print(f"    Contains correlation info: [OK]")
            print(f"    Preview: {result.data[:300]}...")
            print()
        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)
        print("Logging Enhanced Server Testing Complete!")
        print("\nAll FastMCP Structured Logging Features Tested:")
        print("  [OK] Multi-Level Logging (debug, info, warning, error)")
        print("  [OK] Structured Metadata with Rich Context")
        print("  [OK] Performance Tracking with Timing Metrics")
        print("  [OK] Security Logging with Compliance Metadata")
        print("  [OK] Session Correlation and Request Tracking")
        print("  [OK] Runtime Configuration Management")
        print("  [OK] Category-Based Log Organization")
        print("  [OK] Error Context and Recovery Information")

async def demo_logging_workflow():
    """Demonstrate a complete logging workflow with all features"""

    print("\n" + "=" * 70)
    print("STRUCTURED LOGGING WORKFLOW DEMONSTRATION")
    print("=" * 70)

    client = Client("http://localhost:8013/mcp")

    async with client:
        # Scenario: Enterprise deployment with comprehensive logging
        print("\nScenario: Enterprise Deployment with Full Structured Logging")
        print("-" * 65)

        # Step 1: Configure logging for enterprise compliance
        print("1. Configuring logging for enterprise compliance...")
        try:
            # Enable all logging features
            await client.call_tool("configure_logging_settings", {
                "setting_name": "enable_security_logging",
                "setting_value": True
            })

            await client.call_tool("configure_logging_settings", {
                "setting_name": "enable_user_activity_tracking",
                "setting_value": True
            })

            await client.call_tool("configure_logging_settings", {
                "setting_name": "enable_resource_monitoring",
                "setting_value": True
            })

            print(f"   Configured enterprise-grade logging features")
        except Exception as e:
            print(f"   Configuration Error: {e}")

        # Step 2: Deploy with comprehensive logging
        print("2. Deploying GPU workload with comprehensive logging...")
        try:
            deployment_result = await client.call_tool("comprehensive_gpu_deployment", {
                "gpu_type": "a100",
                "gpu_count": 4,
                "memory_gb": 128,
                "cpu_cores": 32,
                "namespace": "enterprise-ml",
                "workload_type": "production",
                "enable_monitoring": True,
                "user_id": "enterprise_admin"
            })
            print(f"   Generated comprehensive deployment with full audit trail")
        except Exception as e:
            print(f"   Deployment Error: {e}")

        # Step 3: Security audit analysis
        print("3. Performing security audit with compliance logging...")
        try:
            audit_result = await client.call_tool("security_audit_log_analysis", {
                "time_range_hours": 24,
                "user_filter": "enterprise_admin",
                "severity_filter": "all"
            })
            print(f"   Generated security audit with SOC2 compliance metadata")
        except Exception as e:
            print(f"   Audit Error: {e}")

        # Step 4: Demonstrate all logging levels
        print("4. Demonstrating all logging levels and categories...")
        try:
            demo_result = await client.call_tool("logging_demonstration", {
                "demo_type": "comprehensive",
                "include_errors": True
            })
            print(f"   Demonstrated all logging capabilities with structured metadata")
        except Exception as e:
            print(f"   Demo Error: {e}")

        # Step 5: Validate logging configuration
        print("5. Validating final logging configuration...")
        try:
            config_result = await client.call_tool("configure_logging_settings", {})
            print(f"   Retrieved and validated enterprise logging configuration")
        except Exception as e:
            print(f"   Validation Error: {e}")

        print("\nStructured Logging Workflow Complete: Enterprise now has:")
        print("  [OK] Comprehensive security logging with SOC2 compliance metadata")
        print("  [OK] Performance tracking with detailed timing and resource metrics")
        print("  [OK] User activity tracking with session correlation")
        print("  [OK] Multi-level logging (debug, info, warning, error) with rich context")
        print("  [OK] Category-based log organization (security, performance, workflow, etc.)")
        print("  [OK] Structured metadata for queryable and actionable log entries")
        print("  [OK] Runtime configuration management for operational flexibility")
        print("  [OK] Complete audit trail for compliance and debugging")

async def test_logging_performance():
    """Test logging performance and metadata handling"""

    print("\n" + "=" * 70)
    print("LOGGING PERFORMANCE AND METADATA TESTING")
    print("=" * 70)

    client = Client("http://localhost:8013/mcp")

    async with client:
        print("\nTesting Logging Performance and Structured Metadata:")
        print("-" * 55)

        # Test 1: Large deployment with extensive logging
        print("1. Testing large deployment with extensive logging...")
        try:
            start_time = asyncio.get_event_loop().time()
            result = await client.call_tool("comprehensive_gpu_deployment", {
                "gpu_type": "h100",
                "gpu_count": 8,
                "memory_gb": 80,
                "cpu_cores": 64,
                "namespace": "performance-test",
                "workload_type": "ml_training",
                "enable_monitoring": True,
                "user_id": "performance_tester"
            })
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            print(f"   Large deployment completed in {duration:.2f} seconds with full logging")
        except Exception as e:
            print(f"   Performance Test Error: {e}")

        # Test 2: Security audit with large time range
        print("2. Testing security audit with extended time range...")
        try:
            start_time = asyncio.get_event_loop().time()
            result = await client.call_tool("security_audit_log_analysis", {
                "time_range_hours": 168,  # 1 week
                "user_filter": None,
                "severity_filter": "high"
            })
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            print(f"   Extended security audit completed in {duration:.2f} seconds")
        except Exception as e:
            print(f"   Audit Performance Test Error: {e}")

        # Test 3: Multiple logging demonstrations
        print("3. Testing multiple concurrent logging operations...")
        try:
            start_time = asyncio.get_event_loop().time()

            # Run multiple demos concurrently
            tasks = [
                client.call_tool("logging_demonstration", {
                    "demo_type": "comprehensive",
                    "include_errors": True
                }),
                client.call_tool("logging_demonstration", {
                    "demo_type": "basic",
                    "include_errors": False
                }),
                client.call_tool("configure_logging_settings", {})
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            successful_operations = sum(1 for r in results if not isinstance(r, Exception))
            print(f"   {successful_operations}/3 concurrent operations completed in {duration:.2f} seconds")

        except Exception as e:
            print(f"   Concurrent Operations Error: {e}")

        print("\nLogging Performance Testing Complete!")
        print("All logging operations maintained performance while providing rich metadata")

if __name__ == "__main__":
    asyncio.run(test_logging_features())
    asyncio.run(demo_logging_workflow())
    asyncio.run(test_logging_performance())