import typing
from typing import Any, List

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


def foo(a, b, c="d", **kwargs) -> typing.Dict:  # noqa
    return a + b + c


def test_fxn_sig():  # noqa
    tmp = mcmas.util.fxn_sig(foo)
    assert tmp.startswith("def foo"), "function name is missing"
    assert 'c="d"' in tmp, "function args missing"
    assert "-> Dict" in tmp, "return annotation detail is missing"


def func1(a: int, b: str, c: float = 3.14) -> bool:  # noqa
    return bool([a, b, c])


def func2(x, y: str, z: int = 10):  # noqa
    # Test function 2: Mixed annotations
    return [x, y, z]


def func3(arg1, arg2="default"):  # noqa
    # Test function 3: No annotations
    return [arg1, arg2]


def func4(
    items: typing.List[str],
    mapping: typing.Dict[str, int],
    optional: typing.Optional[bool] = None,
):  # noqa
    # Test function 4: Complex types
    return [items, mapping, optional]


def test_fxn_sig_dict():
    tmp = mcmas.util.fxn_sig.as_dict(func1)
    assert tmp["a"] == int
    assert tmp["b"] == str
    assert tmp["c"] == float
    tmp = mcmas.util.fxn_sig.as_dict(func2)
    assert "x" in tmp
    assert "y" in tmp
    assert "z" in tmp
    tmp = mcmas.util.fxn_sig.as_dict(func3)
    assert "arg1" in tmp
    assert tmp["arg1"] == Any
    assert "arg2" in tmp
    tmp = mcmas.util.fxn_sig.as_dict(func4)
    assert tmp["items"] == List[str]
    assert len(tmp) == 3
