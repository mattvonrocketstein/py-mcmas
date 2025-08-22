""" """

from mcmas import examples, ispl, models, parser, util  # noqa

LOGGER = util.get_logger(__name__)
txt = open("tests/data/muddy_children.ispl").read()


def test_environment_from_source():
    env = ispl.Environment.from_source(
        """
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
end Agent"""
    )
    assert "card1" in env.vars
    assert "card2" in env.vars
    assert "Other" in env.protocol
    assert not env.advice


def test_agent_from_source():
    agent = ispl.Agent.from_source(
        """
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
end Agent"""
    )
    player1 = agent
    # player1 = agents["player1"]
    # assert 'card1' in env.vars
    # assert 'card2' in env.vars
    assert not player1.advice
    assert player1.concrete
    assert player1.actions == "keep swap none".split()


def test_parser():
    agents = parser.extract_agents(txt)
    # raise Exception(agents)
    assert "Environment" in agents
    environment = agents.pop("Environment")
    environment = ispl.Environment(**environment)
    assert environment.advice == []
    assert environment.concrete
    assert "Child1" in agents
    agents = {a: ispl.Agent(**agents[a]) for a in agents}
    for agent in agents:
        assert agents[agent].actions
        # no missing sections
        assert agents[agent].advice == []
        assert agents[agent].concrete

    # LOGGER.critical(json.dumps(agents,indent=2))
    child1 = agents["Child1"]
    assert child1
    assert child1.actions == ["donotknow", "know"]
    assert child1.advice == []


def test_empty_model_isnt_concrete():
    assert not ispl.Agent().concrete
    # child1 = models.strict.Agent(**child1_data)
    # assert child1.actions
    # try:
    # except:
    #             raise Exception(child1.actions)
    # else:
    #     assert False, 'not finished decoding yet, needs actions'
    # ispl = ISPL(agents=agents,environment=environment)
    # assert ispl
