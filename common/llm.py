"""Shared LLM setup used by every exercise.

Configuration comes from environment variables (see .env.example):

    ANTHROPIC_BASE_URL   base URL of an Anthropic-compatible API
    ANTHROPIC_API_KEY    API token (ANTHROPIC_AUTH_TOKEN also accepted)
    LLM_MODEL            model name (default: GLM-5.3-Flash)
"""

import os

from langchain.chat_models import init_chat_model

DEFAULT_MODEL = "GLM-5.3-Flash"
DEFAULT_BASE_URL = "https://api.z.ai/api/anthropic"


def get_model(temperature: float = 0):
    """Return a chat model created with ``init_chat_model`` (course requirement).

    Every exercise uses the same factory so the endpoint/model can be
    switched from one place (the .env file) without touching exercise code.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        raise RuntimeError(
            "Missing API key: set ANTHROPIC_API_KEY in your environment or .env file"
        )
    return init_chat_model(
        os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        model_provider="anthropic",
        base_url=os.environ.get("ANTHROPIC_BASE_URL", DEFAULT_BASE_URL),
        api_key=api_key,
        temperature=temperature,
        max_tokens=4096,
        # The proxy's default model is a reasoning model and emits thinking
        # blocks; disabling keeps structured output fast and predictable.
        thinking={"type": "disabled"},
    )
