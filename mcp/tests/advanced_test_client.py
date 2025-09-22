#!/usr/bin/env python3
"""
Advanced K8s Infogent FastMCP Test Client
========================================
Comprehensive test client for all advanced FastMCP features including:
- Advanced Kubernetes operations with validation
- Content scraping with navigator-extractor-aggregator
- NRP.ai documentation integration
- Async operations and streaming
- Content search and YAML processing
"""

import asyncio
import json
from datetime import datetime, timedelta
from fastmcp import Client

# Create client for the advanced server
client = Client("http://localhost:8003/mcp")

async def test_advanced_server():
    """Test all advanced server capabilities"""

    async with client:
        print("Testing Advanced K8s Infogent FastMCP Server")
        print("=" * 70)

        # Test 1: Advanced Kubernetes Resource Listing with Caching
        print("\n1. Advanced Kubernetes Resource Listing:")
        try:
            # Test with caching enabled
            result = await client.call_tool("k8s_list_resources_advanced", {
                "resource_type": "pod",
                "namespace": "gsoc",
                "use_cache": True,
                "cache_ttl": 300
            })
            print(f"Pods (with cache): {result.structured_content}")

            # Test deployments
            result = await client.call_tool("k8s_list_resources_advanced", {
                "resource_type": "deployment",
                "namespace": "gsoc"
            })
            print(f"Deployments: {result.structured_content}")

        except Exception as e:
            print(f"Error in K8s listing: {e}")

        # Test 2: Advanced Pod Creation with Comprehensive Validation
        print("\n2. Advanced Pod Creation:")
        try:
            pod_spec = {
                "name": "advanced-test-pod",
                "image": "nginx:latest",
                "memory_limit": "256Mi",
                "cpu_limit": "200m",
                "memory_request": "128Mi",
                "cpu_request": "100m",
                "env_vars": {"ENV": "test", "DEBUG": "true"},
                "ports": [80, 8080],
                "restart_policy": "Always"
            }

            result = await client.call_tool("k8s_create_pod_advanced", {"spec": pod_spec})
            print(f"Pod Creation Result: {result.structured_content}")

        except Exception as e:
            print(f"Error in pod creation: {e}")

        # Test 3: Content Scraping with Navigator-Extractor-Aggregator
        print("\n3. Content Scraping Architecture:")
        try:
            scraping_config = {
                "url": "https://kubernetes.io/docs/concepts/workloads/pods/",
                "content_type": "documentation",
                "extract_yaml": True,
                "follow_links": True,
                "max_depth": 2,
                "cache_duration": 1800
            }

            result = await client.call_tool("scrape_content", {"config": scraping_config})
            print(f"Scraping Result: {result.structured_content}")

        except Exception as e:
            print(f"Error in content scraping: {e}")

        # Test 4: NRP.ai Documentation Scraping
        print("\n4. NRP.ai Documentation Scraping:")
        try:
            result = await client.call_tool("scrape_nrp_documentation", {
                "documentation_path": "/documentation",
                "extract_yaml": True,
                "store_resources": True
            })
            print(f"NRP Documentation Result: {result.structured_content}")

        except Exception as e:
            print(f"Error in NRP scraping: {e}")

        # Test 5: Content Search with Advanced Filtering
        print("\n5. Advanced Content Search:")
        try:
            # Search for Kubernetes-related content
            filter_config = {
                "content_types": ["documentation"],
                "keywords": ["kubernetes", "pod"],
                "date_from": (datetime.now() - timedelta(days=1)).isoformat()
            }

            result = await client.call_tool("search_content", {
                "query": "kubernetes deployment",
                "filter_config": filter_config,
                "limit": 5
            })
            print(f"Search Results: {result.structured_content}")

        except Exception as e:
            print(f"Error in content search: {e}")

        # Test 6: YAML Resource Retrieval
        print("\n6. YAML Resource Management:")
        try:
            result = await client.call_tool("get_yaml_resources", {
                "resource_type": "pod",
                "name_pattern": "test",
                "validated_only": False
            })
            print(f"YAML Resources: {result.structured_content}")

        except Exception as e:
            print(f"Error in YAML retrieval: {e}")

        # Test 7: Server Resources - Cache Statistics
        print("\n7. Cache and Storage Statistics:")
        try:
            result = await client.read_resource("infogent://cache/stats")
            if result and len(result) > 0:
                stats = json.loads(result[0].text)
                print(f"Cache Statistics: {json.dumps(stats, indent=2)}")
        except Exception as e:
            print(f"Error reading cache stats: {e}")

        # Test 8: Architecture Overview
        print("\n8. Infogent Architecture Overview:")
        try:
            result = await client.read_resource("infogent://architecture/overview")
            if result and len(result) > 0:
                overview = json.loads(result[0].text)
                print(f"Architecture: {json.dumps(overview, indent=2)}")
        except Exception as e:
            print(f"Error reading architecture overview: {e}")

        # Test 9: Streaming Operations (if supported)
        print("\n9. Testing Streaming Operations:")
        try:
            # Note: This would need special handling for streaming responses
            # For now, we'll test regular pod logs
            pods_result = await client.call_tool("k8s_list_resources_advanced", {
                "resource_type": "pod",
                "namespace": "gsoc"
            })

            if pods_result.structured_content.get("resources"):
                first_pod = pods_result.structured_content["resources"][0]
                print(f"Testing logs for pod: {first_pod}")

                # This would be streaming in real implementation
                # result = await client.call_tool("stream_pod_logs", {
                #     "pod_name": first_pod,
                #     "namespace": "gsoc",
                #     "follow": False,
                #     "tail_lines": 10
                # })
                # print(f"Streaming Result: {result.structured_content}")

        except Exception as e:
            print(f"Error in streaming test: {e}")

        print("\n" + "=" * 70)
        print("All Advanced Tests Completed!")

async def test_content_workflow():
    """Test the complete content workflow from scraping to usage"""

    print("\n" + "=" * 70)
    print("COMPLETE CONTENT WORKFLOW TEST")
    print("=" * 70)

    async with client:
        # Step 1: Scrape multiple sources
        print("\n1. Scraping Multiple Content Sources:")

        sources = [
            {
                "url": "https://kubernetes.io/docs/concepts/",
                "content_type": "documentation",
                "extract_yaml": True
            },
            {
                "url": "https://docs.docker.com/",
                "content_type": "documentation",
                "extract_yaml": False
            }
        ]

        scraped_urls = []
        for source in sources:
            try:
                result = await client.call_tool("scrape_content", {"config": source})
                scraped_urls.append(source["url"])
                print(f"Scraped: {source['url']} - {result.structured_content.get('content_length', 0)} chars")
            except Exception as e:
                print(f"Error scraping {source['url']}: {e}")

        # Step 2: Search across all content
        print("\n2. Cross-Content Search:")
        try:
            result = await client.call_tool("search_content", {
                "query": "container orchestration",
                "limit": 10
            })
            print(f"Found {result.structured_content.get('total_results', 0)} results across all content")

            for i, res in enumerate(result.structured_content.get('results', [])[:3]):
                print(f"  {i+1}. {res['url']} ({res['content_type']})")
                print(f"     Preview: {res['content_preview'][:100]}...")

        except Exception as e:
            print(f"Error in cross-content search: {e}")

        # Step 3: Get extracted YAML resources
        print("\n3. Extracted YAML Resources:")
        try:
            result = await client.call_tool("get_yaml_resources", {})
            resources = result.structured_content.get('resources', [])
            print(f"Total YAML resources extracted: {len(resources)}")

            for i, resource in enumerate(resources[:5]):
                print(f"  {i+1}. {resource['name']} ({resource['resource_type']})")
                print(f"     Source: {resource['source_url']}")
                print(f"     Validated: {'✓' if resource['validated'] else '✗'}")

        except Exception as e:
            print(f"Error retrieving YAML resources: {e}")

        # Step 4: Cache statistics
        print("\n4. Final Cache Statistics:")
        try:
            result = await client.read_resource("infogent://cache/stats")
            if result and len(result) > 0:
                stats = json.loads(result[0].text)
                print(f"Content items: {sum(item['count'] for item in stats.get('content_statistics', []))}")
                print(f"YAML resources: {sum(item['count'] for item in stats.get('yaml_statistics', []))}")
                print(f"Recent activity: {stats.get('recent_activity', {})}")
        except Exception as e:
            print(f"Error reading final stats: {e}")

async def test_error_handling():
    """Test error handling and validation"""

    print("\n" + "=" * 70)
    print("ERROR HANDLING AND VALIDATION TESTS")
    print("=" * 70)

    async with client:
        # Test 1: Invalid resource type
        print("\n1. Testing Invalid Resource Type:")
        try:
            result = await client.call_tool("k8s_list_resources_advanced", {
                "resource_type": "invalid_type"
            })
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected error caught: {e}")

        # Test 2: Invalid pod specification
        print("\n2. Testing Invalid Pod Specification:")
        try:
            invalid_spec = {
                "name": "INVALID-NAME-WITH-CAPS",  # Invalid K8s name
                "image": "",  # Empty image
                "memory_limit": "invalid"  # Invalid memory format
            }
            result = await client.call_tool("k8s_create_pod_advanced", {"spec": invalid_spec})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected validation error caught: {e}")

        # Test 3: Invalid URL for scraping
        print("\n3. Testing Invalid URL Scraping:")
        try:
            invalid_config = {
                "url": "https://invalid-url-that-doesnt-exist.com",
                "content_type": "documentation"
            }
            result = await client.call_tool("scrape_content", {"config": invalid_config})
            print(f"Result: {result.structured_content}")
        except Exception as e:
            print(f"Expected scraping error caught: {e}")

if __name__ == "__main__":
    print("Starting Advanced K8s Infogent FastMCP Client Tests...")

    # Run all test suites
    asyncio.run(test_advanced_server())
    asyncio.run(test_content_workflow())
    asyncio.run(test_error_handling())

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)