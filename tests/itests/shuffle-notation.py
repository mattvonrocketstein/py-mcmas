from mcmas import ISPL, ai

# load existing agent from fixture
agent1 = ISPL.load_from_file("tests/data/muddy_children.ispl").agents["Child1"]


def test_mutation_notation():
    """mutation with operator syntax"""
    agent2 = agent1**0.1
    expected = agent1 != agent2
    msg = "expected agents should be different after mutation"
    assert expected, msg
    expected = agent1.model_dump() != agent2.model_dump()
    assert expected, msg
    msg = "expected both original and derivative agent should validate"
    expected = all([agent1.concrete, agent2.concrete])
    assert expected, msg


def test_model_mutation():
    """
    use model_mutation directly just for demonstration purposes.
    no assertions since this is exactly the same as above.
    """
    agent2 = ai.model_mutation(obj=agent1, model_settings=dict(top_p=0.1))
