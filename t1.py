from openai import OpenAI

client = OpenAI(
    api_key="QmKTZlW0ck0XO1rvu7SpDiDs3bnOqKoM",
    base_url="https://ellm.nrp-nautilus.io/v1"  # keep /v1
)

completion = client.chat.completions.create(
    model="gemma3",  # ensure this matches /v1/models
    messages=[
        {
            "role": "user",
            "content": "Talk like a pirate. Now count from 1 to 43."
        }
    ],
)

print(completion.choices[0].message.content)


# # NRP K8s System Configuration
# # Copy this file to .env and fill in your values

# NRP_BASE_URL=https://llm.nrp-nautilus.io/

# # NRP API Configuration
# NRP_API_KEY=sk-gY3H4d_Xv4Qf2Ig-x5DjFw

# NRP_MODEL=glm-v


# nrp_key_2=sk-lCnKFKjil5JhwphaeYpVUQ
# nrp_model2=glm-v
# # Alternative: OpenAI Configuration (fallback)
# # OPENAI_API_KEY=your_openai_api_key_here
# # OPENAI_BASE_URL=https://api.openai.com/v1

# # Kubernetes Configuration
# # Uses your existing kubectl config by default

# # Optional: Search API Keys (for enhanced features)
# # SERPER_API_KEY=your_serper_api_key
# # BING_SEARCH_KEY=your_bing_search_key