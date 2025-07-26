"""

"""

import os

import pytest


@pytest.fixture(scope="session")
def global_env(
    defaults=dict(  # Dummy keys for Ollama
        OPENAI_API_KEY="ollama", OPENAI_BASE_URL="http://fake:11434/v1"
    ),
):
    """
    Save original env so we can restore later give tests access
    to it if needed Restore original environment after tests.
    """
    original_env = os.environ.copy()
    os.environ.update(**defaults)
    yield os.environ
    os.environ.clear()
    os.environ.update(original_env)
