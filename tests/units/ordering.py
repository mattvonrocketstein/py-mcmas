from mcmas import ISPL, Agent

import pytest

simple_expr = "p"
nested_expr = "GCK(<g1>, K(a1, AF(p)))"
very_nested_expr = "AG(EF(GCK(<g1>, K(a1, p))))"


def test_abs():
    value = abs(ISPL(formulae=[simple_expr]))
    assert isinstance(value, float)


def test_spec_ranking():
    x = ISPL(formulae=[simple_expr])
    y = ISPL(formulae=[nested_expr])
    z = ISPL(formulae=[very_nested_expr])
    assert x < y < z
    assert z > y > x
    assert sorted([x, z, y]) == [x, y, z]


def test_agent_ranking():
    a1 = Agent(vars={var: bool for var in "xyz"})
    a2 = Agent(vars={var: bool for var in "abcd"})
    assert a2 > a1


def test_incomparable():
    agent = Agent(...)
    spec = ISPL(...)
    with pytest.raises(TypeError):
        agent < spec
