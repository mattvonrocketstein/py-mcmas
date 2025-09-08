from mcmas import ispl, util

LOGGER = util.get_logger(__name__)

from mcmas.logic import symbols


def test_flexible_actions_parsing():
    from mcmas.ispl import symbols

    expected = "keep swap none".split()
    actual = ispl.Agent(
        actions="{keep, swap, none};",
    ).actions
    assert actual == expected
    actual = ispl.Agent(
        actions=["keep", "swap", "none"],
    ).actions
    assert actual == expected
    actual = ispl.Agent(actions=[symbols.keep, symbols.swap, symbols.none]).actions
    assert actual == expected


def test_agent_from_python():
    player1 = ispl.Agent(
        lobsvars=[symbols.card1],
        vars=dict(play=symbols.boolean),
        actions="keep swap none".split(),
        protocol=["(play=false): {keep,swap};", "(play=true): {none};"],
        evolution=["play=true if play=false;"],
    )
    assert isinstance(player1.protocol, (dict,))
    assert "(play=false)" in player1.protocol
    assert "(play=true)" in player1.protocol
