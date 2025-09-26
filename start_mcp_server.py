#!/usr/bin/env python3
"""
MCP Server Launcher for NRP K8s System
Starts the FastMCP server with proper error handling and configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required files and dependencies exist"""
    # Check if MCP directory exists
    mcp_dir = Path("mcp")
    if not mcp_dir.exists():
        print("❌ mcp/ directory not found!")
        print("   Make sure you're in the correct directory")
        return False

    # Check if main server file exists
    server_file = mcp_dir / "ultimate_fastmcp_server.py"
    if not server_file.exists():
        print("❌ mcp/ultimate_fastmcp_server.py not found!")
        return False

    # Try importing fastmcp
    try:
        import fastmcp
        print("✅ FastMCP is available")
    except ImportError:
        print("❌ FastMCP not installed!")
        print("   Run: pip install -r requirements.txt")
        return False

    return True

def check_port(port=8020):
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            print(f"✅ Port {port} is available")
            return True
    except OSError:
        print(f"⚠️  Port {port} is in use")
        print(f"   You can:")
        print(f"   1. Kill the process using the port")
        print(f"   2. Edit ultimate_fastmcp_server.py to use a different port")
        return False

def start_server():
    """Start the MCP server"""
    print("🚀 Starting NRP K8s MCP Server...")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed!")
        return False

    # Check port availability
    if not check_port():
        print("\n⚠️  Port issue detected - server may still work")

    # Load environment variables
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Loading environment from .env")
    else:
        print("⚠️  No .env file found - using demo mode")

    # Check for NRP knowledge base
    cache_dir = Path("mcp/cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.py"))
        if cache_files:
            print(f"✅ Found {len(cache_files)} knowledge base files")
        else:
            print("⚠️  No knowledge base files found - using demo data")
    else:
        print("⚠️  Cache directory not found - creating it")
        cache_dir.mkdir(parents=True, exist_ok=True)

    print("\n🔧 Starting FastMCP server...")
    print("   MCP endpoint: http://localhost:8020/mcp")
    print("   Available tools: 14 total (8 K8s + 6 FastMCP)")
    print("   Use Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Change to mcp directory and start the server
        os.chdir("mcp")
        subprocess.run([sys.executable, "ultimate_fastmcp_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 MCP Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ MCP Server failed to start: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Python not found! Make sure Python is in your PATH")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

    return True

def main():
    """Main function"""
    print("NRP K8s System - MCP Server Launcher")
    print("=" * 40)

    success = start_server()

    if not success:
        print("\n🆘 Troubleshooting:")
        print("1. Run: python setup.py")
        print("2. Check: pip install -r requirements.txt")
        print("3. Verify: mcp/ultimate_fastmcp_server.py exists")
        print("4. Try: cd mcp && python ultimate_fastmcp_server.py")
        print("5. Check the MCP setup guide: mcp/SETUP_GUIDE.md")
        sys.exit(1)

if __name__ == "__main__":
    main()