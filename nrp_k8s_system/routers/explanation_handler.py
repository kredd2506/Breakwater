#!/usr/bin/env python3
"""
Explanation Handler Module for NRP K8s System
=============================================

Handles explanation requests by providing comprehensive guidance using NRP LLM
with contextual examples, policies, and best practices.
"""

from typing import Tuple, List
from ..core.nrp_init import init_chat_model
from ..systems.nautilus_docs_scraper import (
    get_policies_for_topic, format_policy_warning,
    get_yaml_examples, get_yaml_template
)


def handle_nrp_explanation(user_input: str) -> Tuple[str, bool]:
    """
    Provide explanations using NRP LLM with contextual examples.

    Args:
        user_input: User question/request string

    Returns:
        Tuple of (response_message, success_flag)
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

CRITICAL - ALWAYS include relevant warnings and cautions:
- Using sleep commands in batch jobs can result in account suspension/banning from Nautilus
- Resource abuse (holding GPUs without computation) is strictly monitored and penalized
- Jobs must complete within reasonable time limits or they may be terminated
- Inappropriate resource usage can lead to account restrictions
- Always include resource limits and requests to prevent resource hogging
- Be aware of namespace quotas and fair usage policies

Please provide:
1. Direct answer to the user's question
2. Step-by-step instructions where applicable
3. Practical kubectl commands they can run
4. Best practices and considerations
5. CRITICAL WARNINGS AND CAUTIONS relevant to the question
6. Common troubleshooting tips

Be specific, actionable, focused on NRP/K8s context, and ALWAYS emphasize safety and policy compliance.
"""

        response = chat_model.invoke(explanation_prompt)
        base_response = response.content.strip()

        # Enhance response with contextual information
        enhanced_response = _enhance_with_context(base_response, user_input)

        return enhanced_response, True

    except Exception as e:
        return f"Error generating explanation: {str(e)}", False


def _enhance_with_context(base_response: str, user_input: str) -> str:
    """Enhance base response with contextual examples, policies, and YAML templates."""
    components = [base_response]

    # Add relevant policies
    nautilus_policies = _get_relevant_nautilus_policies(user_input)
    if nautilus_policies:
        components.append(nautilus_policies)

    # Add contextual example
    contextual_example = _generate_contextual_example(user_input)
    if contextual_example:
        components.append(contextual_example)

    # Add relevant YAML examples
    yaml_examples_section = _get_relevant_yaml_examples(user_input)
    if yaml_examples_section:
        components.append(yaml_examples_section)

    return "\n\n".join(components)


def _get_relevant_yaml_examples(user_input: str) -> str:
    """Get relevant YAML examples based on user input."""
    try:
        input_lower = user_input.lower()

        # Determine relevant parameters
        resource_type, category, use_case = _extract_yaml_parameters(input_lower)

        # Get relevant examples
        examples = get_yaml_examples(category=category, resource_type=resource_type)

        # Filter by use case if specified
        if use_case and examples:
            filtered_examples = [e for e in examples if use_case in e.tags]
            if filtered_examples:
                examples = filtered_examples

        if examples:
            # Show most relevant example
            example = examples[0]
            return f"""## 📋 RELEVANT YAML EXAMPLE

**{example.title}**
{example.description}

Complexity: {example.complexity.title()} | Category: {example.category.title()}
Tags: {', '.join(example.tags)}

```yaml
{example.yaml_content}
```

Source: {example.source_url}

💡 Use this template with: `create yaml template name=your-name`"""

        return ""

    except Exception as e:
        print(f"[!] Error getting YAML examples: {e}")
        return ""


def _extract_yaml_parameters(input_lower: str) -> Tuple[str, str, str]:
    """Extract resource type, category, and use case from user input."""
    resource_type = None
    category = None
    use_case = None

    # Determine resource type
    if any(term in input_lower for term in ["pod", "container"]):
        resource_type = "pod"
    elif any(term in input_lower for term in ["deployment", "deploy"]):
        resource_type = "deployment"
    elif any(term in input_lower for term in ["job", "batch"]):
        resource_type = "job"
    elif any(term in input_lower for term in ["service", "networking"]):
        resource_type = "service"
    elif any(term in input_lower for term in ["storage", "volume", "pvc"]):
        category = "storage"

    # Determine use case
    if any(term in input_lower for term in ["gpu", "nvidia"]):
        use_case = "gpu"
    elif any(term in input_lower for term in ["storage", "persistent"]):
        use_case = "storage"
    elif any(term in input_lower for term in ["batch", "job"]):
        use_case = "batch"

    return resource_type, category, use_case


def _get_relevant_nautilus_policies(user_input: str) -> str:
    """Get relevant Nautilus policies and warnings for user input."""
    try:
        input_lower = user_input.lower()

        # Map topics to queries
        topic_queries = _identify_policy_topics(input_lower)

        # Collect all relevant policies
        all_policies = []
        for topic in topic_queries:
            policies = get_policies_for_topic(topic)
            all_policies.extend(policies)

        # Remove duplicates
        unique_policies = _deduplicate_policies(all_policies)

        if unique_policies:
            formatted = format_policy_warning(unique_policies)
            return f"## [!] OFFICIAL NAUTILUS POLICIES [!]\n\n{formatted}"

        return ""

    except Exception as e:
        print(f"[!] Error getting Nautilus policies: {e}")
        return ""


def _identify_policy_topics(input_lower: str) -> List[str]:
    """Identify which policy topics are relevant to the user input."""
    topic_queries = []

    topic_mapping = {
        ("sleep", "wait", "pause"): "sleep",
        ("batch", "job"): "batch job",
        ("gpu", "resource"): "resource",
        ("time", "limit", "deadline"): "time limit",
        ("storage", "volume", "pvc"): "storage",
        ("network", "networking"): "networking",
        ("security", "rbac", "permission"): "security"
    }

    for terms, topic in topic_mapping.items():
        if any(term in input_lower for term in terms):
            topic_queries.append(topic)

    return topic_queries


def _deduplicate_policies(policies: List) -> List:
    """Remove duplicate policies based on topic."""
    seen_topics = set()
    unique_policies = []

    for policy in policies:
        if hasattr(policy, 'topic') and policy.topic not in seen_topics:
            unique_policies.append(policy)
            seen_topics.add(policy.topic)

    return unique_policies


def _generate_contextual_example(user_input: str) -> str:
    """Generate a contextual example based on the user's specific input."""
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
        return ""


def get_explanation_capabilities() -> List[str]:
    """Get list of explanation capabilities."""
    return [
        "NRP/Kubernetes best practices and guidance",
        "Step-by-step tutorials and how-to guides",
        "Official Nautilus policies and warnings",
        "Resource management and allocation",
        "GPU usage and configuration",
        "Storage and networking setup",
        "Security and RBAC guidance",
        "Troubleshooting common issues",
        "YAML template recommendations"
    ]