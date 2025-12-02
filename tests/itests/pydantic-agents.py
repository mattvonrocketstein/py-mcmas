import mcmas

import pydantic_ai

# Declare agents & tools as usual
alice = pydantic_ai.Agent(name="alice")
bob = pydantic_ai.Agent(name="bob")


@alice.tool
def tool1(*args, **kwargs) -> str:
    return f"tool1 {[args,kwargs]}"


@bob.tool
def tool2(ctx, first_kwarg: int = 1, **kwargs) -> str:
    return f"tool2 {[ctx, first_kwarg, kwargs]}"


def test_agent_from_pydantic():
    """
    Using square-brackets notation, construct
    an agent spec from an agent implementation
    """
    alice_prime = mcmas.ispl.Agent[alice]
    assert isinstance(alice_prime, (mcmas.Agent,))


def test_agent_complete():
    bob_prime = mcmas.Agent[bob]
    assert bob_prime.protocol, "default protocol should be set"
    assert not bob_prime.advice, "no advice, agent is concrete"
    assert bob_prime.concrete, "expected agent validates and is ready-to-run"
    expected = "Agent bob" in bob_prime.model_dump_source()
    err = "agent name extracted incorrectly"
    assert expected, err
    err = "agent-implementation's argument should be reflected in spec"
    expected = "first_kwarg" in bob_prime.vars
    assert expected, err
    tmp = mcmas.Agent.load_from_source(bob_prime.model_dump_source())
    assert "Other" in str(tmp.protocol)
