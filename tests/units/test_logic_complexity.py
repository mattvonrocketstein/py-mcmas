from mcmas.logic.complexity import analyzer

simple_expr = analyzer("p")
nested_expr = analyzer("GCK({a1,a2,a3,a4}, K(a1, AF(p)))")
very_nested_expr = analyzer("AG(EF(GCK({a1,a2,a3}, K(a1, p))))")


def test_simple_prop():
    op_stats = simple_expr.statistics.operators
    assert op_stats.propositional == 1


def test_basic_conj():
    op_stats = analyzer("p & q").statistics.operators
    assert op_stats.propositional == 2


def test_always_global():
    op_stats = analyzer("AG(p)").statistics.operators
    assert op_stats.ctl_always_global


def test_eventually_possible():
    op_stats = analyzer("EF(p & q)").statistics.operators
    assert op_stats.ctl_eventually_possible


def test_agent_knowledge():
    op_stats = analyzer("K(agent1,p)").statistics.operators
    assert op_stats.knowledge_single


def test_common_knowledge():
    stats = analyzer("GCK({a1,a2})").statistics
    op_stats = stats.operators
    assert op_stats.common_knowledge


def test_coalitions():
    stats = analyzer("GCK({a1,a2})").statistics
    op_stats = stats.operators
    assert stats.coalitions.num_agents > 0


def test_nested():
    assert (
        simple_expr.metadata.nesting_coefficient
        < nested_expr.metadata.nesting_coefficient
        < very_nested_expr.metadata.nesting_coefficient
    )
    assert simple_expr.score < nested_expr.score < very_nested_expr.score


def test_strategic_eventually():
    op_stats = analyzer("<{a1,a2}>F(p)").statistics.operators
    assert op_stats.strategic


def test_obligation():
    op_stats = analyzer("O(p)").statistics.operators
    assert op_stats.obligation
