"""
mcmas.examples.
"""

# don't conflict with Environment-as-symbol
from mcmas.ispl import ISPL
from mcmas.ispl import Environment as _Environment
from mcmas.logic import Environment

agents = dict(
    Child1=dict(
        lobsvars=["child2", "child3"],
        vars=dict(othersayknow="boolean"),
        actions=["donotknow", "know"],
        protocol={
            Environment.mem < Environment.child2 + Environment.child3: "{donotknow};",
            Environment.mem >= Environment.child2 + Environment.child3: "{know};",
        },
        evolution=[
            "othersayknow=true if Environment.Action=ask and Environment.mem<Environment.child2+Environment.child3 and othersayknow=false and (Child2.Action=know or Child3.Action=know);"
        ],
    ),
    Child2=dict(
        lobsvars=["child1", "child3"],
        vars=dict(othersayknow="boolean"),
        actions=["donotknow", "know"],
        protocol={
            Environment.mem < Environment.child1 + Environment.child3: "{donotknow}",
            Environment.mem >= Environment.child1 + Environment.child3: "{know}",
        },
        evolution=[
            "othersayknow=true if Environment.Action=ask and Environment.mem<Environment.child1+Environment.child3 and othersayknow=false and (Child1.Action=know or Child3.Action=know)"
        ],
    ),
    Child3=dict(
        lobsvars=["child1", "child2"],
        vars=dict(othersayknow="boolean"),
        actions=["donotknow", "know"],
        protocol={
            Environment.mem < Environment.child1 + Environment.child2: "{donotknow}",
            Environment.mem >= Environment.child1 + Environment.child2: "{know}",
        },
        evolution=[
            "othersayknow=true if Environment.Action=ask and Environment.mem<Environment.child1+Environment.child2 and othersayknow=false and (Child1.Action=know or Child2.Action=know)"
        ],
    ),
)
environment = dict(
    actions=["exists", "ask"],
    evolution=[
        "initial=false and sayexist=true and mem = mem + 1 if initial=true and Action=exists;",
        "initial=false and mem = mem + 1 if initial=true and Action=ask;",
        "mem = mem + 1 if initial=false and mem < 2;",
    ],
    protocol={
        "initial=true and (child1=1 or child2=1 or child3=1)": "{exists}",
        "Other": "{ask}",
    },
    vars=dict(
        initial="boolean",
        child1="0..1",
        child2="0..1",
        child3="0..1",
    ),
    obsvars=dict(sayexist="boolean", mem="-1..2"),
)
evaluation = [
    "muddy1 if Environment.child1=1;",
    "muddy2 if Environment.child2=1;",
    "muddy3 if Environment.child3=1;",
    "saysknows1 if Environment.child2+Environment.child3<=Environment.mem;",
    "saysknows2 if Environment.child1+Environment.child3<=Environment.mem;",
    "saysknows3 if Environment.child1+Environment.child2<=Environment.mem;",
]
formulae = [
    "AG((saysknows1 -> (K(Child1, muddy1) or K(Child1, !muddy1))) and ((K(Child1, muddy1) or K(Child1, !muddy1)) -> saysknows1));",
    "AG((saysknows2 -> (K(Child2, muddy2) or K(Child2, !muddy2))) and ((K(Child2, muddy2) or K(Child2, !muddy2)) -> saysknows2));",
    "AG((saysknows3 -> (K(Child3, muddy3) or K(Child3, !muddy3))) and ((K(Child3, muddy3) or K(Child3, !muddy3)) -> saysknows3));",
]

init_states = [
    "Child1.othersayknow=false and Child2.othersayknow=false and Child3.othersayknow=false and Environment.sayexist=false and Environment.initial=true and Environment.mem=-1;"
]


model_dict = dict(environment=environment, agents=agents)

incomplete_spec = model = ISPL(
    title="The protocol for the 3 muddy children",
    environment=environment,
    agents=agents,
    formulae=formulae,
    evaluation=evaluation,
    init_states=init_states,
)

complete_spec = dict(
    init_states=init_states,
    environment=_Environment(
        **environment,
    ),
    formulae=formulae,
    agents=agents,
    evaluation=evaluation,
)

card_game_ispl = """
-- Simple card game example from Jamroga et al
-- rule: a > k, k > q, q > a

Agent Environment
  Vars:
    card1: {a, q, k};
    card2: {a, q, k};
  end Vars
  Actions = { none };
  Protocol:
    Other: {none};
  end Protocol
  Evolution:
    card1=card2 and card2=card1 if player1.Action = swap;
  end Evolution
end Agent

-- agent 1
Agent player1
  Lobsvars={card1};
  Vars:
    play: boolean;
  end Vars
  Actions = {keep,swap,none};
  Protocol:
    (play=false): {keep,swap};
    (play=true): {none};
  end Protocol
  Evolution:
    play=true if play=false;
  end Evolution
end Agent
-- agent 2
Agent player2
    Lobsvars={card2};
    Vars:
        play: boolean;
    end Vars
    Actions = {none};
    Protocol:
        Other: {none};
    end Protocol
    Evolution:
        play=true if play=false;
end Evolution
end Agent

Evaluation
  p1win if (  ( Environment.card1=a and Environment.card2=k)  or ( ( Environment.card1=k and Environment.card2=q) )  or ( ( Environment.card1=q and Environment.card2=a) ) );
end Evaluation

InitStates
  (player1.play=false) and (player2.play=false) and ( ( Environment.card1=a and Environment.card2=k ) or ( Environment.card1=a and Environment.card2=q ) or ( Environment.card1=q and Environment.card2=k ) or ( Environment.card1=q and Environment.card2=a ) or ( Environment.card1=k and Environment.card2=a ) or ( Environment.card1=k and Environment.card2=q ));
end InitStates

Groups
  g1 = {player1};
end Groups

Formulae
  AF(p1win) or ! AF(p1win);
  <g1>X(p1win);
end Formulae"""
