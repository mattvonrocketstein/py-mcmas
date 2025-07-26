""" """

from mcmas import examples, ispl, models, parser, util  # noqa

LOGGER = util.get_logger(__name__)
txt = open("tests/data/muddy_children.ispl").read()


def test_pythonic_environment():
    env = ispl.Environment(
        vars=dict(card1="a q k".split(), card2="a q k".split()),
        actions="none".split(),
        protocol=dict(Other="none"),
        evolution=["card1=card2 and card2=card1 if player1.Action = swap;"],
    )
    assert "card1" in env.vars
    assert "card2" in env.vars
    assert "Other" in env.protocol
    assert not env.advice


def test_pythonic_agent():
    agent = ispl.Agent(
        name="player1",
        lobsvars="card1".split(),
        actions="keep swap none".split(),
        protocol=["(play=false): {keep,swap};", "(play=true): {none};"],
        evolution=["play=true if play=false;"],
    )
    player1 = agent
    # player1 = agents["player1"]
    # assert 'card1' in env.vars
    # assert 'card2' in env.vars
    assert not player1.advice
    assert player1.concrete
    assert player1.actions == "keep swap none".split()


def test_spec_algebra():
    """ """
    player1 = ispl.Agent(
        name="player1",
        lobsvars="card1".split(),
        actions="keep swap none".split(),
        protocol=["(play=false): {keep,swap};", "(play=true): {none};"],
        evolution=["play=true if play=false;"],
    )
    player2 = player1.model_copy(update=dict(name="player2"))
    model = ispl.ISPL() + player1 + player2
    assert "player1" in model.agents
    assert "player2" in model.agents
