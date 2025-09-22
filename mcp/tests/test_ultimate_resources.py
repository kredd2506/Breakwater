#!/usr/bin/env python3
"""Test Ultimate NRP Resources Server"""

import asyncio
import json
from fastmcp import Client

async def test_ultimate_resources():
    client = Client("http://localhost:8007/mcp")

    async with client:
        print("Testing Ultimate NRP.ai Resources Server")
        print("=" * 60)

        # Test 1: Server info
        print("\n1. Server Information:")
        try:
            result = await client.read_resource("nrp://ultimate/info")
            if result:
                info = json.loads(result[0].text)
                print(f"  Server: {info['name']} v{info['version']}")
                print(f"  Crawled pages: {info['crawl_statistics'].get('total_pages_crawled', 0)}")
                print(f"  Database size: {info['crawl_statistics'].get('database_size_mb', 0)} MB")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: Specific FPGA page
        print("\n2. FPGA Documentation:")
        try:
            result = await client.read_resource("nrp://specific/fpga")
            if result:
                fpga_data = json.loads(result[0].text)
                print(f"  Title: {fpga_data['title']}")
                print(f"  Content: {fpga_data['content_length']} chars")
                print(f"  Keywords: {', '.join(fpga_data['keywords'][:5])}")
                print(f"  URL: {fpga_data['url']}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: Ceph S3 User Documentation
        print("\n3. Ceph S3 User Documentation:")
        try:
            result = await client.read_resource("nrp://specific/ceph-s3-user")
            if result:
                ceph_data = json.loads(result[0].text)
                print(f"  Title: {ceph_data['title']}")
                print(f"  Content: {ceph_data['content_length']} chars")
                print(f"  Keywords: {', '.join(ceph_data['keywords'][:5])}")
                print(f"  URL: {ceph_data['url']}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Ceph S3 Admin Documentation
        print("\n4. Ceph S3 Admin Documentation:")
        try:
            result = await client.read_resource("nrp://specific/ceph-s3-admin")
            if result:
                ceph_admin_data = json.loads(result[0].text)
                print(f"  Title: {ceph_admin_data['title']}")
                print(f"  Content: {ceph_admin_data['content_length']} chars")
                print(f"  Keywords: {', '.join(ceph_admin_data['keywords'][:5])}")
                print(f"  URL: {ceph_admin_data['url']}")
        except Exception as e:
            print(f"  Error: {e}")

        # Test 5: Direct path access
        print("\n5. Direct Path Access:")
        test_paths = [
            "documentation/admindocs/cluster/fpga/",
            "documentation/userdocs/storage/ceph-s3/",
            "documentation/admindocs/storage/ceph-s3/"
        ]

        for path in test_paths:
            try:
                result = await client.read_resource(f"nrp://crawled/{path}")
                if result:
                    page_data = json.loads(result[0].text)
                    print(f"  Path: {path}")
                    print(f"    Status: {page_data['status']}")
                    print(f"    Title: {page_data.get('title', 'N/A')}")
                    print(f"    Content: {page_data.get('full_content_length', 0)} chars")
            except Exception as e:
                print(f"  Error accessing {path}: {e}")

        # Test 6: Comprehensive search
        print("\n6. Comprehensive Search:")
        search_queries = ["fpga", "ceph", "storage", "gpu"]

        for query in search_queries:
            try:
                result = await client.read_resource(f"nrp://search/all/{query}")
                if result:
                    search_data = json.loads(result[0].text)
                    print(f"  Search '{query}': {search_data['total_results']} total results")

                    for category, data in search_data['results_by_category'].items():
                        if data['count'] > 0:
                            print(f"    {category}: {data['count']} results")
                            if data['results']:
                                print(f"      Top result: {data['results'][0]['title']}")
                    break  # Test just one
            except Exception as e:
                print(f"  Error searching {query}: {e}")

        # Test 7: Crawl statistics
        print("\n7. Crawl Statistics:")
        try:
            result = await client.read_resource("nrp://crawled/stats")
            if result:
                stats = json.loads(result[0].text)
                print(f"  Total pages: {stats['total_pages_crawled']}")
                print(f"  Pages by category: {stats['pages_by_category']}")
                print(f"  Top keywords: {list(stats['top_keywords'].keys())[:5]}")
        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 60)
        print("Ultimate Resources Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_ultimate_resources())