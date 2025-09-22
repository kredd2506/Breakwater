#!/usr/bin/env python3
"""
Final Working Client - Enhanced GLM-4.5V Responses
================================================
This demonstrates the enhanced system you wanted with:
- Precise documentation links
- Comprehensive GLM-4.5V explanations
- Examples, warnings, step-by-step guidance
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastmcp import Client

class EnhancedNRPClient:
    def __init__(self):
        load_dotenv()
        self.glm_client = AsyncOpenAI(
            api_key=os.getenv("NRP_API_KEY"),
            base_url=os.getenv("NRP_BASE_URL")
        )

    async def get_enhanced_response(self, question):
        """Get both precise links AND comprehensive explanations"""
        print(f"\n[QUESTION] {question}")
        print("=" * 70)

        try:
            # Step 1: Get precise documentation link with enhanced query for specific GPUs
            enhanced_question = question
            if any(gpu in question.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                enhanced_question = question + " special GPU type specific"

            async with Client("http://localhost:8024/mcp") as client:
                link_result = await client.call_tool("intelligent_k8s_query", {
                    "params": {"query": enhanced_question, "context": "Link retrieval"}
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

            # Enhanced prompt for specific GPU types
            gpu_specific_guidance = ""
            if any(gpu in question.lower() for gpu in ['a100', 'h100', 'v100', 'rtx4090']):
                gpu_specific_guidance = f"""

CRITICAL: For specific GPU requests like A100, H100, V100, or RTX4090, you MUST include:
- The exact resource specification syntax: nvidia.com/a100 (for A100), nvidia.com/h100 (for H100), etc.
- How to request specific GPU types vs. generic GPUs
- Resource limits and availability constraints for high-end GPUs
- Performance characteristics and use cases for the specific GPU type"""

            explanation_prompt = f'''You are an expert NRP Nautilus platform specialist. Provide a comprehensive, detailed explanation for this query: "{question}"

Based on the precise documentation found at: {precise_link}

Please provide:
1. A clear, detailed explanation of the topic
2. Step-by-step instructions when applicable
3. Code examples or YAML configurations if relevant
4. Best practices and common pitfalls
5. Related concepts the user should know
6. Troubleshooting tips and warnings
7. Specific resource requirements and limits{gpu_specific_guidance}

Make your response comprehensive yet practical, focusing on actionable guidance that goes beyond just pointing to documentation.'''

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

## Additional Resources
- Complete NRP Documentation: https://nrp.ai/documentation/
- Support: NRP Slack/Support channels

---
*Response powered by GLM-4.5V multimodal AI with 65,536 token context*
*Precision link retrieval + comprehensive explanation*'''

            print("[ENHANCED RESPONSE]")
            print(enhanced_response)

        except Exception as e:
            print(f"[ERROR] {e}")

async def main():
    """Demo the enhanced responses you wanted"""
    client = EnhancedNRPClient()

    # Test questions that need comprehensive explanations
    questions = [
        "How do I request an A100 GPU with 8 cores and 32GB RAM?",
        "What storage options are available and how do I use persistent volumes?",
        "How do I expose my service with a custom domain using ingress?",
        "What are the resource allocation policies and limits?",
        "How do I troubleshoot pod startup issues and common errors?"
    ]

    print("=" * 70)
    print("ENHANCED NRP K8s SYSTEM - GLM-4.5V POWERED")
    print("Precise Links + Comprehensive Explanations")
    print("=" * 70)

    for i, question in enumerate(questions, 1):
        print(f"\n[DEMO {i}/5]")
        await client.get_enhanced_response(question)

        if i < len(questions):
            input("\nPress Enter for next demo...")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE - This is the enhanced system you wanted!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())