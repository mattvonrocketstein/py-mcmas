"""
mcmas.models.spec.
"""

import pydantic
from pydantic import Field

from mcmas import fmtk, typing, util

LOGGER = util.get_logger(__name__)


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

FormulaAnalysisDetails=typing.Dict[str, typing.Any]
ComplexityScore=float
FormulaAnalysis = FormulaAnalysisDetails
# FormulaAnalysis = typing.Tuple[ComplexityScore, FormulaAnalysisDetails]
ComplexityAnalysis = typing.Dict[str,FormulaAnalysis]

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
    complexity: ComplexityAnalysis = Field(
        default=[],
        description="Details about time/space complexity for logical operators",
    )
    types: typing.List[str] = Field(
        default=[],
        description="Types that are used",
    )