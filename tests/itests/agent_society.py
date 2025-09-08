import pydantic_ai

# Declare pydantic agents as usual
alice = pydantic_ai.Agent(name="alice")
bob = pydantic_ai.Agent(name="bob")


# Declare pydantic tools as usual
@alice.tool
def tool1(expected="", arguments="", **kwargs) -> str:
    return f"tool1 response {expected} {arguments}"


@bob.tool
def tool2(different="", arguments="", **kwargs) -> str:  # noqa
    return f"tool2 response {different} {arguments}"


# Create society from module
from mcmas import ai

society = ai.Society(pydantic_ai)


def test_society_membership():
    assert alice in society, "failed to detect agent"
    assert bob in society, "failed to detect agent"


def test_society_iterable():
    for agent in [alice, bob]:
        assert agent in society, "society should be populated and iterable"
