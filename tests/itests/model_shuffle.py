""" """

from mcmas import ai, ispl

# download model if necessary
ai.init()


def test_model_shuffle():
    a1 = ispl.ISPL.load_from_file("tests/data/muddy_children.ispl").agents["Child1"]
    assert not a1.advice, "original agent should be valid"
    assert isinstance(a1, (ispl.Agent,))
    a2 = ai.model_shuffle(obj=a1)
    assert a1 != a2, "agents are different after shuffle"
    assert not a2.advice, "derivative agent should still be valid"


if __name__ == "__main__":
    test_model_shuffle()
