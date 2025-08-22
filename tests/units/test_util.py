import mcmas


class Parent:
    pass


class Subclass(Parent):
    pass


def test_find_instances():
    p = Parent()
    s = Subclass()
    actual = mcmas.util.find_instances(Parent)
    expected = [p, s]
    assert set(actual) == set(expected)


def foo(a, b, c="d", **kwargs):
    return a + b + c


def test_signature_to_dict():
    assert mcmas.util.fxn_metadata(foo).strip().startswith("def foo")
