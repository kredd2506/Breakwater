# nrp_init.py
import os
from langchain_openai import ChatOpenAI

try:
    from dotenv import load_dotenv, find_dotenv  # pip install python-dotenv
    # Find .env starting from CWD and walking up; works no matter where you run from
    _dotenv = find_dotenv(usecwd=True)
    if _dotenv:
        load_dotenv(_dotenv)
except Exception:
    # dotenv is optional; ignore if not installed
    pass

def _mask(s: str) -> str:
    return s if not s else (s[:4] + "…" + s[-4:])

_debug_printed = False

def init_chat_model(model: str | None = None, **kwargs):
    """
    Drop-in init that uses NRP_* env vars or OPENAI_* and auto-loads .env.
    """
    global _debug_printed

    # Read envs (NRP first, then OPENAI as fallback)
    nrp_api_key = os.environ.get("NRP_API_KEY") or os.environ.get("NRP") 
    base_url = os.environ.get("NRP_BASE_URL", "https://llm.nrp-nautilus.io/")
    model = model or os.environ.get("NRP_MODEL")

    # Normalize /v1
    if not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    # Map to OpenAI client expectations too (some libs read only these)
    if nrp_api_key:
        os.environ.setdefault("OPENAI_API_KEY", nrp_api_key)
        os.environ.setdefault("OPENAI_BASE_URL", base_url)

    if not nrp_api_key:
        raise RuntimeError(
            "NRP_API_KEY not found. Set it in your environment or in a .env file.\n"
            "Example .env line:\nNRP_API_KEY=your_real_key_here"
        )

    if not _debug_printed:
        print(f"[nrp_init] base_url={base_url}  api_key={_mask(nrp_api_key)}  model={model}")
        _debug_printed = True

    # For recent langchain_openai versions, use api_key/base_url
    return ChatOpenAI(
        model=model,
        api_key=nrp_api_key,
        base_url=base_url,
        **kwargs,
    )