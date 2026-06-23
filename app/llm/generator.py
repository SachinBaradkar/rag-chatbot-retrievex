"""
LLM client — Groq free-tier inference by default (llama3-8b-8192).
Falls back to HuggingFace Inference API if configured.
Both are free; neither charges per token at the relevant usage levels.

Why Groq?
  • Completely free tier (no credit card required)
  • Fast inference (LPU hardware)
  • Llama 3 quality output
  • REST API — works on any hosting platform (no local GPU needed)
  • Single env-var switch to change model or provider
"""

from __future__ import annotations
import logging
from typing import List, Dict, Iterator

from app.config.settings import LLM_PROVIDER, LLM_MODEL_NAME, GROQ_API_KEY, HF_API_TOKEN

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a precise and helpful AI assistant that answers questions \
strictly based on the provided document context.

Rules:
1. Answer ONLY from the provided context. Do not use external knowledge.
2. If the context does not contain enough information, say:
   "I could not find information related to this query in the uploaded documents."
3. Always be concise and factual.
4. Cite sources naturally (e.g., "According to Employee_Handbook.pdf, page 5...").
5. For follow-up questions, use conversation history to maintain context.
6. Never fabricate information."""


# ── Groq client ───────────────────────────────────────────────────────────────

def _groq_chat(messages: List[Dict], model: str) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


# ── HuggingFace fallback ──────────────────────────────────────────────────────

def _hf_chat(messages: List[Dict], model: str) -> str:
    import requests
    prompt = "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}"
        for m in messages
        if m["role"] != "system"
    )
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.1},
    }
    url = f"https://api-inference.huggingface.co/models/{model}"
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    result = r.json()
    if isinstance(result, list):
        return result[0].get("generated_text", "").replace(prompt, "").strip()
    return str(result)


# ── Public interface ──────────────────────────────────────────────────────────

def generate_answer(
    query: str,
    context: str,
    chat_history: List[Dict[str, str]],
) -> str:
    """
    Generate an answer grounded in `context`.

    chat_history: list of {"role": "user"|"assistant", "content": str}
    """
    user_message = f"""Context from uploaded documents:
{context}

---
Question: {query}

Answer based only on the context above:"""

    messages: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include last 6 turns (3 exchanges) for conversational memory
    for turn in chat_history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        if LLM_PROVIDER == "groq" and GROQ_API_KEY:
            return _groq_chat(messages, LLM_MODEL_NAME)
        elif HF_API_TOKEN:
            hf_model = LLM_MODEL_NAME if LLM_PROVIDER == "huggingface" else "mistralai/Mixtral-8x7B-Instruct-v0.1"
            return _hf_chat(messages, hf_model)
        else:
            return (
                "⚠️ No LLM API key configured. "
                "Please set GROQ_API_KEY in your .env file. "
                "Get a free key at https://console.groq.com"
            )
    except Exception as e:
        logger.error("LLM error: %s", e)
        return f"⚠️ LLM error: {e}"


def no_context_response() -> str:
    return "I could not find information related to this query in the uploaded documents."
