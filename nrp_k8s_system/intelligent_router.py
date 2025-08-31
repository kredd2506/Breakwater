#!/usr/bin/env python3
"""
Intelligent NRP + K8s Router
============================

A smart routing system that determines user intent and routes to appropriate handlers:
1. Command Detection: Routes kubectl/k8s operational commands to k8s_operations.py
2. Question/Explanation: Routes documentation questions to NRP+K8s hybrid system

Architecture:
- Intent Classification Agent: Analyzes user input to determine command vs question
- Command Handler: Executes K8s operations using existing k8s_operations.py
- Explanation Handler: Provides comprehensive guidance using NRP+K8s hybrid
- Isolated Caches: Each component maintains separate cache to avoid corruption

Usage:
  python -m nrp_k8s_system.intelligent_router "list my pods"           # -> K8s Command
  python -m nrp_k8s_system.intelligent_router "How do I request GPUs?" # -> NRP+K8s Explanation
  python -m nrp_k8s_system.intelligent_router                          # -> Interactive mode
"""

import os
import sys
import subprocess
import json
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Import from package
from .core.nrp_init import init_chat_model

# ----------------------- Configuration -----------------------

# Paths - use package-relative paths
PACKAGE_DIR = Path(__file__).parent
CACHE_DIR = PACKAGE_DIR / "cache" / "router_cache"
TIMEOUT_SECONDS = 300

# ----------------------- Intent Classification -----------------------

class UserIntent(Enum):
    COMMAND = "command"        # K8s operational commands (list, get, create, etc.)
    EXPLANATION = "explanation" # Documentation, how-to questions
    UNCLEAR = "unclear"        # Ambiguous intent

@dataclass
class RouterDecision:
    intent: UserIntent
    confidence: float
    reasoning: str
    suggested_handler: str

def classify_user_intent(user_input: str) -> RouterDecision:
    """
    Classify user input to determine if it's a command or explanation request
    """
    try:
        print("[*] Analyzing user intent...")
        chat_model = init_chat_model()
        
        classification_prompt = f"""
You are an intelligent router for an NRP (National Research Platform) + Kubernetes system.
Analyze the user input and classify their intent.

User Input: "{user_input}"

INTENT CATEGORIES:
1. COMMAND: User wants to execute a Kubernetes operation
   - Examples: "list pods", "get my services", "delete pod xyz", "show deployments"
   - Keywords: list, get, show, delete, create, apply, describe, logs, exec
   - Action-oriented requests for current cluster state or operations

2. EXPLANATION: User wants documentation, guidance, or how-to information  
   - Examples: "How do I request GPUs?", "What are best practices for storage?"
   - Questions about setup, configuration, troubleshooting, best practices
   - Learning-oriented requests for knowledge and guidance

Respond with JSON only:
{{
    "intent": "command" or "explanation" or "unclear",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification decision",
    "suggested_handler": "k8s_operations" or "nrp_hybrid" or "clarification_needed"
}}
"""
        
        response = chat_model.invoke(classification_prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response.content.strip())
            return RouterDecision(
                intent=UserIntent(result["intent"]),
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                suggested_handler=result["suggested_handler"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[!] Error parsing classification result: {e}")
            # Fallback: simple keyword-based classification
            return fallback_classification(user_input)
            
    except Exception as e:
        print(f"[!] Error in intent classification: {e}")
        return fallback_classification(user_input)

def fallback_classification(user_input: str) -> RouterDecision:
    """
    Fallback classification using simple keyword matching
    """
    input_lower = user_input.lower()
    
    # Command keywords
    command_keywords = [
        'list', 'get', 'show', 'describe', 'delete', 'create', 'apply',
        'exec', 'logs', 'scale', 'restart', 'rollout', 'port-forward'
    ]
    
    # Question keywords
    question_keywords = [
        'how', 'what', 'why', 'when', 'where', 'best practice',
        'guide', 'tutorial', 'help', 'explain', 'setup', 'configure'
    ]
    
    command_score = sum(1 for kw in command_keywords if kw in input_lower)
    question_score = sum(1 for kw in question_keywords if kw in input_lower)
    
    if command_score > question_score:
        return RouterDecision(
            intent=UserIntent.COMMAND,
            confidence=0.7,
            reasoning=f"Contains command keywords: {[kw for kw in command_keywords if kw in input_lower]}",
            suggested_handler="k8s_operations"
        )
    elif question_score > 0:
        return RouterDecision(
            intent=UserIntent.EXPLANATION,
            confidence=0.7,
            reasoning=f"Contains question keywords: {[kw for kw in question_keywords if kw in input_lower]}",
            suggested_handler="nrp_hybrid"
        )
    else:
        return RouterDecision(
            intent=UserIntent.UNCLEAR,
            confidence=0.3,
            reasoning="No clear indicators of command or question intent",
            suggested_handler="clarification_needed"
        )

# ----------------------- Handler Functions -----------------------

def handle_k8s_command(user_input: str) -> Tuple[str, bool]:
    """
    Execute K8s operations by importing and calling k8s_operations functions directly
    """
    try:
        print("[*] Executing K8s command...")
        
        # Import k8s_operations from systems module
        from .systems import k8s_operations
        
        # Parse command and route to appropriate function
        user_input_lower = user_input.lower()
        
        if "list" in user_input_lower or "get" in user_input_lower or "show" in user_input_lower:
            if "pod" in user_input_lower:
                result = k8s_operations.list_pods()
                return f"Pods in namespace 'gsoc':\n{result}", True
            elif "service" in user_input_lower:
                result = k8s_operations.list_services()
                return f"Services in namespace 'gsoc':\n{result}", True
            elif "deployment" in user_input_lower:
                result = k8s_operations.list_deployments()
                return f"Deployments in namespace 'gsoc':\n{result}", True
            elif "job" in user_input_lower:
                result = k8s_operations.list_jobs()
                return f"Jobs in namespace 'gsoc':\n{result}", True
            elif "configmap" in user_input_lower:
                result = k8s_operations.list_configmaps()
                return f"ConfigMaps in namespace 'gsoc':\n{result}", True
            elif "secret" in user_input_lower:
                result = k8s_operations.list_secrets()
                return f"Secrets in namespace 'gsoc':\n{result}", True
            elif "pvc" in user_input_lower or "volume" in user_input_lower:
                result = k8s_operations.list_pvcs()
                return f"PVCs in namespace 'gsoc':\n{result}", True
            elif "event" in user_input_lower:
                result = k8s_operations.list_events()
                return f"Events in namespace 'gsoc':\n{result}", True
            elif "node" in user_input_lower:
                result = k8s_operations.list_nodes()
                return f"Nodes in cluster:\n{result}", True
            else:
                return "Available list commands: pods, services, deployments, jobs, configmaps, secrets, pvcs, events, nodes", True
        
        elif "describe" in user_input_lower:
            # Extract resource name for describe commands
            words = user_input.split()
            if len(words) >= 3:  # e.g., "describe pod myapp"
                resource_type = words[1].lower()
                resource_name = words[2]
                
                if resource_type == "pod":
                    result = k8s_operations.describe_pod(resource_name)
                    return f"Pod '{resource_name}' details:\n{result}", True
                elif resource_type == "service":
                    result = k8s_operations.describe_service(resource_name)
                    return f"Service '{resource_name}' details:\n{result}", True
                else:
                    return f"Describe not yet supported for resource type: {resource_type}", True
            else:
                return "Please specify resource type and name: 'describe pod <name>' or 'describe service <name>'", True
        
        else:
            # Fallback: suggest available commands
            return """Available K8s commands:
- list/get/show pods
- list/get/show services  
- list/get/show deployments
- list/get/show jobs
- list/get/show configmaps
- list/get/show secrets
- list/get/show pvcs
- list/get/show events
- list/get/show nodes
- describe pod <name>
- describe service <name>

Example: 'list my pods' or 'describe pod myapp'""", True
            
    except Exception as e:
        return f"Error executing K8s command: {str(e)}", False

def handle_nrp_explanation(user_input: str) -> Tuple[str, bool]:
    """
    Provide explanations using NRP LLM with contextual examples
    """
    try:
        print("[*] Generating NRP+K8s explanation...")
        
        chat_model = init_chat_model()
        
        explanation_prompt = f"""
You are an expert NRP (National Research Platform) + Kubernetes guide.
Provide comprehensive guidance for this user question: "{user_input}"

Context:
- User is working in the 'gsoc' namespace
- Available resources: A100 GPUs, persistent storage, networking
- Common operations: pod management, job scheduling, storage setup, GPU allocation

Please provide:
1. Direct answer to the user's question
2. Step-by-step instructions where applicable
3. Practical kubectl commands they can run
4. Best practices and considerations
5. Common troubleshooting tips

Be specific, actionable, and focused on NRP/K8s context.
"""
        
        response = chat_model.invoke(explanation_prompt)
        base_response = response.content.strip()
        
        # Add contextual example based on user input
        contextual_example = generate_contextual_example(user_input)
        
        if contextual_example:
            enhanced_response = f"{base_response}\n\n{contextual_example}"
            return enhanced_response, True
        else:
            return base_response, True
            
    except Exception as e:
        return f"Error generating explanation: {str(e)}", False

def generate_contextual_example(user_input: str) -> str:
    """
    Generate a contextual example based on the user's specific input
    """
    try:
        print("[*] Generating contextual example...")
        chat_model = init_chat_model()
        
        example_prompt = f"""
Based on this user question about NRP/Kubernetes: "{user_input}"

Generate a practical, executable example that directly addresses their question. The example should:
1. Be specific to their exact scenario
2. Include actual kubectl commands they can run
3. Show realistic YAML configurations
4. Use NRP-specific context (gsoc namespace, available GPUs, etc.)

Format your response as:

**[*] Practical Example Based on Your Question:**

[Your contextual example here - be specific and actionable]

Keep it concise but practical. Focus on what they can actually do right now.
"""
        
        response = chat_model.invoke(example_prompt)
        return response.content.strip()
        
    except Exception as e:
        print(f"[!] Error generating contextual example: {e}")
        # Fallback: provide basic example based on keywords
        return generate_fallback_example(user_input)

def looks_like_question(user_input: str) -> bool:
    """
    Check if the input looks like a question even if intent classification failed
    """
    input_lower = user_input.lower()
    
    # Question patterns
    question_patterns = [
        # Question words
        'should', 'would', 'could', 'can', 'will', 'is', 'are', 'do', 'does', 'did',
        'how', 'what', 'why', 'when', 'where', 'which', 'who',
        # Question phrases
        'best practice', 'recommend', 'suggest', 'advice', 'guidance', 'help',
        'difference between', 'vs', 'versus', 'compare', 'better',
        'explain', 'understand', 'learn', 'know', 'tell me'
    ]
    
    # Check for question patterns
    for pattern in question_patterns:
        if pattern in input_lower:
            return True
    
    # Check if ends with question mark
    if user_input.strip().endswith('?'):
        return True
    
    # Check for comparative/choice patterns
    comparative_patterns = ['or', 'vs', 'versus', 'better than', 'instead of']
    if any(pattern in input_lower for pattern in comparative_patterns):
        return True
    
    return False

def generate_fallback_example(user_input: str) -> str:
    """
    Generate a simple fallback example based on keyword matching
    """
    input_lower = user_input.lower()
    
    if "gpu" in input_lower:
        return """
**[*] Practical Example Based on Your Question:**

Here's how you can request an A100 GPU for your workload:

```bash
# First, check available nodes with GPUs
kubectl get nodes -L nvidia.com/gpu.product

# Create a pod with A100 GPU
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: my-gpu-pod
  namespace: gsoc
spec:
  containers:
  - name: pytorch-container
    image: pytorch/pytorch:latest
    resources:
      limits:
        nvidia.com/a100: 1
      requests:
        nvidia.com/a100: 1
    command: ["python", "-c", "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"]
EOF
```
"""
    
    elif "storage" in input_lower or "volume" in input_lower:
        return """
**[*] Practical Example Based on Your Question:**

Here's how you can set up persistent storage in the gsoc namespace:

```bash
# Create a PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data-pvc
  namespace: gsoc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

# Use it in a pod
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: storage-pod
  namespace: gsoc
spec:
  containers:
  - name: app
    image: alpine
    volumeMounts:
    - name: data
      mountPath: /data
    command: ["sh", "-c", "echo 'Hello from persistent storage!' > /data/test.txt && sleep 3600"]
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-data-pvc
EOF
```
"""
    
    else:
        return """
**[*] Practical Example Based on Your Question:**

Here are some commands you can run to explore your current NRP environment:

```bash
# Check your current context and namespace
kubectl config current-context
kubectl config view --minify

# List resources in gsoc namespace
kubectl get all -n gsoc
kubectl get pvc,secrets,configmaps -n gsoc

# Check available nodes and their capabilities
kubectl get nodes
kubectl describe nodes
```
"""

def handle_unclear_intent(user_input: str) -> Tuple[str, bool]:
    """
    Handle unclear user intent by asking for clarification
    """
    clarification = f"""
I'm not sure if you want to:
1. **Execute a K8s command** (like "list pods", "get services", "describe deployment xyz")
2. **Get documentation/explanation** (like "How do I set up storage?", "What are GPU best practices?")

Your input: "{user_input}"

Could you please clarify? You can:
- Be more specific about the action you want to take
- Use command words like "list", "get", "show" for operations  
- Use question words like "how", "what", "explain" for guidance

Examples:
- "list my pods" → I'll show your current pods
- "How do I list pods?" → I'll explain the process and provide documentation
"""
    return clarification, True

# ----------------------- Main Router Logic -----------------------

def intelligent_route(user_input: str) -> str:
    """
    Main routing function that analyzes intent and routes to appropriate handler
    """
    print(f"[*] Processing: {user_input}")
    
    # Step 1: Classify user intent
    decision = classify_user_intent(user_input)
    print(f"[*] Intent: {decision.intent.value} (confidence: {decision.confidence:.2f})")
    print(f"[*] Reasoning: {decision.reasoning}")
    print(f"[*] Handler: {decision.suggested_handler}")
    
    # Step 2: Route to appropriate handler with smart fallback
    if decision.intent == UserIntent.COMMAND:
        response, success = handle_k8s_command(user_input)
        if success:
            return f"[K8s Command Executed]\n{'-'*50}\n{response}"
        else:
            return f"[K8s Command Failed]\n{'-'*50}\n{response}"
            
    elif decision.intent == UserIntent.EXPLANATION:
        response, success = handle_nrp_explanation(user_input)
        if success:
            return f"[NRP+K8s Guidance]\n{'-'*50}\n{response}"
        else:
            return f"[Explanation Failed]\n{'-'*50}\n{response}"
            
    else:  # UNCLEAR - but try explanation first for low confidence questions
        # If confidence is low but input looks like a question, try explanation
        if decision.confidence <= 0.4 and looks_like_question(user_input):
            print(f"[*] Low confidence ({decision.confidence:.2f}) but appears to be a question - trying explanation...")
            response, success = handle_nrp_explanation(user_input)
            if success:
                return f"[NRP+K8s Guidance - Auto-routed]\n{'-'*50}\n{response}"
            else:
                return f"[Explanation Failed - Fallback to clarification]\n{'-'*50}\n{response}"
        else:
            response, success = handle_unclear_intent(user_input)
            return f"[Clarification Needed]\n{'-'*50}\n{response}"

# ----------------------- Interactive Mode -----------------------

def interactive_mode():
    """
    Interactive chat mode for the intelligent routing system
    """
    print("[*] Intelligent NRP + K8s System")
    print("Routes commands to K8s operations, explanations to NRP+K8s hybrid")
    print("Type 'exit', 'quit', or 'bye' to exit\n")
    
    while True:
        try:
            user_input = input("[?] Your request: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("[*] Goodbye!")
                break
            
            if not user_input:
                continue
            
            print()  # Empty line
            response = intelligent_route(user_input)
            print(response)
            print("\n" + "="*80 + "\n")  # Separator
            
        except KeyboardInterrupt:
            print("\n[*] Goodbye!")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

# ----------------------- Main Entry Point -----------------------

def main():
    """Main entry point"""
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    if len(sys.argv) > 1:
        # Single request mode
        user_input = " ".join(sys.argv[1:])
        response = intelligent_route(user_input)
        print(response)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()