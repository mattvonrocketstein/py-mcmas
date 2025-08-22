import mcmas
from mcmas import engine, models, util

LOGGER = util.lme.get_logger(__name__)


def test_run_filename_return_dict():
    out: dict = mcmas.engine(fname="tests/data/muddy_children.ispl")
    assert isinstance(out, (dict,)), "returns dictionary by default"
    assert "metadata" in out, "dictionary-output includes key for `model`"
    assert "facts" in out, "dictionary-output includes key for `facts`"
    assert out["metadata"]["parsed"], "parsed? => legal ISPL"
    assert out["metadata"][
        "validates"
    ], "validates? => parsed and all formulae confirmed"


def test_run_filename_return_text():
    out: str = mcmas.engine(
        fname="tests/data/muddy_children.ispl", output_format="text"
    )
    assert isinstance(out, (str,))
    assert out.startswith("Command line: mcmas ")


def test_run_text_return_model():
    with open("tests/data/muddy_children.ispl") as fhandle:
        text = fhandle.read()
    out = mcmas.engine(text=text, output_format="model")
    assert isinstance(out, (models.Simulation,)), "requested a model? => Simulation"
    # assert not out.failed
    assert not out.error, "successful run => no error"
    assert out.text, "model encapsulates raw output"
    assert out.metadata, "model has metadata"


def test_run_bad_program_wont_validate():
    text = "ILLEGAL PROGRAM"
    out = mcmas.engine(text=text, output_format="model")
    assert isinstance(out, (models.Simulation,)), "requested a model? => Simulation"
    # assert not out.text
    # assert out.error
    assert not out.metadata.validates, "bad program => marked as not valid"
    assert not out.metadata.parsed, "bad program => marked as not parsed"
    assert not out.text, "bad program => `text` not set"
    assert out.error


def test_bad_filename():
    try:
        engine(fname="does/not/exist.ispl")
    except (SystemExit,) as exc:
        pass
    else:
        raise ValueError("non existant file should exit 1")


def test_run_partial():
    ispl = mcmas.ISPL(agents={})
    out = mcmas.engine(model=ispl, strict=False, output_format="model")
    assert not out.metadata.parsed  # == False
    assert not out.metadata.validates  # == False
