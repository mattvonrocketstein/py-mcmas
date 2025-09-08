""" """

from mcmas import Agent, ai

# download model if necessary
ai.init()


def test_model_completion():
    a1 = Agent()
    assert not a1.concrete, "original agent is empty and should not be valid"
