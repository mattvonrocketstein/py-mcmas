from mcmas import logic, util
from mcmas.ispl import ISPL
from mcmas.logic import Environment, false, symbols, true

LOGGER = util.get_logger(__name__)
ask = symbols.ask
othersayknow = symbols.othersayknow
know = symbols.know


def test_basic_symbols():
    # create a symbol just by naming it
    x, y = symbols.x, symbols.y
    assert str(x) == "x", "symbol evaluates to itself"
    assert str(y) == "y", "symbol evaluates to itself"
    z = symbols.z
    expr1 = logic.Equal(z, x + y)
    assert str(expr1) == "z=x+y", "addition and equality works"
    expr2 = z(x + y)
    assert str(expr2) == "z(x+y)", "symbols are callable"


def test_logical_if():
    label = 'working if-as-syntax ( i.e. ">>" )'
    actual = str(symbols.aaa >> symbols.bbb)
    expected = "aaa if bbb"
    assert actual == expected, label
    label = "working if-as-function, i.e. rshift"
    actual = str(logic.If(symbols.aaa, symbols.bbb))
    assert actual == expected, label


def test_logical_and():
    label = 'working and-as-syntax ( i.e. "&" )'
    expected = "aaa and bbb"
    actual = symbols.aaa & symbols.bbb
    assert actual == expected, label
    # ==str(logic.And(symbols.aaa, symbols.bbb))


def test_symbol_or():
    expected = "aaa or bbb"
    label = "working or-as-function"
    actual = str(logic.Or(symbols.aaa, symbols.bbb))
    assert actual == expected, label
    label = 'working or-as-syntax ( i.e. "|" )'
    actual = str(symbols.aaa | symbols.bbb)
    assert actual == expected, label


def test_fragment4():
    actual = symbols.muddy1 >> logic.Eq(Environment.child1, 1)
    expected = "muddy1 if Environment.child1=1"
    label = ""
    assert actual == expected, label
    ispl = ISPL(evaluation=[symbols.muddy1 + " if Environment.child1=1;"])
    label = "instantiated model with combined strings/symbols"
    assert ispl, label


def test_logic_fragment1():
    expected = "othersayknow=true"
    actual = str(logic.Eq(othersayknow, true))
    # assert frag1 == str(expr)
    label = "fragment1"
    assert actual == expected, label


def test_logic_fragment2():
    expected = "Environment.Action=ask and Environment.mem<Environment.child1+Environment.child3"
    actual = str(
        logic.And(
            logic.Eq(Environment.Action, ask),
            Environment.mem < Environment.child1 + Environment.child3,
        )
    )
    label = "fragment2"
    assert actual == expected, label
    # frag2 == str(expr2)


def test_logic_fragment3():
    frag3 = "othersayknow=true if Environment.Action=ask and Environment.mem<Environment.child1+Environment.child3 and othersayknow=false and (Child1.Action=know or Child3.Action=know)"
    expr = logic.If(
        logic.Eq(othersayknow, true),
        logic.And(
            logic.Eq(Environment.Action, ask),
            Environment.mem < Environment.child1 + Environment.child3,
            logic.Eq(othersayknow, false),
            logic.Grouping(
                logic.Or(
                    logic.Equal(symbols.Child1.Action, know),
                    logic.Equal(symbols.Child3.Action, know),
                )
            ),
        ),
    )
    assert frag3 == str(expr)
