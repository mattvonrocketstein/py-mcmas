"""
Declare pydantic agents as usual, then convert to ISPL spec.
"""

import mcmas

import pydantic_ai

LOGGER = mcmas.util.get_logger(__name__)

alice = pydantic_ai.Agent(
    name="alice",
)
bob = pydantic_ai.Agent(name="bob")


# declare agent tools as usual
@alice.tool
def tool1(*args, **kwargs) -> str:
    LOGGER.debug(f"{[args,kwargs]}")
    return f"tool1"


@bob.tool
def tool2(*args, **kwargs) -> str:
    LOGGER.debug(f"{[args,kwargs]}")
    return f"tool2"


def test_agent_from_pydantic():
    alice_prime = mcmas.ispl.Agent.from_pydantic_agent(alice)
    assert isinstance(alice_prime, (mcmas.ispl.Agent,))
    assert alice_prime.metadata.parser.endswith("Agent.from_pydantic_agent")


def test_agent_complete():
    bob_prime = mcmas.ispl.Agent.from_pydantic_agent(bob).model_complete()
    assert bob_prime.protocol
    assert not bob_prime.advice
    assert bob_prime.concrete
    assert "Agent bob" in bob_prime.model_dump_source()
    tmp = mcmas.ispl.Agent.from_source(bob_prime.model_dump_source())
    assert "Other" in str(tmp.protocol)
