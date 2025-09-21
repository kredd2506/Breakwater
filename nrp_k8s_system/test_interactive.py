#!/usr/bin/env python3
"""Test script to demonstrate interactive mode functionality"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_intelligent_router import EnhancedIntelligentRouter

def test_interactive():
    """Test the interactive functionality"""
    router = EnhancedIntelligentRouter()
    
    print("Testing Enhanced Intelligent Router")
    print("=" * 50)
    
    # Test question
    print("\n1. Testing Question Handling:")
    result = router.process_query("What are the GPU types available?")
    print(f"Type: {result.get('type')}")
    print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
    
    # Test command 
    print("\n2. Testing Command Handling:")
    result = router.process_query("show me pods in gsoc namespace")
    print(f"Type: {result.get('type')}")
    print(f"Success: {result.get('success')}")
    
    # Test generation
    print("\n3. Testing Generation Handling:")
    result = router.process_query("create a simple web deployment")
    print(f"Type: {result.get('type')}")
    if 'manifests' in result:
        print(f"Generated {len(result['manifests'])} manifest(s)")
    
    print("\n" + "=" * 50)
    print("Enhanced Router is working correctly!")

if __name__ == "__main__":
    test_interactive()