from mcmas import ISPL, Agent, Environment

import pytest


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


@pytest.mark.xfail(reason="smaller LLMs choke on bigger json-schemas")
def test_spec_from_prompt():
    prompt = "The title of the specification is Bridge Game."
    spec = ISPL[prompt]
    assert spec.title == "Bridge Game"
    # assert spec.agents == [1]
    # agent.actions == ["hold", "fold"]
