"""
mcmas.models.spec.
"""

import pydantic
from pydantic import Field

from mcmas import fmtk, typing, util

LOGGER = util.get_logger(__name__)  # noqa


class SymbolMetadata(pydantic.BaseModel):
    """
    Result of running ISPL Analysis.

    This extracts details about symbols, namespaces, etc.
    """

    actions: typing.SymbolList2 = Field(
        default=[],
        description="Actions list",
    )
    agents: typing.SymbolList2 = Field(
        default=[],
        description="Agents list",
    )
    vars: typing.SymbolList2 = Field(
        default=[],
        description="Var list",
    )


# Details about logical operators that are used in specification's formulae.
# Coarse detail about operators can be used to derive information about time/space complexity.

FormulaAnalysisDetails = typing.Dict[str, typing.Any]
ComplexityScore = float
FormulaAnalysis = FormulaAnalysisDetails
# FormulaAnalysis = typing.Tuple[ComplexityScore, FormulaAnalysisDetails]

ComplexityAnalysis = typing.Dict[str, typing.Any]


class OpStats(pydantic.BaseModel):
    """
    
    """

    temporal_basic: int = Field(default=0)
    temporal_until: int = Field(default=0)
    path_quantifier: int = Field(default=0)
    ctl_always_global: int = Field(default=0)
    ctl_eventually_possible: int = Field(default=0)
    ctl_always_next: int = Field(default=0)
    ctl_always_eventually: int = Field(default=0)
    ctl_possibly_always: int = Field(default=0)
    knowledge_single: int = Field(default=0)
    knowledge_group: int = Field(default=0)
    knowledge_distributed: int = Field(default=0)
    common_knowledge: int = Field(default=0)
    strategic: int = Field(default=0)
    obligation: int = Field(default=0)
    propositional: int = Field(default=0)

    def model_dump(self, *args, **kwargs):
        tmp = super().model_dump(*args, **kwargs)
        out = {k: v for k, v in tmp.items() if v not in [0, "0", 0.0]}
        return out


class AnalysisMeta(pydantic.BaseModel):
    """
    
    """

    formula_index: int = Field(default=-1)
    base_complexity: float = Field(default=0.0)
    nesting_coefficient: int = Field(default=1)
    raw_score: float = Field(default=0.0)


class CoalitionStats(pydantic.BaseModel):
    """
    
    """

    max_coalition_size: int = Field(default=0)
    num_agents: int = Field(default=0)
    num_groups: int = Field(default=0)

    def model_dump(self, *args, **kwargs):
        tmp = super().model_dump(*args, **kwargs)
        out = {k: v for k, v in tmp.items() if v not in [0, "0", 0.0]}
        return out


class ComplexityStats(pydantic.BaseModel):
    """
    
    """

    coalitions: CoalitionStats = Field(default=CoalitionStats())
    operators: OpStats = Field(default=OpStats().model_dump())

    def model_dump(self, *args, **kwargs):
        return dict(
            coalitions=self.coalitions.model_dump(*args, **kwargs),
            operators=self.operators.model_dump(*args, **kwargs),
        )


class ComplexityAnalysis(pydantic.BaseModel):
    """
    
    """

    score: float = Field(default=0.0)
    formula: str = Field(default="")
    metadata: AnalysisMeta = Field(default=AnalysisMeta())
    statistics: ComplexityStats = Field(default=ComplexityStats())

    def model_dump(self, *args, **kwargs):
        return dict(
            score=self.score,
            formula=self.formula,
            metadata=self.metadata.model_dump(*args, **kwargs),
            statistics=self.statistics.model_dump(*args, **kwargs),
        )


class Analysis(fmtk.SpecificationAnalysis):
    """
    Result of analyzing the given specification.

    This breaks down details about ISPL symbols and logical
    operators that are used
    """

    symbols: SymbolMetadata = Field(
        description="Symbols (includes vars+actions)",
        default=SymbolMetadata(),
    )
    complexity: typing.List[ComplexityAnalysis] = Field(
        default={},
        description="Details about time/space complexity for logical operators",
    )
    types: typing.List[str] = Field(
        default=[],
        description="Types that are used",
    )
