"""
A more idiomatic/abbreviated version of `minimal.py`
Run this using `ispl --sim tests/data/minimal2.py`
See the docs https://mattvonrocketstein.github.io/py-mcmas/demos/pythonic-ispl
"""

from mcmas import ISPL, And, Environment, false, symbols, true
from mcmas.logic import types

__spec__ = ISPL(...)(
    title="Minimal valid ISPL definition in Python",
    environment=Environment(...)(vars={var: types.bool for var in "pq"}),
    evaluation=[
        symbols.p >> symbols.Environment.p @ true,
        symbols.q >> symbols.Environment.q @ true,
    ],
    init_states=[
        And(
            symbols.Environment.p @ true,
            symbols.Environment.q @ false,
        )
    ],
    formulae=["p", "!q", "p -> !q"],
)
