#!/usr/bin/env python3
"""
Your Interactive Testing Session
===============================
Ask any questions and see both precise links and comprehensive GLM-4.5V explanations
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastmcp import Client

class InteractiveNRPSession:
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

QUESTION: User wants information, explanation, documentation, examples, or tutorials about NRP Nautilus, Kubernetes, or related topics
COMMAND: User wants to perform a live Kubernetes operation (list actual resources, get running pods, describe existing deployments, create/delete real resources)
QUIT: User wants to exit or stop

User input: "{user_input}"

Respond with ONLY the category name (QUESTION, COMMAND, or QUIT) and nothing else.

Examples:
"How do I request GPUs?" -> QUESTION
"Show me YAML example for A100 GPU" -> QUESTION
"Give me pod template" -> QUESTION
"What is persistent storage?" -> QUESTION
"List my pods" -> COMMAND
"Get cluster info" -> COMMAND
"Describe pod myapp" -> COMMAND
"exit" -> QUIT'''

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
                # CRITICAL: Only classify as COMMAND for actual K8s operations, NOT documentation requests
                elif any(phrase in user_lower for phrase in ['list my pods', 'list pods', 'get pods', 'describe pod', 'delete pod', 'create pod', 'kubectl']) and not any(doc_word in user_lower for doc_word in ['example', 'yaml', 'template', 'how to', 'show me']):
                    intent = 'COMMAND'
                else:
                    intent = 'QUESTION'

            return intent

        except Exception as e:
            print(f"[INTENT ERROR] {e}")
            # Fallback to keyword-based classification
            user_lower = user_input.lower()
            if any(word in user_lower for word in ['quit', 'exit', 'stop', 'bye']):
                return 'QUIT'
            # CRITICAL: Only classify as COMMAND for actual K8s operations, NOT documentation requests
            elif any(phrase in user_lower for phrase in ['list my pods', 'list pods', 'get pods', 'describe pod', 'delete pod', 'create pod', 'kubectl']) and not any(doc_word in user_lower for doc_word in ['example', 'yaml', 'template', 'how to', 'show me']):
                return 'COMMAND'
            else:
                return 'QUESTION'

    async def ask_question(self, question):
        """Get both precise links AND comprehensive explanations"""
        print(f"\n[YOUR QUESTION] {question}")
        print("=" * 70)

        try:
            # Step 1: Get precise documentation link with enhanced query for A100
            enhanced_question = question
            if any(gpu in question.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                enhanced_question = question + " special GPU type specific"

            async with Client("http://localhost:8025/mcp") as client:
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

            # Step 2: Generate comprehensive explanation with GLM-4.5V
            print("[GENERATING] Comprehensive explanation with GLM-4.5V...")

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

            print("[ANSWER]")
            print(enhanced_response)

        except Exception as e:
            print(f"[ERROR] {e}")

    async def process_k8s_command(self, user_input):
        """Process K8s command using natural language"""
        print(f"\n[K8S COMMAND] {user_input}")
        print("-" * 40)

        try:
            async with Client("http://localhost:8025/mcp") as client:
                # Use intelligent_k8s_query for command processing
                result = await client.call_tool("intelligent_k8s_query", {
                    "params": {"query": user_input, "context": "K8s command execution"}
                })
                print(result.data)
        except Exception as e:
            print(f"[ERROR] {e}")

    async def run_k8s_operation(self, operation, **params):
        """Run K8s operations"""
        print(f"\n[K8S OPERATION] {operation}")
        print("-" * 40)

        try:
            async with Client("http://localhost:8025/mcp") as client:
                result = await client.call_tool(operation, params)
                print(result.data)
        except Exception as e:
            print(f"[ERROR] {e}")

async def main():
    """Interactive testing session with automatic intent classification"""
    session = InteractiveNRPSession()

    print("=" * 70)
    print("NRP K8s INTERACTIVE SESSION - GLM-4.5V POWERED")
    print("Automatic Intent Classification - Just type naturally!")
    print("Examples:")
    print("  'How do I request GPUs?' -> Documentation + Explanation")
    print("  'List my pods' -> K8s Command")
    print("  'quit' -> Exit")
    print("=" * 70)

    while True:
        try:
            # Get user input naturally
            user_input = input("\n> ").strip()

            if not user_input:
                print("Please enter something.")
                continue

            # Classify intent automatically
            print(f"[ANALYZING] {user_input}")
            intent = await session.classify_intent(user_input)
            print(f"[INTENT] {intent}")

            if intent == 'QUIT':
                print("\nGoodbye! Session ended.")
                break

            elif intent == 'QUESTION':
                await session.ask_question(user_input)

            elif intent == 'COMMAND':
                await session.process_k8s_command(user_input)

            else:
                print(f"[UNCLEAR] Treating as question: {user_input}")
                await session.ask_question(user_input)

        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())