""" """

from mcmas import examples, util
from mcmas.ispl import ISPL

LOGGER = util.get_logger(__name__)


def test_run_partial_model():
    model = ISPL(agents={}).exec()
    sim = model.simulation
    assert sim.failed
    assert not sim.metadata.validates
    model = ISPL(**examples.complete_spec)
    model = model.exec()
    assert model.source_code, "source code is finalized after exec"
    sim = model.simulation
    assert sim, "simulation is finalized after exec"
    assert not sim.error, "no error with complete spec"

    sans_agents = partial_spec = {
        k: v for k, v in examples.complete_spec.items() if k != "init_states"
    }
    assert set(examples.complete_spec.keys()) != set(
        partial_spec.keys()
    ), "nothing removed"
    model = ISPL(**partial_spec)
    sim = model.exec().simulation
    assert sim
    assert sim.error
    assert not sim.metadata.validates  # == False
    assert not sim.metadata.parsed  # == False


def test_pydantic_model_to_json():
    model = ISPL(**examples.model_dict)
    data = model.model_dump_json()
    LOGGER.debug(data)
    assert data


def test_pydantic_model_to_ispl():
    model = ISPL(**examples.model_dict)
    data = model.model_dump_source()
    LOGGER.debug(data)
