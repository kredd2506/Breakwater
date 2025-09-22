#!/usr/bin/env python3
"""
Test Enhanced Extraction
=======================

Test the enhanced deep extractor and knowledge base functionality
to ensure proper extraction and storage of YAML templates and cautions.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from nrp_k8s_system.agents.deep_extractor_agent import DeepExtractorAgent
from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pattern_matching():
    """Test the new extraction patterns."""
    print("Testing extraction patterns...")

    # Define NRP-specific patterns directly for testing
    yaml_patterns = [
        # NRP-specific: <pre data-language="yaml"> with class="expressive code"
        r'<pre[^>]*data-language=["\']yaml["\'][^>]*class=["\'][^"\']*expressive[^"\']*code[^"\']*["\'][^>]*>(.*?)</pre>',
        r'<pre[^>]*class=["\'][^"\']*expressive[^"\']*code[^"\']*["\'][^>]*data-language=["\']yaml["\'][^>]*>(.*?)</pre>',
        # Alternative NRP patterns
        r'<pre[^>]*data-language=["\']yaml["\'][^>]*>(.*?)</pre>',
    ]

    warning_patterns = [
        # NRP-specific caution patterns
        r'<[^>]*class=["\'][^"\']*\bcomplementary\s+caution\b[^"\']*["\'][^>]*>(.*?)</[^>]*>',
        r'<[^>]*class=["\'][^"\']*\bcaution\b[^"\']*["\'][^>]*>(.*?)</[^>]*>',
    ]

    # Test YAML patterns
    test_yamls = [
        '<pre data-language="yaml" class="expressive code">apiVersion: v1\nkind: Pod</pre>',
        '<pre class="expressive code" data-language="yaml">apiVersion: v1\nkind: Job</pre>',
        '<pre data-language="yaml">apiVersion: v1\nkind: Service</pre>',
    ]

    print("Testing YAML pattern matching:")
    for i, test_yaml in enumerate(test_yamls):
        matched = False
        for j, pattern in enumerate(yaml_patterns):
            import re
            match = re.search(pattern, test_yaml, re.DOTALL)
            if match:
                print(f"  [OK] Pattern {j} matched test {i}: {match.group(1)[:30]}...")
                matched = True
                break
        if not matched:
            print(f"  [FAIL] No pattern matched test {i}")

    # Test caution patterns
    test_cautions = [
        '<div class="caution">This is a caution</div>',
        '<aside class="complementary caution">This is a complementary caution</aside>',
        '<p class="warning caution note">Mixed classes</p>',
    ]

    print("\nTesting caution pattern matching:")
    for i, test_caution in enumerate(test_cautions):
        matched = False
        for j, pattern in enumerate(warning_patterns):
            import re
            match = re.search(pattern, test_caution, re.DOTALL)
            if match:
                print(f"  [OK] Warning pattern {j} matched test {i}: {match.group(1)[:30]}...")
                matched = True
                break
        if not matched:
            print(f"  [FAIL] No warning pattern matched test {i}")

def test_bs4_parsing():
    """Test BeautifulSoup parsing with NRP-style HTML."""
    print("\nTesting BeautifulSoup parsing...")

    # Sample NRP-style HTML
    sample_html = '''
    <div>
        <h2>GPU Example</h2>
        <div class="caution">
            <p>A100 GPUs are limited resources.</p>
        </div>
        <pre data-language="yaml" class="expressive code">
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  containers:
  - name: gpu-container
    resources:
      limits:
        nvidia.com/a100: 1
        </pre>
        <div class="complementary caution">
            <p>Use appropriate resource requests.</p>
        </div>
    </div>
    '''

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html.parser')

        # Test YAML extraction
        yaml_blocks = soup.find_all('pre', attrs={'data-language': 'yaml'})
        print(f"Found {len(yaml_blocks)} YAML blocks with data-language='yaml'")

        expressive_blocks = soup.find_all(['pre', 'code'], class_=lambda x: x and 'expressive' in ' '.join(x))
        print(f"Found {len(expressive_blocks)} blocks with 'expressive' class")

        # Test caution extraction
        import re
        caution_blocks = soup.find_all(class_=re.compile(r'\bcaution\b', re.I))
        print(f"Found {len(caution_blocks)} caution blocks")

        complementary_caution_blocks = soup.find_all(class_=re.compile(r'\bcomplementary\s+caution\b', re.I))
        print(f"Found {len(complementary_caution_blocks)} complementary caution blocks")

        for i, block in enumerate(yaml_blocks):
            content = block.get_text(strip=True)
            print(f"  YAML Block {i+1}: {content[:50]}...")

        for i, block in enumerate(caution_blocks):
            content = block.get_text(strip=True)
            print(f"  Caution {i+1}: {content[:50]}...")

        print("[OK] BeautifulSoup parsing test completed successfully")

    except Exception as e:
        print(f"[FAIL] BeautifulSoup parsing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run tests."""
    print("="*60)
    print("Enhanced Extraction Test Suite")
    print("="*60)

    try:
        test_pattern_matching()
        test_bs4_parsing()

        print("\n" + "="*60)
        print("Test suite completed!")
        print("="*60)

    except Exception as e:
        print(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
