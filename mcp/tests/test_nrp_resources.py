#!/usr/bin/env python3
"""
Test Client for NRP.ai Resources FastMCP Server
==============================================
Comprehensive testing of resource system including:
- Static resources
- Dynamic resource generation
- Template-based resources with parameters
- Resource caching and performance
"""

import asyncio
import json
from fastmcp import Client

async def test_nrp_resources_server():
    """Test all resource capabilities of the NRP resources server"""

    client = Client("http://localhost:8005/mcp")

    async with client:
        print("Testing NRP.ai Resources FastMCP Server")
        print("=" * 60)

        # Test 1: Static Resources
        print("\n1. Static Resources:")

        # Server status
        try:
            result = await client.read_resource("nrp://status")
            if result and len(result) > 0:
                status = json.loads(result[0].text)
                print(f"Server Status: {status['status']}")
                print(f"Capabilities: {len(status['capabilities'])}")
                print(f"Statistics: {status['statistics']}")
        except Exception as e:
            print(f"Error reading status: {e}")

        # Documentation index
        try:
            result = await client.read_resource("nrp://docs/index")
            if result and len(result) > 0:
                docs_index = json.loads(result[0].text)
                print(f"Documentation Index: {docs_index['total_documents']} documents")
        except Exception as e:
            print(f"Error reading docs index: {e}")

        # Templates index
        try:
            result = await client.read_resource("nrp://templates/index")
            if result and len(result) > 0:
                templates_index = json.loads(result[0].text)
                print(f"Templates Index: {templates_index['total_templates']} templates")
        except Exception as e:
            print(f"Error reading templates index: {e}")

        # Test 2: Dynamic Resources - Documentation Pages
        print("\n2. Dynamic Documentation Resources:")

        # Test fetching specific documentation
        doc_paths = ["/documentation", "/documentation/getting-started", "/guides/quickstart"]

        for path in doc_paths:
            try:
                result = await client.read_resource(f"nrp://docs{path}")
                if result and len(result) > 0:
                    doc_data = json.loads(result[0].text)
                    print(f"Documentation '{path}':")
                    print(f"  Title: {doc_data.get('title', 'N/A')}")
                    print(f"  Content Length: {len(doc_data.get('content', ''))} chars")
                    print(f"  YAML Resources: {doc_data.get('yaml_resources', 0)}")
                    print(f"  Code Blocks: {doc_data.get('code_blocks', 0)}")
                    break  # Test just one for demo
            except Exception as e:
                print(f"Error reading doc {path}: {e}")

        # Test 3: Refresh Documentation Tool
        print("\n3. Documentation Refresh Tool:")
        try:
            result = await client.call_tool("refresh_nrp_documentation", {
                "path": "/documentation"
            })
            print(f"Refresh Result: {result.data}")
        except Exception as e:
            print(f"Error refreshing documentation: {e}")

        # Test 4: Template Resources
        print("\n4. Template Resources:")

        # Get templates by type
        template_types = ["pod", "deployment", "service"]
        for template_type in template_types:
            try:
                result = await client.read_resource(f"nrp://k8s/template/{template_type}")
                if result and len(result) > 0:
                    template_data = json.loads(result[0].text)
                    print(f"{template_type.title()} Templates: {template_data['total_templates']}")
            except Exception as e:
                print(f"Error reading {template_type} templates: {e}")

        # Test 5: Parameterized Resources - Search
        print("\n5. Parameterized Resources - Search:")

        search_queries = ["kubernetes", "pod", "deployment"]
        for query in search_queries:
            try:
                result = await client.read_resource(f"nrp://search/{query}")
                if result and len(result) > 0:
                    search_data = json.loads(result[0].text)
                    print(f"Search '{query}': {search_data['total_results']} results")
                    for i, res in enumerate(search_data['results'][:2]):
                        print(f"  {i+1}. {res['title']} ({res['path']})")
            except Exception as e:
                print(f"Error searching for '{query}': {e}")

        # Test 6: Template Generation
        print("\n6. Dynamic Template Generation:")

        generation_tests = ["pod", "deployment", "service"]

        for resource_type in generation_tests:
            try:
                result = await client.read_resource(f"nrp://generate/{resource_type}")
                if result and len(result) > 0:
                    template = result[0].text
                    lines = template.split('\n')
                    print(f"Generated {resource_type} template:")
                    print(f"  Lines: {len(lines)}")
                    print(f"  Preview: {lines[0] if lines else 'Empty'}")
            except Exception as e:
                print(f"Error generating {resource_type} template: {e}")

        # Test 7: Cache Statistics
        print("\n7. Cache Statistics:")
        try:
            result = await client.read_resource("nrp://cache/stats")
            if result and len(result) > 0:
                cache_stats = json.loads(result[0].text)
                print(f"Documentation: {cache_stats['documentation']['total_pages']} pages")
                print(f"Templates: {cache_stats['templates']['total_templates']} templates")
                print(f"Cache: {cache_stats['cache']['active_entries']} active entries")
                print(f"Storage: {cache_stats['storage']['database_size_mb']} MB")
        except Exception as e:
            print(f"Error reading cache stats: {e}")

        # Test 8: Specific Template Access
        print("\n8. Specific Template Access:")

        # First get a template name from the index
        try:
            result = await client.read_resource("nrp://templates/index")
            if result and len(result) > 0:
                templates_index = json.loads(result[0].text)
                if templates_index['templates']:
                    template_name = templates_index['templates'][0]['name']

                    # Now get the specific template
                    result = await client.read_resource(f"nrp://templates/{template_name}")
                    if result and len(result) > 0:
                        template_data = json.loads(result[0].text)
                        print(f"Template '{template_name}':")
                        print(f"  Type: {template_data['type']}")
                        print(f"  Description: {template_data['description']}")
                        print(f"  Parameters: {template_data['parameters']}")
        except Exception as e:
            print(f"Error accessing specific template: {e}")

        # Test 9: Cache Management
        print("\n9. Cache Management:")
        try:
            result = await client.call_tool("clear_resource_cache", {
                "older_than_hours": 1
            })
            print(f"Cache Clear Result: {result.data}")
        except Exception as e:
            print(f"Error clearing cache: {e}")

        print("\n" + "=" * 60)
        print("All Resource Tests Completed!")

async def demo_resource_workflow():
    """Demonstrate complete resource workflow"""

    print("\n" + "=" * 60)
    print("RESOURCE WORKFLOW DEMONSTRATION")
    print("=" * 60)

    client = Client("http://localhost:8005/mcp")

    async with client:
        # Step 1: Check server status
        print("\n1. Server Status Check:")
        result = await client.read_resource("nrp://status")
        if result:
            status = json.loads(result[0].text)
            print(f"Server operational with {len(status['capabilities'])} capabilities")

        # Step 2: Refresh documentation to populate cache
        print("\n2. Populating Documentation Cache:")
        result = await client.call_tool("refresh_nrp_documentation", {
            "path": "/documentation"
        })
        print(f"Documentation refresh: {result.data[:100]}...")

        # Step 3: Search for specific content
        print("\n3. Content Discovery:")
        result = await client.read_resource("nrp://search/docs?q=kubernetes&limit=5")
        if result:
            search_data = json.loads(result[0].text)
            print(f"Found {search_data['total_results']} kubernetes-related documents")

        # Step 4: Generate templates
        print("\n4. Template Generation:")
        for resource_type in ["pod", "deployment"]:
            result = await client.read_resource(f"nrp://generate/{resource_type}")
            if result:
                print(f"Generated {resource_type} template ({len(result[0].text)} chars)")

        # Step 5: Cache performance
        print("\n5. Cache Performance:")
        result = await client.read_resource("nrp://cache/stats")
        if result:
            stats = json.loads(result[0].text)
            print(f"Cache hit rate: {stats['cache']['hit_rate']}")
            print(f"Database size: {stats['storage']['database_size_mb']} MB")

if __name__ == "__main__":
    print("Starting NRP.ai Resources FastMCP Server Tests...")

    # Run all tests
    asyncio.run(test_nrp_resources_server())
    asyncio.run(demo_resource_workflow())

    print("\n" + "=" * 60)
    print("RESOURCE TESTING COMPLETED SUCCESSFULLY!")
    print("=" * 60)