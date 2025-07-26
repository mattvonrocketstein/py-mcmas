from mcmas import examples
from mcmas.ispl import ISPL, Agent, Environment


def test_add():
    spec = ISPL() + Agent(name="alice") + Agent(name="bob") + Environment()
    assert "alice" in spec.agents
    assert "bob" in spec.agents


def test_iadd():
    spec = ISPL()
    spec += Agent(name="alice")
    spec += Agent(name="bob")
    spec += Environment()
    assert "alice" in spec.agents
    assert "bob" in spec.agents


def test_invert():
    spec = ISPL(**examples.complete_spec)
    assert not spec.advice
    assert ~spec == spec
