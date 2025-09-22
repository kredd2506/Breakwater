#!/usr/bin/env python3
"""
Quick Start Script for Ultimate FastMCP Server
==============================================
Simple script to verify setup and start the server.
"""

import subprocess
import sys
import os
import time

def check_python():
    """Check Python version"""
    print("1. Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n2. Checking dependencies...")
    required_packages = [
        'fastmcp',
        'kubernetes',
        'langchain-openai',
        'python-dotenv',
        'openai',
        'pydantic',
        'requests',
        'beautifulsoup4'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n   Install missing packages with:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True

def check_files():
    """Check if required files exist"""
    print("\n3. Checking required files...")

    required_files = [
        'ultimate_fastmcp_server.py',
        'test_k8s_infogent_integration.py',
        'test_nautilus_question.py'
    ]

    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
            missing.append(file)

    return len(missing) == 0

def check_port():
    """Check if port 8022 is available"""
    print("\n4. Checking port availability...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8022))
        sock.close()

        if result == 0:
            print("   ⚠️  Port 8022 is in use")
            print("      You may need to stop existing servers")
            return False
        else:
            print("   ✅ Port 8022 is available")
            return True
    except Exception as e:
        print(f"   ⚠️  Could not check port: {e}")
        return True

def start_server():
    """Start the Ultimate FastMCP server"""
    print("\n5. Starting Ultimate FastMCP Server...")
    print("   🚀 Launching server on http://127.0.0.1:8022/mcp")
    print("   📝 Check the output below for any errors")
    print("   🛑 Press Ctrl+C to stop the server")
    print("\n" + "="*60)

    try:
        subprocess.run([sys.executable, "ultimate_fastmcp_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
    except FileNotFoundError:
        print("\n❌ ultimate_fastmcp_server.py not found")

def main():
    """Main function"""
    print("🚀 Ultimate FastMCP Server - Quick Start")
    print("=" * 50)

    # Run all checks
    checks_passed = 0
    total_checks = 4

    if check_python():
        checks_passed += 1

    if check_dependencies():
        checks_passed += 1

    if check_files():
        checks_passed += 1

    if check_port():
        checks_passed += 1

    print(f"\n📊 Setup Check: {checks_passed}/{total_checks} passed")

    if checks_passed == total_checks:
        print("✅ All checks passed! Ready to start server.")

        response = input("\n🤔 Start the server now? (y/n): ").lower().strip()
        if response in ['y', 'yes', '']:
            start_server()
        else:
            print("\n📖 To start manually, run:")
            print("   python ultimate_fastmcp_server.py")

    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n📖 See SETUP_GUIDE.md for detailed instructions.")

    print("\n📝 Quick Test Commands:")
    print("   python test_k8s_infogent_integration.py")
    print("   python test_nautilus_question.py")

if __name__ == "__main__":
    main()