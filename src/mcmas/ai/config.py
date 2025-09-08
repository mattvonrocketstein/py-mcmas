"""
mcmas.ai.config:

Defaults and environment overrides for AI related config
"""

import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

DEFAULT_MODEL_NAME = "granite3-dense:2b"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

LLM_MODEL_NAME = os.environ.get(
    "LLM_MODEL_NAME", os.environ.get("MODEL", DEFAULT_MODEL_NAME)
)

OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", f"{OLLAMA_URL}/v1")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")

DEFAULT_MODEL = OpenAIModel(
    model_name=LLM_MODEL_NAME,
    provider=OpenAIProvider(base_url=OPENAI_BASE_URL),
)

# def get_model(**kwargs):
#     """
#     """
#     name = kwargs.pop('model_name',LLM_MODEL_NAME)
#     base_url = kwargs.pop('base_url',OPENAI_BASE_URL)
#     return OpenAIModel(
#         model_name=name,
#         provider=OpenAIProvider(base_url=base_url),
#         **kwargs
#     )
