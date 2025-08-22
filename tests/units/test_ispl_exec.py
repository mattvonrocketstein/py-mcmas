"""
testing ISPL models and ispl.exec
"""

from mcmas import examples, ispl, util

LOGGER = util.get_logger(__name__)


complete_spec = examples.complete_spec
complete_model = ispl.ISPL(**complete_spec)


def test_run_partial_model():
    partial_model = ispl.ISPL(agents={}).exec()
    model = partial_model
    assert not model.validates
    assert model.simulation.failed, "partial model wont validate"
    # assert not model.sim.model.validates
    model = complete_model
    model = model.exec()
    assert model.source_code, "source code is finalized after exec"
    assert not model.simulation.failed, "simulation is finalized after exec"
    assert not model.simulation.error, "no error with complete spec"

    sans_agents = partial_spec = {
        k: v for k, v in complete_spec.items() if k != "init_states"
    }
    assert set(complete_spec.keys()) != set(partial_spec.keys()), "nothing removed"
    model = ispl.ISPL(**partial_spec)
    # assert model.validates
    sim = model.exec().simulation
    assert sim
    assert sim.error
    assert not sim.metadata.validates
    assert not sim.metadata.parsed
