#!/usr/bin/env python3
"""
System Status Checker for NRP K8s System
Quick health check for all components
"""

import sys
import socket
from pathlib import Path

def check_mark(condition, message):
    """Print check mark or X based on condition"""
    if condition:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False

def warning_mark(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version >= (3, 8):
        return check_mark(True, f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        return check_mark(False, f"Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")

def check_dependencies():
    """Check if key dependencies are installed"""
    dependencies = [
        ("flask", "Flask web framework"),
        ("fastmcp", "FastMCP server"),
        ("kubernetes", "Kubernetes client"),
        ("openai", "OpenAI client"),
        ("langchain_openai", "LangChain OpenAI"),
        ("requests", "HTTP requests"),
        ("pydantic", "Data validation"),
    ]

    all_good = True
    for package, description in dependencies:
        try:
            __import__(package)
            check_mark(True, f"{description}")
        except ImportError:
            check_mark(False, f"{description} - pip install {package}")
            all_good = False

    return all_good

def check_files():
    """Check if required files exist"""
    required_files = [
        ("web_chat_server.py", "Web server main file"),
        ("templates/chat.html", "Web interface template"),
        ("mcp/ultimate_fastmcp_server.py", "MCP server main file"),
        ("requirements.txt", "Dependencies list"),
        ("setup.py", "Setup script"),
        (".env.example", "Environment template"),
    ]

    all_good = True
    for file_path, description in required_files:
        path = Path(file_path)
        if check_mark(path.exists(), f"{description}"):
            continue
        else:
            all_good = False

    return all_good

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        check_mark(True, "Environment file (.env) exists")
    elif env_example.exists():
        warning_mark("No .env file, but template exists (will use demo mode)")
    else:
        check_mark(False, "No environment files found")

def check_ports():
    """Check if required ports are available"""
    ports = [
        (5000, "Web server port"),
        (8020, "MCP server port"),
    ]

    for port, description in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                check_mark(True, f"{description} ({port}) available")
        except OSError:
            warning_mark(f"{description} ({port}) in use (may conflict)")

def check_directories():
    """Check if required directories exist"""
    directories = [
        "templates",
        "mcp",
        "mcp/cache",
        "nrp_k8s_system",
    ]

    all_good = True
    for directory in directories:
        path = Path(directory)
        if not check_mark(path.exists(), f"Directory: {directory}"):
            all_good = False

    return all_good

def main():
    """Main system check"""
    print("🔍 NRP K8s System Status Check")
    print("=" * 50)

    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_files),
        ("Directories", check_directories),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Ports", check_ports),
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ Error checking {check_name}: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 System check completed successfully!")
        print("\n🚀 Ready to start:")
        print("   • Web Server: python start_web_server.py")
        print("   • MCP Server: python start_mcp_server.py")
        print("   • Quick Start: quick_start.bat (Windows) or ./quick_start.sh (Linux/macOS)")
    else:
        print("⚠️  System check found issues")
        print("\n🔧 To fix issues:")
        print("   1. Run: python setup.py")
        print("   2. Install missing dependencies")
        print("   3. Check file permissions")
        print("   4. Run this check again")

    print(f"\n📊 Status: {'READY' if all_passed else 'NEEDS ATTENTION'}")

if __name__ == "__main__":
    main()