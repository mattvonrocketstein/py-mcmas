"""
mcmas.fmtk:

A growing formal methods toolkit. This is focused on abstract base classes
(pydantic models) that are intended to be useful for describing things like
"specifications" and "simulations" in general. Classes like ispl.Specification
and ispl.Simulation extend these, but the hopefully the base classes are more
reusable.

This might be reused to wrap other kinds of formalisms like:

* Other model-checkers (.. Alloy lang?)
* SAT & SMT Provers (.. Z3?)
* Constraints, Discrete-events, Systems Simulations (.. SimPy / CPMpy?)
* Games & Protocols, etc (.. py-mfglib?)
"""

import typing

import pydantic
from pydantic import Field

from mcmas import util
from mcmas.typing import PathType

LOGGER = util.get_logger(__name__)


class SpecificationMetadata(pydantic.BaseModel):
    """
    Metadata for this Specification.
    """

    file: PathType = Field(
        description="File associated with this specification", default=None
    )
    engine: str = Field(
        description="The engine that will be used for this specification",
        default="mcmas",
    )
    parser: str = Field(
        description="The parser that will be used for this specification",
        default="mcmas.parser",
    )


SpecificationMetadataType = typing.Union[SpecificationMetadata, None]


class SpecificationFragment(pydantic.BaseModel):
    """
    A Fragment of a Specification.

    NB: Fragments are incomplete by definition.
    """

    logger: typing.ClassVar = LOGGER
    Metadata: typing.ClassVar = SpecificationMetadata
    metadata: SpecificationMetadata = Field(
        description=(
            "Known metadata about this Specification.\n\n"
            "(Updated if/when the specification is analyzed or simulated)"
        ),
        default=SpecificationMetadata(),
        exclude=True,
    )

    @classmethod
    def get_trivial(kls, **kwargs):
        """
        Subclassers must implement this.

        Returns the trivial fragment for this type.
        """
        raise NotImplementedError(f"{kls}")

    @classmethod
    def load_from_source(kls, txt) -> typing.Self:
        """
        Subclassers must implement this.

        Creates spec-fragment from raw source-code.
        """
        raise NotImplementedError(f"{kls}")

    def model_dump_source(self) -> str:
        """
        Subclassers must implement this.

        Dumps raw source-code for this fragment.
        """
        raise NotImplementedError(f"{self}")

    @property
    def valid(self):
        """
        True if this agent is valid, i.e. ready to run and not a
        fragment.
        """
        return not any(
            [self.__class__.__name__ == "SpecificationFragment", self.advice]
        )

    concrete = valid

    @property
    def advice(self) -> list:
        """
        Returns a list of any problems with this object.

        See also `valid` property
        """
        required = getattr(self.__class__, "REQUIRED", [])
        if not required:
            LOGGER.warning(
                f"no attrs listed as required for {self}; advice unavailable"
            )
        return [
            f"MISSING-REQUIRED {f} from {self.__class__.__name__}"
            for f in required
            if not bool(getattr(self, f))
        ] + self.local_advice

    @property
    def local_advice(self) -> list:
        """
        Subclassers must implement this.
        """
        return []

    def __add__(self, other):
        """
        Subclassers must implement this.
        """
        raise TypeError(f"Cannot add {self} and {other}")

    def __and__(self, other):
        """
        Subclassers must implement this.
        """
        raise TypeError(f"Cannot `and` {self} and {other}")

    def __or__(self, other):
        """
        Subclassers must implement this.
        """
        raise TypeError(f"Cannot `or` {self} and {other}")


Fragment = SpecificationFragment


class Specification(SpecificationFragment):
    """
    Pydantic models for a Specification.
    """


#####################
from mcmas import typing


class AnalysisMeta(pydantic.BaseModel):
    """
    Metadata for a Specification Analysis.
    """

    formula_index: int = Field(default=-1)
    base_complexity: float = Field(default=0.0)
    nesting_coefficient: int = Field(default=1)
    raw_score: float = Field(default=0.0)


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


#########################


class SpecificationAnalysis(pydantic.BaseModel):
    """
    Base class for all Analysis results.
    """
