""" """

from pathlib import Path

from mcmas import engine, examples
from mcmas.util.lme import get_logger

LOGGER = get_logger(__name__)

data_dir = Path(__file__).parent.parent / "data"


def test_dict2ispl():
    from mcmas.util import dict2ispl

    tmp = dict2ispl(examples.model_dict)
    assert isinstance(tmp, (str,))
    assert "-- Untitled Model" in tmp
    assert "Agent Environment" in tmp


def test_run_after_transform():
    tmp = engine(fname=data_dir / "muddy_children.json.ispl")
    assert isinstance(tmp, (dict,))
    assert not tmp["error"]
    assert tmp["text"]
    assert tmp["metadata"]["exit_code"] == 0
    assert tmp["metadata"]["validates"]
    # assert "model" in tmp
    # assert tmp["model"]["validates"]
