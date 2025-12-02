import os
import sys

from mcmas import ISPL, Agent, Environment

import pytest

# required for even importing the pydantic examples
os.environ["GROQ_API_KEY"] = "fake"


def test_agent_from_prompt():
    prompt = (
        "a person named alice is playing a game of cards."
        'actions are available at each turn, and alice may "hold" or "fold"'
    )
    agent = Agent[prompt]
    assert agent.name == "alice"
    assert agent.actions == ["hold", "fold"]


def test_environment_from_prompt():
    prompt = "Variables are foo, bar, and baz."
    env = Environment[prompt]
    assert sorted(list(env.vars.keys())) == "bar baz foo".split()


@pytest.mark.xfail(reason="smaller LLMs choke on bigger json-schemas! :/")
def test_spec_from_prompt():
    prompt = "The title of the specification is Bridge Game."
    spec = ISPL[prompt]
    assert spec.title == "Bridge Game"


def test_spec_from_implementation():
    from pydantic_ai_examples import roulette_wheel

    agent_implementation = roulette_wheel.roulette_agent
    agent_spec = Agent[agent_implementation]
    expected = "load_from_pydantic_ai_agent"
    actual = agent_spec.metadata.parser
    assert expected in actual
    assert "square" in agent_spec.vars
    actual = agent_spec.vars["square"]
    expected = f"0..{sys.maxsize}"
    assert actual == expected, "integer->bounded integer type conversion failed"
