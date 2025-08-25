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


def test_parse_witness():
    """Test the original example from the requirements."""
    test_input = """-- State 0 --
  Agent Environment
  Agent Supplier
    state=s3
    zonk=bop
  Agent Purchaser
    state=p1
    foo=bar"""

    actual = parser.extract_witnesses(test_input)
    expected = [
        {
            "Supplier.state": "s3",
            "Supplier.zonk": "bop",
            "Purchaser.state": "p1",
            "Purchaser.foo": "bar",
        }
    ]

    assert actual == expected


def test_empty_agent_sections():
    """Test that empty agent sections are properly ignored."""
    test_input = """-- State 5 --
  Agent Database
    state=connected
    host=localhost
  Agent EmptyAgent
  Agent Logger
    level=debug"""
    actual = parser.extract_witnesses(test_input)
    expected = [
        {
            "Database.state": "connected",
            "Database.host": "localhost",
            "Logger.level": "debug",
        }
    ]
    assert actual == expected


def test_multiple_properties_per_agent():
    """Test agents with multiple properties."""
    test_input = """-- State 0 --
  Agent Cache
    state=active
    size=1000
    timeout=300"""
    actual = parser.extract_witnesses(test_input)
    expected = [{"Cache.state": "active", "Cache.size": "1000", "Cache.timeout": "300"}]
    assert actual == expected


def test_no_agents():
    """Test input with no agent sections."""
    test_input = """-- State 0 --
    not=agent
    stuff=here"""
    actual = parser.extract_witnesses(test_input)
    expected = []
    assert actual == expected


def test_empty_input():
    """Test empty input."""
    actual = parser.extract_witnesses("")
    assert actual == []


def test_whitespace_variations():
    """Test various whitespace patterns."""
    test_input = """-- State 0 --
  Agent   SpacedName
        key1=value1
    key2=value2
	key3=value3"""  # noqa

    actual = parser.extract_witnesses(test_input)
    expected = [
        {
            "SpacedName.key1": "value1",
            "SpacedName.key2": "value2",
            "SpacedName.key3": "value3",
        }
    ]

    assert actual == expected


def test_multiple_states():
    txt = """
-- State 0 --
  Agent Environment
  Agent Supplier
    state=s0
  Agent Purchaser
    state=p0

-- State 1 --
  Agent Environment
  Agent Supplier
    state=s1
  Agent Purchaser
    state=p1

-- State 2 --
  Agent Environment
  Agent Supplier
    state=s3
  Agent Purchaser
    state=p1

-- State 3 --
  Agent Environment
  Agent Supplier
    state=s0
  Agent Purchaser
    state=p0

-- State 4 --
  Agent Environment
  Agent Supplier
    state=s1
  Agent Purchaser
    state=p1

-- State 5 --
  Agent Environment
  Agent Supplier
    state=s3
  Agent Purchaser
    state=p1

"""
    actual = parser.extract_witnesses(txt)
    assert len(actual) == 6
    assert isinstance(actual, (list,))
    assert isinstance(actual[0], (dict,))
    assert len(actual[0]) == 2
    assert len(actual[-1]) == 2
