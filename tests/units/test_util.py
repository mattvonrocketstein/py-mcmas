import typing

import mcmas


class Parent:
    pass


class Subclass(Parent):
    pass


def test_find_instances():
    p = Parent()
    s = Subclass()
    actual = mcmas.util.find_instances(Parent)
    expected = [p, s]
    assert set(actual) == set(expected)


def foo(a, b, c="d", **kwargs) -> typing.Dict:
    return a + b + c


def test_fxn_sig():
    tmp = mcmas.util.fxn_sig(foo)
    assert tmp.startswith("def foo"), "function name is missing"
    assert 'c="d"' in tmp, "function args missing"
    assert "-> Dict" in tmp, "return annotation detail is missing"
