from mcmas.ispl import ISPL, Agent, Environment


def test_ellipsis():
    """
    ellipsis notation returns 'trivial' objects,
    which are the concrete minimum that validates *and* runs.
    """
    spec = ISPL(...)
    assert spec.environment.concrete
    assert spec.agents
    default_agent = list(spec.agents.values())[0]
    assert default_agent.valid, "default agent in default spec should validate!"
    assert spec.valid
    assert spec.exec(strict=True)


def test_env_ellipsis():
    env = Environment(...)
    assert env.concrete, "environment returned from ellipsis should validate!"


def test_agent_ellipsis():
    agent = Agent(...)
    assert agent.valid, "agent returned from ellipsis should validate!"


def test_ellipsis_overrides():
    spec = ISPL(...)(agents=dict(p1=Agent(...)))
    assert "p1" in spec.agents
