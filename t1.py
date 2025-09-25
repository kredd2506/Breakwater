import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Use specific credentials for this test
api_key = "60giG4L3xNAMC1FT2f2ivYnExpHYA1fD"
base_url = "https://ellm.nrp-nautilus.io/v1"
model = "deepseek-r1"

print(f"Using API key: {api_key[:10]}...")
print(f"Using base URL: {base_url}")
print(f"Using model: {model}")

try:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Talk like a pirate. Now count from 1 to 43."
            }
        ],
    )

    print("Success!")
    content = completion.choices[0].message.content
    # Handle encoding issues on Windows
    try:
        print(content)
    except UnicodeEncodeError:
        # Replace problematic characters with safe alternatives
        safe_content = content.encode('ascii', errors='replace').decode('ascii')
        print(safe_content)

except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")