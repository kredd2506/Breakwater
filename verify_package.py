#!/usr/bin/env python3
"""
Package Verification Script for NRP K8s System
Verifies that all knowledge bases and resources are properly included
"""

import os
import sys
from pathlib import Path
import json

def check_knowledge_bases():
    """Check if knowledge base files are present and functional"""
    print("*** Checking Knowledge Bases ***")

    # MCP Cache Knowledge Files
    mcp_cache = Path("mcp/cache")
    critical_mcp_files = [
        "nrp_comprehensive_templates.py",
        "nrp_complete_anchor_db.py",
        "nrp_gpu_knowledge.py",
        "comprehensive_template_database.json",
        "nrp_complete_anchors.json"
    ]

    missing_mcp = []
    for file in critical_mcp_files:
        file_path = mcp_cache / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"[OK] {file} ({size:,} bytes)")
        else:
            missing_mcp.append(file)
            print(f"[MISSING] {file}")

    # NRP K8s Cache Knowledge
    nrp_cache = Path("nrp_k8s_system/cache")
    critical_nrp_dirs = [
        "fast_knowledge",
        "enhanced_knowledge_base",
        "nautilus_docs"
    ]

    missing_nrp = []
    for directory in critical_nrp_dirs:
        dir_path = nrp_cache / directory
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            print(f"✅ {directory}/ ({len(files)} files)")
        else:
            missing_nrp.append(directory)
            print(f"❌ {directory}/ (missing)")

    return len(missing_mcp) == 0 and len(missing_nrp) == 0

def check_templates():
    """Check if template files are present"""
    print("\n🎨 Checking Templates...")

    template_files = [
        "templates/chat.html"
    ]

    all_present = True
    for template in template_files:
        path = Path(template)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {template} ({size:,} bytes)")
        else:
            print(f"❌ {template} (missing)")
            all_present = False

    return all_present

def test_imports():
    """Test if knowledge base imports work"""
    print("\n🔬 Testing Knowledge Base Imports...")

    # Test MCP imports
    sys.path.insert(0, str(Path("mcp/cache")))

    tests = [
        ("nrp_comprehensive_templates", "NRP_TEMPLATES"),
        ("nrp_complete_anchor_db", "NRP_COMPLETE_ANCHORS"),
        ("nrp_gpu_knowledge", "NRP_GPU_RESOURCES"),
    ]

    success_count = 0
    for module, attribute in tests:
        try:
            imported = __import__(module)
            data = getattr(imported, attribute)
            size = len(data) if hasattr(data, '__len__') else "N/A"
            print(f"✅ {module}.{attribute} ({size} items)")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}.{attribute} - Import failed: {e}")
        except AttributeError as e:
            print(f"⚠️  {module}.{attribute} - Attribute missing: {e}")
        except Exception as e:
            print(f"❌ {module}.{attribute} - Error: {e}")

    return success_count == len(tests)

def check_server_files():
    """Check if server files are present and functional"""
    print("\n🖥️ Checking Server Files...")

    server_files = [
        "web_chat_server.py",
        "mcp/ultimate_fastmcp_server.py",
        "start_web_server.py",
        "start_mcp_server.py",
        "setup.py"
    ]

    all_present = True
    for server_file in server_files:
        path = Path(server_file)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {server_file} ({size:,} bytes)")

            # Basic syntax check for Python files
            if server_file.endswith('.py'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        compile(f.read(), path, 'exec')
                    print(f"   └─ Syntax: OK")
                except SyntaxError as e:
                    print(f"   └─ Syntax: ERROR - {e}")
                    all_present = False
        else:
            print(f"❌ {server_file} (missing)")
            all_present = False

    return all_present

def check_configuration():
    """Check configuration files"""
    print("\n⚙️ Checking Configuration...")

    config_files = [
        ".env.example",
        "requirements.txt",
        "README.md",
        "INSTALLATION.md"
    ]

    all_present = True
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {config_file} ({size:,} bytes)")
        else:
            print(f"❌ {config_file} (missing)")
            all_present = False

    # Check if .env exists (optional)
    env_path = Path(".env")
    if env_path.exists():
        print(f"✅ .env (configured)")
    else:
        print(f"⚠️  .env (not configured - will use demo mode)")

    return all_present

def estimate_package_size():
    """Estimate total package size"""
    print("\n📊 Package Size Analysis...")

    directories_to_check = [
        "mcp/cache",
        "nrp_k8s_system/cache",
        "templates",
        "."
    ]

    total_size = 0
    for directory in directories_to_check:
        if directory == ".":
            # Root files only
            files = [f for f in Path(".").glob("*.py") if f.is_file()]
            files.extend([f for f in Path(".").glob("*.md") if f.is_file()])
            files.extend([f for f in Path(".").glob("*.txt") if f.is_file()])
        else:
            files = list(Path(directory).rglob("*"))
            files = [f for f in files if f.is_file()]

        dir_size = sum(f.stat().st_size for f in files if f.exists())
        total_size += dir_size

        if dir_size > 0:
            print(f"  {directory}: {dir_size:,} bytes ({len(files)} files)")

    print(f"\n📦 Total estimated package size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    return total_size

def main():
    """Main verification function"""
    print("*** NRP K8s System Package Verification ***")
    print("=" * 50)

    checks = [
        ("Knowledge Bases", check_knowledge_bases),
        ("Templates", check_templates),
        ("Server Files", check_server_files),
        ("Configuration", check_configuration),
        ("Import Tests", test_imports),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append((check_name, False))

    # Package size analysis
    package_size = estimate_package_size()

    print("\n" + "=" * 50)
    print("📋 VERIFICATION RESULTS:")
    print("=" * 50)

    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False

    print(f"\nPackage Size: {package_size:,} bytes ({package_size/1024/1024:.1f} MB)")

    if all_passed:
        print("\n🎉 PACKAGE VERIFICATION SUCCESSFUL!")
        print("📦 All knowledge bases and resources are properly included")
        print("🚀 Ready for git commit and distribution")

        print("\n📋 Package includes:")
        print("  • Complete NRP knowledge base (1.4MB)")
        print("  • Comprehensive templates database")
        print("  • GPU resource specifications")
        print("  • Nautilus documentation cache")
        print("  • Web chat interface")
        print("  • FastMCP server with 14 tools")
        print("  • Automated setup and launcher scripts")

    else:
        print("\n⚠️ PACKAGE VERIFICATION FAILED!")
        print("🔧 Some components are missing or broken")
        print("💡 Run setup.py or check file permissions")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)