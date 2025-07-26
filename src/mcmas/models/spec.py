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
    """

    actions: typing.SymbolList2 = Field(
        description="Actions list",
        default=[],
    )
    agents: typing.SymbolList2 = Field(
        description="Agents list",
        default=[],
    )
    vars: typing.SymbolList2 = Field(
        description="Var list",
        default=[],
    )


class OpMetadata(pydantic.BaseModel):
    formulae: typing.SymbolList2 = Field(
        description="Operators used in formulae",
        default=[],
    )


class Analysis(fmtk.SpecificationAnalysis):
    """
    Another view of symbol metadata.
    """

    symbols: SymbolMetadata = Field(
        description="Symbols (includes vars+actions)",
        default=SymbolMetadata(),
    )
    operators: OpMetadata = Field(
        description="Logical operators that are used",
        default=OpMetadata(),
    )

    # def model_dump(self, **kwargs):
    #     result = super().model_dump(**kwargs)
