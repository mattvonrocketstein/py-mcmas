""" """

import mcmas
from mcmas import ai, util

LOGGER = mcmas.util.get_logger(__name__)


def foo(a, b, c="d", **kwargs):
    return a + b + c


def test_main():
    assert util.fxn_metadata(foo).strip().startswith("def foo")
    recc = ai.call_completion(
        fxn=foo,
        query="use 1 for a, two for b.",
    )
    assert recc.get("a", None) == 1, "failed to pickup value for first kwarg"
    assert recc.get("b", None) in [
        "two",
        2,
        "2",
    ], "failed to pickup value for 2nd kwarg"


if __name__ == "__main__":
    test_main()
