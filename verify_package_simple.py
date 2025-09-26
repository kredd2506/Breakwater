#!/usr/bin/env python3
"""
Package Verification Script for NRP K8s System (Unicode-safe version)
Verifies that all knowledge bases and resources are properly included
"""

import os
import sys
from pathlib import Path

def check_knowledge_bases():
    """Check if knowledge base files are present"""
    print("\n=== Checking Knowledge Bases ===")

    # MCP Cache Knowledge Files
    mcp_cache = Path("mcp/cache")
    critical_files = [
        "nrp_comprehensive_templates.py",
        "nrp_complete_anchor_db.py",
        "nrp_gpu_knowledge.py",
        "comprehensive_template_database.json"
    ]

    missing = 0
    total_size = 0

    for file in critical_files:
        file_path = mcp_cache / file
        if file_path.exists():
            size = file_path.stat().st_size
            total_size += size
            print(f"[OK] {file} ({size:,} bytes)")
        else:
            missing += 1
            print(f"[MISSING] {file}")

    print(f"\nMCP Knowledge Base Summary:")
    print(f"  - Files found: {len(critical_files) - missing}/{len(critical_files)}")
    print(f"  - Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

    return missing == 0

def check_server_files():
    """Check if server files exist"""
    print("\n=== Checking Server Files ===")

    server_files = [
        "web_chat_server.py",
        "mcp/ultimate_fastmcp_server.py",
        "start_web_server.py",
        "start_mcp_server.py",
        "setup.py",
        "requirements.txt"
    ]

    missing = 0
    for file in server_files:
        if Path(file).exists():
            print(f"[OK] {file}")
        else:
            print(f"[MISSING] {file}")
            missing += 1

    return missing == 0

def check_templates():
    """Check template files"""
    print("\n=== Checking Templates ===")

    template_files = ["templates/chat.html"]
    missing = 0

    for template in template_files:
        if Path(template).exists():
            print(f"[OK] {template}")
        else:
            print(f"[MISSING] {template}")
            missing += 1

    return missing == 0

def get_package_size():
    """Calculate package size"""
    print("\n=== Package Size Analysis ===")

    total_size = 0
    file_count = 0

    # Check key directories
    dirs_to_check = ["mcp/cache", "nrp_k8s_system/cache", "templates"]

    for dir_path in dirs_to_check:
        if Path(dir_path).exists():
            dir_size = 0
            dir_files = 0
            for file in Path(dir_path).rglob("*"):
                if file.is_file():
                    size = file.stat().st_size
                    dir_size += size
                    dir_files += 1

            total_size += dir_size
            file_count += dir_files
            print(f"  {dir_path}: {dir_size:,} bytes ({dir_files} files)")

    # Check root Python files
    root_files = list(Path(".").glob("*.py"))
    root_files.extend(list(Path(".").glob("*.md")))
    root_files.extend(list(Path(".").glob("*.txt")))

    root_size = sum(f.stat().st_size for f in root_files if f.exists())
    total_size += root_size
    print(f"  root files: {root_size:,} bytes ({len(root_files)} files)")

    print(f"\nTotal Package Size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print(f"Total Files: {file_count + len(root_files)}")

    return total_size

def main():
    """Main verification"""
    print("=" * 60)
    print("NRP K8s System Package Verification")
    print("=" * 60)

    # Run checks
    checks = [
        ("Knowledge Bases", check_knowledge_bases),
        ("Server Files", check_server_files),
        ("Templates", check_templates)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERROR] {name} check failed: {e}")
            results.append((name, False))

    # Get package size
    package_size = get_package_size()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: [{status}]")
        if not result:
            all_passed = False

    print(f"\nPackage Size: {package_size:,} bytes ({package_size/1024/1024:.1f} MB)")

    if all_passed:
        print("\n[SUCCESS] Package verification completed successfully!")
        print("All knowledge bases and resources are properly included.")
        print("\nPackage includes:")
        print("  - Complete NRP knowledge base")
        print("  - Comprehensive templates database")
        print("  - Web chat interface")
        print("  - FastMCP server with 14 tools")
        print("  - Automated setup scripts")
        print("\nReady for git distribution!")
    else:
        print("\n[WARNING] Some components are missing.")
        print("System will still work but with reduced functionality.")

    return all_passed

if __name__ == "__main__":
    success = main()
    print(f"\nExit code: {0 if success else 1}")
    sys.exit(0 if success else 1)