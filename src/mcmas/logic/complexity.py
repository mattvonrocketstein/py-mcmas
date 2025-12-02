"""
mcmas.logic.complexity.

A collection of (very unsophisticated!) heuristics for extracting
metadata from logical expressions, including details about their
time/space complexity.  Consider this is a placeholder for
something smarter ;)  Weights in particular are suggested by AI,
and NOT based on close reading of all the literature on
theoretical analysis.
"""

import math
import re

from mcmas import typing
from mcmas.models.spec import *  # noqa

# Basic propositional logic
PROPOSITIONAL = 0.1

# Temporal operators (CTL/LTL)
TEMPORAL_BASIC = 0.3  # X, F, G
TEMPORAL_UNTIL = 0.4  # U (more complex)

# Path quantifiers
PATH_QUANTIFIER = 0.2  # A, E

# Epistemic operators
KNOWLEDGE_SINGLE = 0.5  # K(i, φ) - PSPACE
KNOWLEDGE_GROUP = 0.6  # GK(G, φ)
KNOWLEDGE_DISTRIBUTED = 0.7  # DK(G, φ)
COMMON_KNOWLEDGE = 0.9  # GCK(G, φ) - EXPSPACE, approaching undecidable

# Strategic operators (ATL)
STRATEGIC_BASIC = 0.6  # <group>X, <group>F, <group>G
STRATEGIC_COMPLEX = 0.8  # Complex coalition strategies

# Deontic logic
OBLIGATION = 0.2  # O(φ)

# Nesting penalty (exponential growth)
NESTING_BASE = 1.3
MAX_REASONABLE_DEPTH = 10


# Regex patterns for different operator types
PATTERNS = {
    # Temporal operators
    "temporal_basic": r"[XFG]\s*\(",
    "temporal_until": r"U\s*\(",
    # Path quantifiers
    "path_quantifier": r"[AE]\s*\(",
    # CTL combinations
    "ctl_always_global": r"AG\s*\(",
    "ctl_eventually_possible": r"EF\s*\(",
    "ctl_always_next": r"AX\s*\(",
    "ctl_always_eventually": r"AF\s*\(",
    "ctl_possibly_always": r"EG\s*\(",
    # Epistemic operators
    "knowledge_single": r"K\s*\(\s*\w+\s*,",
    "knowledge_group": r"GK\s*\(\s*\{[^}]+\}\s*,",
    "knowledge_distributed": r"DK\s*\(\s*\{[^}]+\}\s*,",
    "common_knowledge": r"GCK\s*\(.*\)",
    # Strategic operators (ATL)
    "strategic": r"<[^>]+>[XFG]\s*\(",
    # Deontic operators
    "obligation": r"O\s*\(",
    # Propositional
    "propositional": r"[a-z]\w*(?!\s*\()",
}


class ExpressionAnalyzer:

    def extract_agents_and_groups(self, expression: str) -> typing.Tuple[int, int, int]:
        """
        Extract number of agents, groups, and coalition size.
        """
        agents = set()
        groups = []
        max_coalition_size = 0

        # Find individual agents in K(agent, ...)
        agent_matches = re.findall(r"K\s*\(\s*(\w+)\s*,", expression)
        agents.update(agent_matches)

        # Find groups in GK({...}), DK({...}), GCK({...})
        group_matches = re.findall(r"[GD]?[CK]+\s*\(\s*\{([^}]+)\}", expression)
        for group_str in group_matches:
            group_agents = [a.strip() for a in group_str.split(",")]
            groups.append(group_agents)
            agents.update(group_agents)
            max_coalition_size = max(max_coalition_size, len(group_agents))

        # Find strategic coalitions <...>
        coalition_matches = re.findall(r"<([^>]+)>", expression)
        for coalition_str in coalition_matches:
            coalition_agents = [a.strip() for a in coalition_str.split(",")]
            agents.update(coalition_agents)
            max_coalition_size = max(max_coalition_size, len(coalition_agents))

        return len(agents), len(groups), max_coalition_size

    def calculate_nesting_coefficient(self, expression: str) -> int:
        """Calculate maximum nesting depth of operators
        Simplified approach: count maximum parentheses nesting
        """
        max_depth = 0
        current_depth = 0

        for char in expression:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1

        return max_depth

    def count_operator_occurrences(self, expression: str) -> OperatorStatistics:
        """
        Count occurrences of each operator type.
        """
        op_stats = OperatorStatistics()
        for op_type, pattern in PATTERNS.items():
            matches = re.findall(pattern, expression, re.IGNORECASE)
            setattr(op_stats, op_type, len(matches))
        return op_stats

    def calculate_base_complexity(
        self, op_stats: typing.Dict[str, int], num_agents: int, max_coalition: int
    ) -> float:
        """
        Calculate base complexity score from operator counts.
        """
        score = 0.0

        # Temporal operators
        score += op_stats.temporal_basic * TEMPORAL_BASIC
        score += op_stats.temporal_until * TEMPORAL_UNTIL

        # Path quantifiers
        score += op_stats.path_quantifier * PATH_QUANTIFIER

        # CTL combinations (higher weight than individual components)
        ctl_ops = [
            "ctl_always_global",
            "ctl_eventually_possible",
            "ctl_always_next",
            "ctl_always_eventually",
            "ctl_possibly_always",
        ]
        for op in ctl_ops:
            score += getattr(op_stats, op) * (TEMPORAL_BASIC + PATH_QUANTIFIER)

        # Epistemic operators (scaled by number of agents)
        agent_factor = 1 + math.log2(max(1, num_agents))
        score += op_stats.knowledge_single * KNOWLEDGE_SINGLE * agent_factor
        score += op_stats.knowledge_group * KNOWLEDGE_GROUP * agent_factor
        score += op_stats.knowledge_distributed * KNOWLEDGE_DISTRIBUTED * agent_factor

        # Common knowledge (exponential in agent count, capped near 1.0)
        ck_count = op_stats.common_knowledge
        if ck_count > 0:
            ck_complexity = COMMON_KNOWLEDGE * (1 + num_agents * 0.05)
            score += ck_count * min(ck_complexity, 0.95)

        # Strategic operators (exponential in coalition size)
        strategic_count = op_stats.strategic
        if strategic_count > 0:
            coalition_factor = 1 + math.log2(max(1, max_coalition))
            strategic_complexity = STRATEGIC_BASIC * coalition_factor
            score += strategic_count * min(strategic_complexity, 0.85)

        # Deontic operators
        score += op_stats.obligation * OBLIGATION

        # Propositional variables (minimal complexity)
        score += op_stats.propositional * PROPOSITIONAL

        return score

    def apply_nesting_penalty(self, base_score: float, depth: int) -> float:
        """
        Apply exponential penalty for nesting depth.
        """
        if depth <= 1:
            return base_score

        # Exponential growth with depth, but bounded
        depth_factor = min(
            math.pow(NESTING_BASE, depth - 1), 10.0  # Cap the multiplier
        )

        return base_score * depth_factor

    @staticmethod
    def normalize_score(raw_score: float) -> float:
        """
        Normalize score to [0, 1] range using sigmoid-like
        function.
        """
        # Use a sigmoid function to map [0, ∞) to [0, 1)
        # The function approaches 1 as scores get very high
        return 1 - math.exp(-raw_score)

    def analyze(self, expression: str, index: int = -1):
        """
        Main function to analyze logical expression complexity.

        Args:
            expression: String containing logical formula

        Returns:
            Tuple of (complexity_score, analysis_details)
            - complexity_score: Float between 0 and 1
            - analysis_details: Dict with breakdown of analysis
        """
        if not expression or not expression.strip():
            return 0.0, {"error": "Empty expression"}

        # Clean and normalize expression
        expression = expression.strip()

        # Extract structural information
        num_agents, num_groups, max_coalition = self.extract_agents_and_groups(
            expression
        )
        nesting_coefficient = self.calculate_nesting_coefficient(expression)
        opstats = self.count_operator_occurrences(expression)

        # Calculate base complexity
        base_complexity = self.calculate_base_complexity(
            opstats, num_agents, max_coalition
        )

        # Apply nesting penalty
        raw_score = self.apply_nesting_penalty(base_complexity, nesting_coefficient)

        # Normalize to [0, 1]
        final_score = self.normalize_score(raw_score)

        # Prepare analysis details
        from mcmas import fmtk
        from mcmas.models import spec  # logic import complexity

        return spec.ComplexityAnalysis(
            score=final_score,
            formula=expression,
            metadata=fmtk.AnalysisMeta(
                formula_index=index,
                base_complexity=base_complexity,
                nesting_coefficient=nesting_coefficient,
                raw_score=raw_score,
            ).model_dump(exclude_unset=True),
            statistics=ComplexityStats(
                coalitions=CoalitionStats(
                    max_coalition_size=max_coalition,
                    num_agents=num_agents,
                    num_groups=num_groups,
                ).model_dump(),
                operators=opstats.model_dump(),
            ).model_dump(),
        )

    __call__ = analyze


analyzer = ExpressionAnalyzer()
