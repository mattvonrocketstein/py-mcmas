""" """

import mcmas
from mcmas import ai

import pydantic_ai

from mcmas.tests.fixtures import global_env  # noqa

LOGGER = mcmas.util.get_logger(__name__)

# declare pydantic agents as usual
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


def test_pydantic_society(global_env):  # noqa
    society = ai.Society(pydantic_ai)
    assert alice in society, "failed to detect agent"
    assert bob in society, "failed to detect agent"


def test_pydantic_agents_patched(global_env):  # noqa
    mcmas.ctx.patch_pydantic()
    assert type(alice.specification) == mcmas.ispl.Agent
    assert "tool1" in alice.specification.actions
    assert "tool2" in bob.specification.actions
    assert not bob.specification.concrete
    assert len(bob.specification.advice) > 0
