#!/usr/bin/env python3
"""
Web Server Launcher for NRP K8s System
Starts the Flask web server with proper error handling and configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required files and dependencies exist"""
    # Check if main server file exists
    if not Path("web_chat_server.py").exists():
        print("❌ web_chat_server.py not found!")
        print("   Make sure you're in the correct directory")
        return False

    # Check if templates exist
    if not Path("templates/chat.html").exists():
        print("❌ templates/chat.html not found!")
        print("   Web interface will not work correctly")
        return False

    # Try importing flask
    try:
        import flask
        print("✅ Flask is available")
    except ImportError:
        print("❌ Flask not installed!")
        print("   Run: pip install -r requirements.txt")
        return False

    return True

def check_port(port=5000):
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
        print(f"   2. Edit web_chat_server.py to use a different port")
        return False

def start_server():
    """Start the web server"""
    print("🚀 Starting NRP K8s Web Server...")
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

    print("\n🌐 Starting Flask web server...")
    print("   Web interface: http://localhost:5000")
    print("   Use Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Start the server
        subprocess.run([sys.executable, "web_chat_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Python not found! Make sure Python is in your PATH")
        return False

    return True

def main():
    """Main function"""
    print("NRP K8s System - Web Server Launcher")
    print("=" * 40)

    success = start_server()

    if not success:
        print("\n🆘 Troubleshooting:")
        print("1. Run: python setup.py")
        print("2. Check: pip install -r requirements.txt")
        print("3. Verify: templates/chat.html exists")
        print("4. Try: python web_chat_server.py directly")
        sys.exit(1)

if __name__ == "__main__":
    main()