import mcmas
from mcmas import Simulation, util

LOGGER = util.lme.get_logger(__name__)


def test_simulation_type():
    sim = Simulation()


def test_run_text_return_model():
    with open("tests/data/muddy_children.ispl") as fhandle:
        text = fhandle.read()
    out = mcmas.engine(text=text, output_format="model")
    assert isinstance(out, (Simulation,)), "requested a model? => Simulation"
    data = out.model_dump()
    for k in "deadlock exit_code parsed validates".split():
        assert k in data["metadata"].keys()
