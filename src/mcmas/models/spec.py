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


class OperatorMetadata(pydantic.BaseModel):
    """
    Details about logical operators that are used in
    specification's formulae.

    Coarse detail about operators can be used to derive
    information about time/space complexity.
    """

    # formulae: typing.SymbolList2 = Field(
    #     default=[],
    #     description="Operators used in formulae",
    # )


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
    operators: typing.List[str] = Field(
        default=[],
        description="Logical operators that are used",
    )
    types: typing.List[str] = Field(
        default=[],
        description="Types that are used",
    )
    # def model_dump(self, **kwargs):
    #     result = super().model_dump(**kwargs)
