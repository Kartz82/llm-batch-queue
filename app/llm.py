"""LLM backend with retry. 'echo' runs offline (no key); 'gemini' calls the API."""
from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings


def _gemini(prompt: str) -> str:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=0.2,
        max_retries=0,  # retry policy owned below
    )
    content = llm.invoke(prompt).content
    # Newer Gemini models return a list of typed blocks; flatten to plain text.
    if isinstance(content, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        ).strip()
    return content


@retry(
    stop=stop_after_attempt(max(1, settings.max_retries)),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def generate(prompt: str) -> str:
    """Generate a completion for a single prompt, retrying transient failures."""
    if settings.llm_backend == "gemini":
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY not set for gemini backend.")
        return _gemini(prompt)
    return f"[echo] {prompt.strip()[:280]}"
