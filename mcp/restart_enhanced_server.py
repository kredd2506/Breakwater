#!/usr/bin/env python3
"""
Restart Enhanced Server Script
=============================
Properly restarts the server with GLM-4.5V integration
"""

import subprocess
import time
import requests
import os

def check_server_health(port=8025):
    """Check if server is responding"""
    try:
        response = requests.get(f"http://localhost:{port}/mcp", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_enhanced_server():
    """Start the enhanced server on port 8025"""
    print("=" * 60)
    print("STARTING ENHANCED GLM-4.5V SERVER")
    print("=" * 60)

    print("[1] Starting enhanced server on port 8025...")

    # Modify the server to use port 8025
    server_script = '''
import sys
sys.path.insert(0, "D:/Gsoc Gitlab/ocean/breakwater")

# Import and run with modified port
exec(open("ultimate_fastmcp_server.py").read().replace("port=8024", "port=8025"))
'''

    with open("enhanced_server_8025.py", "w") as f:
        f.write(server_script)

    # Start the server
    process = subprocess.Popen([
        "python", "enhanced_server_8025.py"
    ], cwd="D:/Gsoc Gitlab/ocean/breakwater/mcp")

    print("[2] Waiting for server to start...")
    for i in range(30):  # Wait up to 30 seconds
        if check_server_health(8025):
            print(f"[3] Enhanced server ready on port 8025!")
            return True
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")

    print("[ERROR] Server failed to start within 30 seconds")
    return False

if __name__ == "__main__":
    if start_enhanced_server():
        print("\n" + "=" * 60)
        print("SUCCESS! Enhanced GLM-4.5V server is running on port 8025")
        print("=" * 60)
        print("Now run: python your_interactive_session.py")
        print("(And edit it to use port 8025 instead of 8024)")
    else:
        print("Failed to start enhanced server")