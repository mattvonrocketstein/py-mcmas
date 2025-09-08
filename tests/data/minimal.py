"""
A 1:1 port of `minimal.ispl` to python.
Run this using `ispl --sim tests/data/minimal.py`
See the docs https://mattvonrocketstein.github.io/py-mcmas/demos/pythonic-ispl
"""

# Imports are implied with `ispl` CLI, but add them anyway
from mcmas import ISPL, Agent, And, Environment, Eq, If, symbols

__spec__ = ISPL(
    title="Minimal valid ISPL definition in Python",
    environment=Environment(
        vars=dict(p=symbols.boolean, q=symbols.boolean),
        actions=[symbols.tick],
        protocol=dict(Other=[symbols.tick]),
    ),
    agents={
        "Player1": Agent(
            vars={"ticking": symbols.boolean},
            actions=[symbols.tick],
            protocol=["Other : {tick}"],
            evolution=[
                If(
                    Eq(symbols.ticking, symbols.true),
                    Eq(symbols.Action, symbols.tick),
                )
            ],
        )
    },
    evaluation=[
        # Equivalently: p if Environment.p=true; q if Environment.q=true
        If(symbols.p, Eq(symbols.Environment.p, symbols.true)),
        If(symbols.q, Eq(symbols.Environment.q, symbols.true)),
    ],
    init_states=[
        # Equivalently: Environment.p=true and Environment.q=false
        And(
            Eq(symbols.Environment.p, symbols.true),
            Eq(symbols.Environment.q, symbols.false),
        )
    ],
    formulae=["p; !q; p -> !q;"],
)
