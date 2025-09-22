#!/usr/bin/env python3
"""Test Enhanced GPU Pods Resources with A100 Examples and Cautions"""

import asyncio
import json
from fastmcp import Client

async def test_enhanced_gpu_resources():
    client = Client("http://localhost:8008/mcp")

    async with client:
        print("Testing Enhanced GPU Pods Resources")
        print("=" * 70)

        # Test 1: Enhanced GPU Pods with A100 examples
        print("\n1. Enhanced GPU Pods Documentation:")
        try:
            result = await client.read_resource("nrp://enhanced/gpu-pods")
            if result:
                gpu_data = json.loads(result[0].text)
                print(f"  Title: {gpu_data['title']}")
                print(f"  Status: {gpu_data['status']}")
                print(f"  Content Length: {gpu_data['content_length']} chars")
                print()

                # A100 Examples
                if gpu_data.get('a100_gpu_examples'):
                    a100_section = gpu_data['a100_gpu_examples']
                    print(f"  A100 GPU Examples ({a100_section['count']}):")
                    for i, example in enumerate(a100_section['examples'][:3], 1):
                        print(f"    {i}. {example['text'][:150]}...")
                    print()

                # GPU Resource Types
                if gpu_data.get('gpu_resource_types'):
                    resource_section = gpu_data['gpu_resource_types']
                    print(f"  GPU Resource Types ({resource_section['count']}):")
                    for i, resource in enumerate(resource_section['resources'][:5], 1):
                        print(f"    {i}. {resource['resource']}")
                    print()

                # YAML Configurations
                if gpu_data.get('yaml_configurations'):
                    yaml_section = gpu_data['yaml_configurations']
                    print(f"  YAML Configurations ({yaml_section['count']}):")
                    for i, config in enumerate(yaml_section['configs'][:2], 1):
                        print(f"    {i}. GPU Type: {config['gpu_type']}")
                        print(f"       YAML Preview: {config['yaml'][:100]}...")
                    print()

                # Request Instructions
                if gpu_data.get('request_instructions'):
                    instruction_section = gpu_data['request_instructions']
                    print(f"  Request Instructions ({instruction_section['count']}):")
                    for i, instruction in enumerate(instruction_section['instructions'][:3], 1):
                        print(f"    {i}. {instruction['instruction'][:150]}...")
                    print()

                # Cautions and Notes
                if gpu_data.get('cautions_and_notes'):
                    caution_section = gpu_data['cautions_and_notes']
                    print(f"  Cautions and Notes ({caution_section['count']}):")
                    for i, note in enumerate(caution_section['notes'][:3], 1):
                        print(f"    {i}. {note['text'][:150]}...")

        except Exception as e:
            print(f"  Error: {e}")

        # Test 2: Specific A100 Examples
        print("\n" + "=" * 70)
        print("2. Specific A100 GPU Examples:")
        try:
            result = await client.read_resource("nrp://gpu/a100-examples")
            if result:
                a100_data = json.loads(result[0].text)
                print(f"  Title: {a100_data['title']}")
                print(f"  Resource Identifier: {a100_data['resource_identifier']}")
                print(f"  Reservation Required: {a100_data['reservation_required']}")
                print()

                # Examples
                if a100_data.get('examples'):
                    examples = a100_data['examples']
                    print(f"  A100 Examples ({examples['count']}):")
                    for i, example in enumerate(examples['detailed_examples'][:3], 1):
                        print(f"    {i}. {example['text'][:200]}...")
                    print()

                # YAML Configurations
                if a100_data.get('yaml_configurations'):
                    yaml_configs = a100_data['yaml_configurations']
                    print(f"  A100 YAML Configurations ({yaml_configs['count']}):")
                    for i, config in enumerate(yaml_configs['configs'][:2], 1):
                        print(f"    {i}. {config['yaml'][:150]}...")
                    print()

                # Key Points
                if a100_data.get('key_points'):
                    print("  Key Points:")
                    for i, point in enumerate(a100_data['key_points'], 1):
                        print(f"    {i}. {point}")

        except Exception as e:
            print(f"  Error: {e}")

        # Test 3: All Cautions and Notes
        print("\n" + "=" * 70)
        print("3. All Cautions and Important Notes:")
        try:
            result = await client.read_resource("nrp://special/cautions-notes")
            if result:
                cautions_data = json.loads(result[0].text)
                print(f"  Title: {cautions_data['title']}")
                print(f"  Total Items: {cautions_data['total_items']}")
                print()

                # Categories
                if cautions_data.get('categories'):
                    categories = cautions_data['categories']

                    print(f"  GPU-Related Items: {len(categories.get('gpu_related', []))}")
                    for i, item in enumerate(categories.get('gpu_related', [])[:2], 1):
                        print(f"    {i}. {item['text'][:150]}...")

                    print(f"\\n  General Instructions: {len(categories.get('general_instructions', []))}")
                    for i, item in enumerate(categories.get('general_instructions', [])[:2], 1):
                        print(f"    {i}. {item['instruction'][:150]}...")

                    print(f"\\n  Cautions/Warnings: {len(categories.get('cautions_warnings', []))}")
                    for i, item in enumerate(categories.get('cautions_warnings', [])[:2], 1):
                        print(f"    {i}. {item['text'][:150]}...")

        except Exception as e:
            print(f"  Error: {e}")

        # Test 4: Refresh Tool
        print("\n" + "=" * 70)
        print("4. Refresh GPU Documentation:")
        try:
            result = await client.call_tool("refresh_gpu_documentation", {})
            print(f"  Refresh Result: {result.data}")
        except Exception as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)
        print("Enhanced GPU Resources Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_gpu_resources())