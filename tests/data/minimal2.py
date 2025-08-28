# An absolutely minimal ISPL program in pure python.
# See the docs https://mattvonrocketstein.github.io/py-mcmas/demos/pythonic-ispl

__spec__ = ISPL.__class_getitem__(
    title="Minimal valid ISPL definition in Python",
    environment=Environment[dict(vars=dict(p=symbols.boolean, q=symbols.boolean))],
    # Equivalently: p if Environment.p=true; q if Environment.q=true
    evaluation=[
        If(symbols.p, Equal(symbols.Environment.p, true)),
        If(symbols.q, Equal(symbols.Environment.q, true)),
    ],
    # Equivalently: Environment.p=true and Environment.q=false
    init_states=[
        And(
            Equal(symbols.Environment.p, true),
            Equal(symbols.Environment.q, symbols.false),
        )
    ],
    formulae=["p; !q; p -> !q;"],
)
