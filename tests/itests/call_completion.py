""" """

import typing

import mcmas
from mcmas import ai

import pytest

LOGGER = mcmas.util.get_logger(__name__)


def foo(a: str = "a", b: str = "b", c: str = "c", **kwargs) -> typing.Dict:
    return a + b + c


def test_call_completion():
    recc = ai.call_completion(
        fxn=foo,
        query="use 1 for a, two for b.",
    )
    assert recc.get("a", None) in ["1"], "failed to pickup value for first kwarg"
    assert recc.get("b", None) in [
        "two",
        "2",
    ], "failed to pickup value for 2nd kwarg"
    try:
        tmp = foo(**recc)
    except:
        pytest.fail("could not call function with args from call-completion")
    else:
        assert tmp in ["12c", "1twoc"]


if __name__ == "__main__":
    test_call_completion()
