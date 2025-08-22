""" """

import os

import mcmas

import pydantic_ai

LOGGER = mcmas.util.get_logger(__name__)

# Dummy keys for Ollama
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://fake:11434/v1"

# os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
# model = OpenAIModel("driaforall/tiny-agent-a:0.5b")
agent_defaults = dict(
    retries=1,
    output_retries=1,
    # model=model,
    # output_type=mcmas.ispl.Agent,
    system_prompt="You are a helpful AI assistant.",
)
mcmas.ctx.patch_pydantic()

alice = pydantic_ai.Agent(name="alice", **agent_defaults)
bob = pydantic_ai.Agent(name="bob", **agent_defaults)

from agents import Agent

charlie = Agent(name="chuck")

# @alice.tool
# def tool1(*args, **kwargs) -> str:
#     LOGGER.debug(f"{[args,kwargs]}")
#     return f"tool1"


# @bob.tool
# def tool2(*args, **kwargs) -> str:
#     LOGGER.debug(f"{[args,kwargs]}")
#     return f"tool2"


# @agent.tool
# async def analyze_profile(
#     ctx: RunContext[mcmas.ispl.Agent], profile_data: dict
# ) -> str:
#     LOGGER.debug(f"{ctx}")
#     profile = mcmas.ispl.Agent(**profile_data)
#     return str(profile)


# def test_pull_model():
#         pull_model()


def test_pydantic_agents():
    assert alice in mcmas.ai.Society.pydantic, "failed to detect agent"
    assert bob in mcmas.ai.Society.pydantic, "failed to detect agent"


def test_openai_agents():
    assert charlie in mcmas.ai.Society.openai, "failed to detect openai agent"


def test_tags():
    b = mcmas.ctx.agent_builder
    b.add_tag(charlie, vars=dict(card1="a q k".split()))
    assert "vars" in b[charlie]


# assert tool2==[]
# raise Exception(bob.tool)


# def test_bonk():
#     user_profile = mcmas.ispl.Agent(
#         vars=dict(one="1", two="2"), actions="a1 a2".split()
#     )
#     result = agent.run_sync(
#         "this is definition of an automaton in the ISPL language.  what vars does the agent know about? \n\n"
#         + user_profile.model_dump_json(),
#         # deps=user_profile,
#     )
#     print(result.output)
#     # print(agent.run_sync('Alice is playing a card game where she knows one face value at a time.  She can use actions fold or call'))
