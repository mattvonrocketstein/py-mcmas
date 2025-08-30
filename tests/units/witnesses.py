from mcmas import engine
from mcmas.sim import Simulation


def test_witnesses():
    sim = engine(
        fname="tests/data/book_store.ispl", output_format="model", witness=True
    )
    assert isinstance(sim, (Simulation,))
    assert len(sim.witnesses) == 5
    assert len(sim.counter_examples) == 2
    isinstance(sim.witnesses, (dict,)), "witnesses should be dictionary"
    formula = "AF (K(Supplier, contract_success))"
    assert formula in sim.witnesses, "witnesses should be keyed on formula"
    formula = "EF supplier_violation"
    assert isinstance(
        sim.witnesses[formula], (list,)
    ), "witness value should be a list of states"
    assert isinstance(
        sim.witnesses[formula][0], (dict,)
    ), "witness value should be a list of states"
    expected = [
        {
            "Purchaser.state": "p0",
            "Supplier.state": "s0",
        },
        {
            "Purchaser.state": "p1",
            "Supplier.state": "s1",
        },
        {
            "Purchaser.state": "p1",
            "Supplier.state": "s14",
        },
    ]
    assert sim.witnesses[formula] == expected, "witness does not match expected output"


def test_witnesses_on_demand():
    sim = engine(fname="tests/data/book_store.ispl", output_format="model")
    assert isinstance(sim, (Simulation,))
    assert not sim.witnesses, "witnesses not present if not requested"
