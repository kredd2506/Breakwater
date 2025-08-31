#!/usr/bin/env python3
"""
Test script to verify NRP K8s System installation
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test package imports
        from nrp_k8s_system import intelligent_route, init_chat_model
        print("✅ Package imports successful")
    except ImportError as e:
        print(f"❌ Package import failed: {e}")
        return False
    
    try:
        # Test core dependencies
        import langchain_openai
        import kubernetes
        import requests
        import json
        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Core dependency missing: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration"""
    print("Testing configuration...")
    
    # Check for .env file
    if Path(".env").exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - copy from config/default.env")
    
    # Check NRP_API_KEY
    nrp_key = os.environ.get("NRP_API_KEY")
    if nrp_key:
        print("✅ NRP_API_KEY is set")
    else:
        print("⚠️  NRP_API_KEY not set in environment")
    
    return True

def test_kubernetes():
    """Test Kubernetes connectivity"""
    print("Testing Kubernetes...")
    
    try:
        from kubernetes import client, config
        
        # Try to load config
        try:
            config.load_incluster_config()
            print("✅ In-cluster Kubernetes config loaded")
        except config.ConfigException:
            try:
                config.load_kube_config()
                print("✅ Local Kubernetes config loaded")
            except config.ConfigException:
                print("❌ Could not load Kubernetes config")
                return False
        
        # Try to create client
        v1 = client.CoreV1Api()
        print("✅ Kubernetes client created")
        
        return True
        
    except Exception as e:
        print(f"❌ Kubernetes test failed: {e}")
        return False

def test_directories():
    """Test directory structure"""
    print("Testing directory structure...")
    
    expected_dirs = [
        "core",
        "systems", 
        "cache",
        "config"
    ]
    
    expected_files = [
        "__init__.py",
        "intelligent_router.py",
        "cli.py",
        "requirements.txt",
        "core/__init__.py",
        "core/nrp_init.py",
        "systems/__init__.py"
    ]
    
    for dir_name in expected_dirs:
        if Path(dir_name).is_dir():
            print(f"✅ Directory {dir_name} exists")
        else:
            print(f"❌ Directory {dir_name} missing")
            return False
    
    for file_name in expected_files:
        if Path(file_name).is_file():
            print(f"✅ File {file_name} exists")
        else:
            print(f"❌ File {file_name} missing")
            return False
    
    return True

def main():
    """Main test function"""
    print("🧪 NRP K8s System Installation Test")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directories),
        ("Python Imports", test_imports),
        ("Configuration", test_configuration), 
        ("Kubernetes", test_kubernetes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation looks good.")
        print("\nNext steps:")
        print("1. Set NRP_API_KEY in .env file")
        print("2. Test with: python -m nrp_k8s_system.intelligent_router 'list pods'")
    else:
        print("⚠️  Some tests failed. Check the output above.")
        print("Run setup.sh or setup.bat to fix installation issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)