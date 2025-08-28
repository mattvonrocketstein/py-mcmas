# An absolutely minimal ISPL program in pure python.
# See the docs https://mattvonrocketstein.github.io/py-mcmas/demos/pythonic-ispl

__spec__ = ISPL(
    title='Minimal valid ISPL definition in Python',
    environment=Environment(
        vars=dict(p=symbols.boolean, q=symbols.boolean),
        actions=[symbols.tick],
        protocol=dict(Other=[symbols.tick]),
    ),
    
    agents = {
        "Player1": Agent(
            vars={"ticking": symbols.boolean},
            actions=[symbols.tick],
            protocol=["Other : {tick}"],
            evolution=[
                logic.If(
                    logic.Eq(symbols.ticking, symbols.true),
                    logic.Eq(symbols.Action, symbols.tick),
                )
            ],
        )
    },
    
    evaluation=[
        # Equivalently: p if Environment.p=true; q if Environment.q=true
        logic.If(symbols.p, logic.Eq(symbols.Environment.p, symbols.true)),
        logic.If(symbols.q, logic.Eq(symbols.Environment.q, symbols.true)),
    ],
    
    init_states=[
        # Equivalently: Environment.p=true and Environment.q=false
        logic.And(
            logic.Eq(symbols.Environment.p, symbols.true),
            logic.Eq(symbols.Environment.q, symbols.false),
        )
    ],
    formulae =  ["p; !q; p -> !q;"],
)