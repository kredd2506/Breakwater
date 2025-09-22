#!/usr/bin/env python3
"""Extract YAML examples from NRP.ai documentation"""

import asyncio
import aiohttp
import re
import json
from bs4 import BeautifulSoup

async def extract_nrp_yaml():
    """Extract all YAML examples from NRP.ai documentation"""

    # Key NRP.ai pages
    pages = [
        'https://nrp.ai/documentation',
        'https://nrp-nautilus.io/docs/getting-started',
        'https://nrp-nautilus.io/docs/storage',
        'https://nrp-nautilus.io/docs/gpu'
    ]

    yaml_examples = {}

    async with aiohttp.ClientSession() as session:
        for url in pages:
            try:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')

                        # Find YAML code blocks
                        yaml_blocks = []

                        # Method 1: Find <code> blocks with YAML
                        code_blocks = soup.find_all(['code', 'pre'])
                        for block in code_blocks:
                            text = block.get_text()
                            if ('apiVersion' in text or 'kind:' in text or
                                'metadata:' in text or 'spec:' in text):
                                yaml_blocks.append(text.strip())

                        # Method 2: Regex for markdown YAML blocks
                        yaml_pattern = r'```ya?ml\s*([\s\S]*?)```'
                        matches = re.findall(yaml_pattern, content, re.IGNORECASE)
                        yaml_blocks.extend([match.strip() for match in matches])

                        # Method 3: Look for K8s resource patterns
                        k8s_pattern = r'(apiVersion:\s*[\w/]+\s*\nkind:\s*\w+[\s\S]*?)(?=\n\s*(?:apiVersion|---|$))'
                        k8s_matches = re.findall(k8s_pattern, content, re.MULTILINE)
                        yaml_blocks.extend([match.strip() for match in k8s_matches])

                        # Clean and deduplicate
                        clean_blocks = []
                        for block in yaml_blocks:
                            if len(block) > 20 and ('apiVersion' in block or 'kind:' in block):
                                clean_blocks.append(block)

                        yaml_examples[url] = list(set(clean_blocks))  # Remove duplicates
                        print(f"{url}: Found {len(yaml_examples[url])} unique YAML blocks")

                        # Show sample
                        for i, block in enumerate(yaml_examples[url][:2]):
                            lines = block.split('\n')
                            print(f"  Example {i+1}: {len(lines)} lines")
                            if len(lines) > 0:
                                print(f"    First line: {lines[0]}")

                    else:
                        print(f"{url}: HTTP {response.status}")

            except Exception as e:
                print(f"{url}: Error - {e}")

    # Save all examples
    total_examples = sum(len(examples) for examples in yaml_examples.values())
    print(f"\nTotal YAML examples found: {total_examples}")

    # Save to file
    with open('nrp_yaml_examples.json', 'w') as f:
        json.dump(yaml_examples, f, indent=2)

    return yaml_examples

if __name__ == "__main__":
    asyncio.run(extract_nrp_yaml())