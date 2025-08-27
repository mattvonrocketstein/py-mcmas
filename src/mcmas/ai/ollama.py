"""
mcmas.ai.ollama:

Some small utilities for working with ollama.
"""

import ollama as ollama_mod

from mcmas import util

from .config import LLM_MODEL_NAME, OLLAMA_URL  # noqa

LOGGER = util.get_logger(__name__)

# try:
# except (ImportError,) as exc:
#     ollama_mod = None
#     LOGGER.critical(str(exc))
#     LOGGER.warning("some features may not be available!")
#     LOGGER.warning("cannot import ollama module, consider installing 'mcmas[ai]'")


class OllamaWrapper:
    """
    A wrapper for using the ollama module.
    """

    @util.classproperty_cached
    def client(self):
        """
        Returns a (cached) ollama client.

        This respects ${OLLAMA_URL} from environment
        """
        return ollama_mod.Client(host=OLLAMA_URL)

    def list(self):
        """
        List available models.
        """
        return self.client.list()

    def pull_model(self, model_name: str = "") -> None:
        """
        Pull the given model, or ${LLM_MODEL_NAME} or ${MODEL},
        whichever is found first.
        """
        model_name = model_name or LLM_MODEL_NAME
        LOGGER.debug("Checking connection..")
        models = self.list()
        LOGGER.debug("Connection ok.")
        LOGGER.debug(f"Found {len(models['models'])} models:")

        if model_name not in models["models"]:
            LOGGER.debug(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            LOGGER.debug(f"Successfully pulled: {model_name}")
        else:
            LOGGER.debug(f"Model {model_name} is available.")


ollama = OllamaWrapper()
ollama_pull_model = ollama.pull_model
