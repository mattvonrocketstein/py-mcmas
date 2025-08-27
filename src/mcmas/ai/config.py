"""
mcmas.ai.config:

Defaults and environment overrides for AI related config
"""

import os

DEFAULT_MODEL = "granite3-dense:2b"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

LLM_MODEL_NAME = os.environ.get(
    "LLM_MODEL_NAME", os.environ.get("MODEL", DEFAULT_MODEL)
)

OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", f"{OLLAMA_URL}/v1")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")
