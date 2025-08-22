# -- An absolutely minimal ISPL program still requires a do-nothing agent.
# -- This example is just enough boilerplate to use the logic-engine for simple stuff.
# from mcmas.ispl import ISPL, Environment, Agent
# from mcmas.logic import symbols

__spec__ = ISPL(
    environment=Environment(
        vars=dict(p=symbols.boolean, q=symbols.boolean),
        actions=[symbols.tick],
        protocol=dict(Other=[symbols.tick]),
    ),
    agents={
        "NOOP": Agent(
            vars={"ticking": symbols.boolean},
            actions=[symbols.tick],
            protocol=["Other : {tick}"],
            # evolution=["ticking=true if Action=tick;"],
            evolution=[
                logic.If(
                    logic.Eq(symbols.ticking, symbols.true),
                    logic.Eq(symbols.Action, symbols.tick),
                )
            ],
        )
    },
    evaluation=[
        logic.If(symbols.p, logic.Eq(symbols.Environment.p, symbols.true)),
        logic.If(symbols.q, logic.Eq(symbols.Environment.q, symbols.true)),
    ],
    init_states=[
        # 'Environment.p=true and Environment.q=false;',],
        logic.And(
            logic.Eq(symbols.Environment.p, symbols.true),
            logic.Eq(symbols.Environment.q, symbols.false),
        )
    ],
    formulae=["p; !q; p -> !q;"],
)
