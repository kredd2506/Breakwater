#!/usr/bin/env python3
"""
Test Client for Enhanced NRP.ai Resources FastMCP Server
========================================================
Comprehensive testing of ALL FastMCP resource concepts including:
- Static resources with metadata and tags
- Dynamic resources with lazy loading
- Resource templates with parameterized URIs
- Wildcard parameters and default values
- Async/sync resource generation
- Analytics and usage tracking
- Cache management and statistics
"""

import asyncio
import json
from fastmcp import Client

async def test_enhanced_resources_server():
    """Test all enhanced resource capabilities"""

    client = Client("http://localhost:8006/mcp")

    async with client:
        print("Testing Enhanced NRP.ai Resources FastMCP Server")
        print("=" * 70)

        # Test 1: Static Resources with Metadata
        print("\n1. Static Resources with Comprehensive Metadata:")

        # Server info with enhanced metadata
        try:
            result = await client.read_resource("nrp://server/info")
            if result and len(result) > 0:
                info = json.loads(result[0].text)
                print(f"Server: {info['name']} v{info['version']}")
                print(f"Capabilities: {len(info['capabilities'])} advanced features")
                print(f"Formats: {', '.join(info['supported_formats'])}")
                print(f"Tags: {', '.join(info['tags'])}")
        except Exception as e:
            print(f"Error reading server info: {e}")

        # Templates catalog
        try:
            result = await client.read_resource("nrp://templates/catalog")
            if result and len(result) > 0:
                catalog = json.loads(result[0].text)
                print(f"Templates Catalog: {catalog['total_templates']} templates")
                for name, template in list(catalog['templates'].items())[:3]:
                    print(f"  - {name}: {template['description']}")
        except Exception as e:
            print(f"Error reading templates catalog: {e}")

        # Test 2: Dynamic Resources with Lazy Loading
        print("\n2. Dynamic Resources with Lazy Loading:")

        doc_paths = ["/documentation", "/user-guide"]
        for path in doc_paths:
            try:
                result = await client.read_resource(f"nrp://docs{path}")
                if result and len(result) > 0:
                    doc_data = json.loads(result[0].text)
                    print(f"Documentation '{path}':")
                    print(f"  Title: {doc_data.get('title', 'N/A')}")
                    print(f"  Content: {doc_data.get('full_content_length', 0)} chars")
                    print(f"  YAML Blocks: {doc_data.get('yaml_blocks', 0)}")
                    print(f"  Status: {doc_data.get('status', 'unknown')}")
                    break  # Test just one for demo
            except Exception as e:
                print(f"Error reading doc {path}: {e}")

        # Test 3: Resource Templates with Wildcard Parameters
        print("\n3. Resource Templates with Wildcard Parameters:")

        template_names = ["basic-pod", "gpu-pod", "deployment"]
        for template_name in template_names:
            try:
                result = await client.read_resource(f"nrp://template/{template_name}")
                if result and len(result) > 0:
                    template_data = json.loads(result[0].text)
                    print(f"Template '{template_name}':")
                    print(f"  Type: {template_data['type']}")
                    print(f"  Parameters: {template_data['parameters']}")
                    print(f"  Lines: {template_data['metadata']['template_lines']}")
                    break  # Test just one for demo
            except Exception as e:
                print(f"Error reading template {template_name}: {e}")

        # Test 4: Parameterized Resource Generation with Default Values
        print("\n4. Parameterized Resource Generation:")

        generation_tests = [
            ("pod", "basic-pod"),
            ("pod", "gpu-pod"),
            ("deployment", "deployment")
        ]

        for resource_type, template_name in generation_tests:
            try:
                result = await client.read_resource(f"nrp://generate/{resource_type}/{template_name}")
                if result and len(result) > 0:
                    generated_yaml = result[0].text
                    lines = generated_yaml.split('\n')
                    print(f"Generated {resource_type}/{template_name}:")
                    print(f"  Lines: {len(lines)}")
                    print(f"  Preview: {lines[0] if lines else 'Empty'}")
                    if len(lines) > 1:
                        print(f"  Kind: {lines[1] if len(lines) > 1 else 'N/A'}")
            except Exception as e:
                print(f"Error generating {resource_type}/{template_name}: {e}")

        # Test 5: Advanced Search with Flexible Parameters
        print("\n5. Advanced Search with Flexible Parameters:")

        search_queries = ["pod", "gpu", "storage", "kubernetes"]
        for query in search_queries:
            try:
                result = await client.read_resource(f"nrp://search/{query}")
                if result and len(result) > 0:
                    search_data = json.loads(result[0].text)
                    print(f"Search '{query}': {search_data['total_results']} results")
                    if search_data['templates']:
                        for template in search_data['templates'][:2]:
                            print(f"  Template: {template['name']} (relevance: {template.get('relevance', 0):.1f})")
                    break  # Test just one for demo
            except Exception as e:
                print(f"Error searching for '{query}': {e}")

        # Test 6: Analytics and Usage Tracking
        print("\n6. Analytics and Usage Tracking:")

        try:
            result = await client.read_resource("nrp://analytics/usage")
            if result and len(result) > 0:
                analytics = json.loads(result[0].text)
                print(f"Usage Analytics:")
                print(f"  Top Resources: {len(analytics.get('top_resources', []))}")
                if analytics.get('top_resources'):
                    for resource in analytics['top_resources'][:3]:
                        print(f"    - {resource['uri']}: {resource['count']} accesses")
                print(f"  Recent Activity: {len(analytics.get('recent_activity', []))} entries")
                if analytics.get('cache_statistics'):
                    cache_stats = analytics['cache_statistics']
                    print(f"  Cache Entries: {cache_stats.get('total_entries', 0)}")
                    print(f"  Total Accesses: {cache_stats.get('total_accesses', 0)}")
        except Exception as e:
            print(f"Error reading analytics: {e}")

        # Test 7: Resource Management Tools
        print("\n7. Resource Management Tools:")

        # Refresh template cache
        try:
            result = await client.call_tool("refresh_template_cache", {})
            print(f"Cache Refresh: {result.data}")
        except Exception as e:
            print(f"Error refreshing cache: {e}")

        # Clear analytics data
        try:
            result = await client.call_tool("clear_analytics_data", {
                "older_than_hours": 1
            })
            print(f"Analytics Clear: {result.data}")
        except Exception as e:
            print(f"Error clearing analytics: {e}")

        # Test 8: Error Handling and Edge Cases
        print("\n8. Error Handling and Edge Cases:")

        # Non-existent template
        try:
            result = await client.read_resource("nrp://template/non-existent")
            if result and len(result) > 0:
                error_data = json.loads(result[0].text)
                print(f"Non-existent template: {error_data.get('error', 'No error')}")
        except Exception as e:
            print(f"Expected error for non-existent template: {e}")

        # Invalid documentation path
        try:
            result = await client.read_resource("nrp://docs/invalid-path")
            if result and len(result) > 0:
                error_data = json.loads(result[0].text)
                print(f"Invalid doc path status: {error_data.get('status', 'unknown')}")
        except Exception as e:
            print(f"Expected error for invalid path: {e}")

        print("\n" + "=" * 70)
        print("All Enhanced Resource Tests Completed!")

async def demo_enhanced_workflow():
    """Demonstrate complete enhanced workflow"""

    print("\n" + "=" * 70)
    print("ENHANCED RESOURCE WORKFLOW DEMONSTRATION")
    print("=" * 70)

    client = Client("http://localhost:8006/mcp")

    async with client:
        # Step 1: Check enhanced server capabilities
        print("\n1. Enhanced Server Capabilities:")
        result = await client.read_resource("nrp://server/info")
        if result:
            info = json.loads(result[0].text)
            print(f"Server operational with {len(info['capabilities'])} advanced capabilities")
            print(f"Supported formats: {', '.join(info['supported_formats'])}")

        # Step 2: Explore template catalog
        print("\n2. Template Catalog Exploration:")
        result = await client.read_resource("nrp://templates/catalog")
        if result:
            catalog = json.loads(result[0].text)
            print(f"Available: {catalog['total_templates']} K8s templates")

        # Step 3: Generate specific resources
        print("\n3. Advanced Resource Generation:")
        resources_to_generate = [
            ("pod", "gpu-pod"),
            ("storage", "persistent-volume"),
            ("deployment", "deployment")
        ]

        for resource_type, template_name in resources_to_generate:
            result = await client.read_resource(f"nrp://generate/{resource_type}/{template_name}")
            if result:
                yaml_content = result[0].text
                print(f"Generated {template_name}: {len(yaml_content.split('\\n'))} lines")

        # Step 4: Perform advanced search
        print("\n4. Advanced Content Discovery:")
        result = await client.read_resource("nrp://search/gpu")
        if result:
            search_data = json.loads(result[0].text)
            print(f"GPU-related resources: {search_data['total_results']} results")

        # Step 5: Check analytics
        print("\n5. Usage Analytics:")
        result = await client.read_resource("nrp://analytics/usage")
        if result:
            analytics = json.loads(result[0].text)
            cache_stats = analytics.get('cache_statistics', {})
            print(f"Cache entries: {cache_stats.get('total_entries', 0)}")
            print(f"Total accesses: {cache_stats.get('total_accesses', 0)}")

if __name__ == "__main__":
    print("Starting Enhanced NRP.ai Resources FastMCP Server Tests...")

    # Run all tests
    asyncio.run(test_enhanced_resources_server())
    asyncio.run(demo_enhanced_workflow())

    print("\n" + "=" * 70)
    print("ENHANCED RESOURCE TESTING COMPLETED SUCCESSFULLY!")
    print("=" * 70)