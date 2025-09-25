#!/usr/bin/env python3
"""
Live test of "describe the pods in my namespace" functionality
"""

import requests
import json
import time

def test_web_chat_k8s_commands():
    """Test the web chat K8s command functionality"""
    print("Testing Live Web Chat K8s Commands")
    print("=" * 50)

    base_url = "http://localhost:5000"
    session_id = f"test_session_{int(time.time())}"

    # Test commands
    test_queries = [
        "list pods",
        "describe the pods in my namespace",
        "get namespace"
    ]

    for query in test_queries:
        print(f"\n[TEST] Query: '{query}'")
        print("-" * 40)

        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "message": query,
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get('response', 'No response')

                # Check if it's a K8s command result
                if "Kubernetes Command Result:" in result:
                    print("[SUCCESS] Direct K8s command executed!")
                    print("Response:")
                    # Clean up the markdown formatting for display
                    clean_result = result.replace("🔧 **Kubernetes Command Result:**\n\n```\n", "")
                    clean_result = clean_result.replace("\n```", "")
                    print(clean_result[:500])  # First 500 chars
                    if len(clean_result) > 500:
                        print("... (truncated)")
                else:
                    print("[INFO] DeepSeek-R1 conversational response:")
                    print(result[:200] + "..." if len(result) > 200 else result)

            else:
                print(f"[ERROR] HTTP {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[ERROR] Request failed: {e}")

    print(f"\n[COMPLETE] Live functionality test finished")

def test_k8s_status():
    """Test K8s status endpoint"""
    print("\n[K8S STATUS] Checking Kubernetes integration status")
    print("-" * 50)

    try:
        response = requests.get("http://localhost:5000/api/k8s-status")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] K8s Available: {data.get('available')}")
            print(f"[OK] Namespace: {data.get('namespace')}")
            print(f"[OK] Available Commands: {len(data.get('commands', []))}")

            for cmd in data.get('commands', [])[:5]:  # Show first 5 commands
                print(f"     - {cmd}")
        else:
            print(f"[ERROR] Status check failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Status check error: {e}")

if __name__ == "__main__":
    print("Live System Test - 'describe the pods in my namespace'")
    print("Testing both MCP and Web Chat servers...")

    test_k8s_status()
    test_web_chat_k8s_commands()

    print("\nTo test in browser, go to: http://localhost:5000")
    print("Try typing: 'describe the pods in my namespace'")