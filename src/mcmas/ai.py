"""
mcmas.ai.

Generic AI-powered "completion" support for pydantic models.  Using this
module requires mcmas[ai] optional dependencies, e.g. pydantic-ai and
openai.

NB: Lots of this is manually doing what `pydantic_ai.Agent(..,
output_type=..)` is supposed to do, but it works better!  Upstream
implementation seems to be using tools (?) instead of native
"completion" capabilities.  This one works by passing in json-schema
details for pydantic models, and might expand to include details like
pydantic.Field descriptions, model-docstrings, etc.
"""

import inspect
import json
import os
import typing

import pydantic
from pydantic import ValidationError

import mcmas
from mcmas import rendering, util

LOGGER = mcmas.util.get_logger(__name__)
DEFAULT_MODEL = "granite3-dense:2b"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", f"{OLLAMA_URL}/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")
LLM_MODEL_NAME = os.environ.get(
    "LLM_MODEL_NAME", os.environ.get("MODEL", DEFAULT_MODEL)
)

try:
    import ollama as ollama_mod
except (ImportError,) as exc:
    ollama_mod = None
    LOGGER.critical(str(exc))
    LOGGER.warning("some features may not be available!")
    LOGGER.warning("cannot import ollama module, consider installing 'mcmas[ai]'")

try:
    import openai

    DEFAULT_CLIENT = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
except (ImportError,) as exc:
    openai = DEFAULT_CLIENT = None
    LOGGER.critical(str(exc))
    LOGGER.warning("some features may not be available!")
    LOGGER.warning("cannot import openai module, consider installing 'mcmas[ai]'")


def _loop(
    client: typing.Any = None,
    fxn: typing.Callable = None,
    model: str = DEFAULT_MODEL,
    query: str = None,
    schema: typing.Type = None,
    max_retries: int = 3,
    temperature: float = 0.1,
    system_prompt: str = "You are a precise JSON generator that follows schemas exactly.",
    user_prompt: str = None,
):
    """
    Inner loop for openai completion.
    """
    client = client or DEFAULT_CLIENT
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            parsed_json = json.loads(content)
            return parsed_json
        except json.JSONDecodeError as e:
            LOGGER.critical(f"Attempt {attempt + 1}: JSON decode error - {e}")
            if attempt == max_retries - 1:
                raise ValueError(
                    f"Failed to generate valid JSON after {max_retries} attempts"
                )
        except ValidationError as e:
            LOGGER.critical(f"Attempt {attempt + 1}: Schema validation error - {e}")
            if attempt == max_retries - 1:
                raise ValueError(
                    f"Failed to generate schema-compliant response after {max_retries} attempts"
                )
        except Exception as e:
            LOGGER.critical(f"Attempt {attempt + 1}: Unexpected error - {e}")
            if attempt == max_retries - 1:
                raise


@pydantic.validate_call
def agent_completion(
    fxn: typing.Callable = None,
    query: str = None,
    **kwargs,
) -> typing.Any:
    """
    See module doc-string.
    """

    from mcmas import ispl

    schema = ispl.Agent
    prompt_t = rendering.get_template("prompts/agent-generator.md")
    src = inspect.getsource(fxn)
    src = src[src.find("def ") :]  # .split('\n'); src=src
    query = prompt_t.render(
        user_query=src,
        json_schema=json.dumps(schema.model_json_schema(), indent=2),
    )
    agent = model_completion(schema=schema, **kwargs)
    LOGGER.critical(f"{agent}")
    trivial = ispl.Agent.trivial_agent()
    assert not trivial.advice
    templ = trivial.model_dump()
    for k in list(
        set(list(trivial.model_dump().keys()) + list(agent.model_dump().keys()))
    ):
        discovered = getattr(agent, k, None)
        if discovered:
            templ[k] = discovered
            # update()
            # tmp = getattr(agent, k, None)
        # templ[k] = getattr(agent, k, tmp or templ[k])
    templ["actions"] = list(set(agent.actions + trivial.actions))
    agent = ispl.Agent(**templ)
    LOGGER.critical(f"after merged with trivial {agent}")
    # parsed_json = _loop(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
    if agent.advice:
        LOGGER.critical(
            f"\n\nexpecting a completed agent in {agent}\n\nbut found advice {agent.advice}"
        )
        agent.protocol = trivial.protocol
        agent.evolution = trivial.evolution
    # import IPython; IPython.embed(confirm_exit=False)
    return agent


@pydantic.validate_call
def call_completion(
    fxn: typing.Callable = None,
    query: str = None,
    schema: typing.Type = None,
    system_prompt: str = "You are a precise JSON generator that follows schemas exactly.",
    **kwargs,
) -> typing.Any:
    """
    See module doc-string.
    """
    prompt_t = rendering.get_template("prompts/function-call-generator.md")
    user_prompt = prompt_t.render(
        user_query=query,
        function_sig=util.fxn_metadata(fxn),
    )
    parsed_json = _loop(system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
    return parsed_json


@pydantic.validate_call
def model_completion(
    query: str = None,
    schema: typing.Type = None,
    model: str = DEFAULT_MODEL,
    system_prompt: str = "You are a precise JSON generator that follows schemas exactly.",
    **kwargs,
) -> typing.Any:
    """
    See module doc-string.
    """
    prompt_t = rendering.get_template("prompts/json-response-generator.md")
    user_prompt = prompt_t.render(
        user_query=query,
        json_schema=json.dumps(schema.model_json_schema(), indent=2),
    )
    parsed_json = _loop(
        model=model, system_prompt=system_prompt, user_prompt=user_prompt, **kwargs
    )
    metadata = parsed_json.get("metadata", {})
    metadata.update(
        {
            "file": "<<prompt>>",
            "parser": f"mcmas.ai.model_completion[model={model}]",
        }
    )
    parsed_json.update(metadata=metadata)
    validated_data = schema(**parsed_json)
    return validated_data


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
        # LOGGER.warning("❌ Failed to connect to Ollama. Make sure it's running.")
        # LOGGER.info("✅ Connected to Ollama successfully!")
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

        # for model in models["models"]:
        # LOGGER.debug(f"   * {model.model}")
        if model_name not in models["models"]:
            LOGGER.debug(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            LOGGER.debug(f"Successfully pulled: {model_name}")
        else:
            LOGGER.debug(f"Model {model_name} is available.")


ollama = OllamaWrapper()
ollama_pull_model = ollama.pull_model


class Society:
    """
    Agent-discovery for a few different ecosystems / frameworks.
    Supported frameworks are { pydantic_ai | openai | camelai }.

    Instantiate a Society with the framework module, or a string
    version of the module name.  This auto-detects all agents that
    are defined / instantiated for this runtime.

    These class-properties are also available as shortcuts:
        * `Society.pydantic`
        * `Society.openai`
    """

    def __getitem__(self, other):
        tmp = [x for x in self]
        if isinstance(other, (str,)):
            agent = None
            for agent in tmp:
                if gettattr(agent, "name", None) == tmp:
                    break
        if other in tmp:
            agent = other

        raise Exception(agent._function_toolset.tools)
        return agent_completion(agent=agent, framework=self.module)

    def get_spec(self, agent):
        """
        
        """
        return self[agent]

    def __init__(self, module):
        """
        
        """
        name = getattr(module, "__name__", module)
        assert name in ["pydantic_ai", "openai", "agents"]
        self._module = module
        self._society = []
        if name == "pydantic_ai":
            try:
                import pydantic_ai
            except ImportError as exc:
                LOGGER.critical(
                    "`pydantic_ai` module not available.  "
                    f"pip install py-mcmas[ai] or openai-agents {exc}"
                )
            else:
                self._society = util.find_instances(pydantic_ai.Agent)
        elif name in ["openai", "agents"]:
            try:
                from agents import Agent
            except ImportError:
                LOGGER.critical(
                    "`agents` module not available.  "
                    "pip install py-mcmas[ai] or openai-agents"
                )
            else:
                self._society = util.find_instances(Agent)

        else:
            raise Exception(f"niy {[type(module), module]}")

    def __iter__(self):
        return iter(self._society)

    @util.classproperty
    def pydantic(kls) -> typing.List:
        """
        Finds all the pydantic agents.
        """
        return kls("pydantic_ai")

    @util.classproperty
    def openai(kls) -> typing.List:
        """
        Finds all the openai agents.
        """
        return kls("openai")

    # @classmethod
    # def index(kls):
    #     """"""
    #     out = {"pydantic": kls.pydantic, "openai": kls.openai}
    #     for name, members in out.items():
    #         LOGGER.warning(f"Found {len(members)} {name} agents in current runtime")
    #         for agentic in members:
    #             LOGGER.warning(f"  {agentic.__class__.__name__}: {agentic.name}")
    #     return out
