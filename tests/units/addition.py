from mcmas.ispl import ISPL, Agent, Environment

from pytest import fail


def test_add():
    """adding agents to spec embeds those agents in the spec"""
    spec = (
        ISPL()
        + Agent(name="alice", actions="holdem foldem".split())
        + Agent(name="bob")
        + Environment()
    )
    assert "alice" in spec.agents
    assert "bob" in spec.agents


def test_iadd():
    """incremental addition also works as expected"""
    spec = ISPL()
    spec += Agent(name="alice")
    spec += Agent(name="bob")
    spec += Environment()
    assert "alice" in spec.agents
    assert "bob" in spec.agents


def test_agent_addition_undefined():
    try:
        Agent(name="alice") + Agent(name="bob")
    except (TypeError,) as exc:
        pass
    else:
        fail("agent addition is undefined")
