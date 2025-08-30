import mcmas
from mcmas import ISPL, Simulation


def test_empty_simulation():
    """empty simulations are allowed so they can be built incrementally"""
    sim = Simulation()


def test_run_text_return_model():
    with open("tests/data/muddy_children.ispl") as fhandle:
        text = fhandle.read()
    out = mcmas.engine(text=text, output_format="model")
    assert isinstance(out, (Simulation,)), "requested a model? => Simulation"
    data = out.model_dump()
    for k in ["deadlock", "exit_code", "parsed", "validates"]:
        assert k in data["metadata"]


def test_run_model_return_model():
    spec = ISPL.load_from_ispl_file("tests/data/muddy_children.ispl")
    out = mcmas.engine(model=spec, output_format="model")
    assert isinstance(out, (Simulation,)), "requested a model? => Simulation"


def test_run_model_return_json():
    spec = ISPL.load_from_ispl_file("tests/data/muddy_children.ispl")
    out = mcmas.engine(model=spec, output_format="json")
    assert isinstance(out, str), "JSON request should return a string"


def test_run_model_return_data():
    spec = ISPL.load_from_ispl_file("tests/data/muddy_children.ispl")
    out = mcmas.engine(model=spec, output_format="data")
    assert isinstance(out, dict), "data request should return dict"
