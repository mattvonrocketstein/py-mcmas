""" """

from mcmas import examples, models, util
from mcmas.ispl import ISPL

# from mcmas.logic import Environment, false, symbols, true
LOGGER = util.get_logger(__name__)


def test_import_symbols():
    model = ISPL.from_source(examples.card_game_ispl)
    meta = model.model_dump_analysis()
    symbols = meta.symbols
    assert isinstance(meta, (models.spec.Analysis,))
    assert isinstance(symbols, (models.spec.SymbolMetadata,))
    assert symbols.actions
    assert symbols.agents
    assert symbols.vars
    assert "player1" in list(map(str, symbols.agents))
    assert "Environment" in list(map(str, symbols.agents))
