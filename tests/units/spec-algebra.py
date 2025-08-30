from mcmas.ispl import ISPL, Agent, Environment


def test_eq():
    alice1 = Agent(name="alice")
    alice2 = Agent(name="alice")
    assert alice1 == alice2
    bob = Agent(name="bob")
    assert alice1 != bob


def test_trivial_spec():
    """
    ellipsis notation returns 'trivial' objects,
    which are the concrete minimum that validates *and* runs.
    """
    spec = ISPL(...)
    assert spec.environment.concrete
    assert spec.agents
    assert not list(spec.agents.values())[0].advice
    assert spec.concrete


def test_trivial_env():
    """
    ellipsis notation returns 'trivial' objects,
    which are the concrete minimum that validates *and* runs.
    """
    spec = Environment(...)
    assert spec.concrete


def test_trivial_agent():
    """
    ellipsis notation returns 'trivial' objects,
    which are the concrete minimum that validates *and* runs.
    """
    spec = Agent(...)
    assert spec.concrete


def test_invert():
    """
    the inversion operation means 'autocomplete from ai'.
    since trivial specs are the minimum complete spec,
    the autocomplete operation returns the same object
    """
    spec = ISPL(...)
    assert spec.concrete
    assert ~spec == spec


def test_ellipsis():
    spec = ISPL(...)(agents=dict(p1=Agent(...)))
