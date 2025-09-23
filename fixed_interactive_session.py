#!/usr/bin/env python3
"""
Fixed Interactive Session for Gradio UI
Returns results instead of just printing them
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastmcp import Client

# Add MCP path
mcp_path = Path(__file__).parent / "mcp"
sys.path.append(str(mcp_path))

class FixedInteractiveNRPSession:
    def __init__(self):
        load_dotenv()
        self.glm_client = AsyncOpenAI(
            api_key=os.getenv("NRP_API_KEY"),
            base_url=os.getenv("NRP_BASE_URL")
        )

    async def classify_intent(self, user_input):
        """Classify user intent using GLM-4.5V"""
        try:
            classification_prompt = f'''Analyze this user input and classify the intent as one of these categories:

QUESTION: User wants information, explanation, or documentation about NRP Nautilus, Kubernetes, or related topics
COMMAND: User wants to perform a Kubernetes operation (list, get, describe, create, delete resources)
QUIT: User wants to exit or stop

User input: "{user_input}"

Respond with ONLY the category name (QUESTION, COMMAND, or QUIT) and nothing else.

Examples:
"How do I request GPUs?" -> QUESTION
"List my pods" -> COMMAND
"Get cluster info" -> COMMAND
"What is persistent storage?" -> QUESTION
"exit" -> QUIT
"describe pod myapp" -> COMMAND'''

            response = await self.glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond with only the category name: QUESTION, COMMAND, or QUIT."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )

            intent = response.choices[0].message.content.strip().upper()

            # Fallback keyword-based classification if GLM response is unclear
            if intent not in ['QUESTION', 'COMMAND', 'QUIT']:
                user_lower = user_input.lower()
                if any(word in user_lower for word in ['quit', 'exit', 'stop', 'bye']):
                    intent = 'QUIT'
                elif any(word in user_lower for word in ['list', 'get', 'describe', 'create', 'delete', 'kubectl', 'show me']):
                    intent = 'COMMAND'
                else:
                    intent = 'QUESTION'

            return intent

        except Exception as e:
            # Fallback to keyword-based classification
            user_lower = user_input.lower()
            if any(word in user_lower for word in ['quit', 'exit', 'stop', 'bye']):
                return 'QUIT'
            elif any(word in user_lower for word in ['list', 'get', 'describe', 'create', 'delete', 'kubectl', 'show me']):
                return 'COMMAND'
            else:
                return 'QUESTION'

    async def ask_question(self, question):
        """Get both precise links AND comprehensive explanations - RETURNS result"""
        try:
            # Step 1: Get precise documentation link with enhanced query for A100
            enhanced_question = question
            if any(gpu in question.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                enhanced_question = question + " special GPU type specific"

            try:
                async with Client("http://localhost:8024/mcp") as client:
                    # Use the ultra-comprehensive anchor database directly
                    link_result = await client.call_tool("intelligent_k8s_query", {
                        "params": {"query": enhanced_question, "context": "Interactive session with infogent architecture"}
                    })

                # Extract the precise link
                response_text = link_result.data
                if "**Direct Link**:" in response_text:
                    lines = response_text.split('\n')
                    for line in lines:
                        if "**Direct Link**:" in line:
                            precise_link = line.replace("**Direct Link**: ", "").strip()
                            break
                    else:
                        precise_link = "https://nrp.ai/documentation/"
                else:
                    precise_link = "https://nrp.ai/documentation/"
            except Exception as e:
                # Fallback if MCP server not available
                precise_link = "https://nrp.ai/documentation/"
                response_text = f"MCP Server not available: {str(e)}"

            # Step 2: Generate comprehensive explanation with GLM-4.5V
            explanation_prompt = f'''You are an expert NRP Nautilus platform specialist. Provide a comprehensive, detailed explanation for this query: "{question}"

Based on the precise documentation found at: {precise_link}

Please provide:
1. A clear, detailed explanation of the topic
2. Step-by-step instructions when applicable
3. Code examples or YAML configurations if relevant
4. Best practices and common pitfalls
5. Related concepts the user should know
6. Troubleshooting tips and warnings
7. Specific resource requirements and limits

Make your response comprehensive yet practical, focusing on actionable guidance.'''

            response = await self.glm_client.chat.completions.create(
                model=os.getenv("NRP_MODEL", "glm-v"),
                messages=[
                    {"role": "system", "content": "You are an expert NRP Nautilus Kubernetes platform specialist with deep knowledge of all NRP documentation, policies, and best practices. Provide comprehensive, actionable explanations with examples and warnings."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            comprehensive_explanation = response.choices[0].message.content

            # Step 3: Format enhanced response
            enhanced_response = f'''# NRP Nautilus Documentation - Enhanced Response

## Precise Documentation Match
**Direct Link**: {precise_link}
**Query**: {question}

## Comprehensive Explanation
{comprehensive_explanation}

---
*Response powered by GLM-4.5V multimodal AI with 65,536 token context*
*Precision link retrieval + comprehensive explanation*'''

            return enhanced_response

        except Exception as e:
            return f"Error processing question: {str(e)}"

    async def process_k8s_command(self, user_input):
        """Process K8s command using natural language - RETURNS result"""
        try:
            async with Client("http://localhost:8024/mcp") as client:
                # Use intelligent_k8s_query for command processing
                result = await client.call_tool("intelligent_k8s_query", {
                    "params": {"query": user_input, "context": "K8s command execution"}
                })
                return result.data
        except Exception as e:
            return f"K8s command processing error: {str(e)}\n\nNote: This would work in deployment when MCP server is running properly."