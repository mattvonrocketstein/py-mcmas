"""
mcmas.fmtk:

A growing formal methods toolkit. This is focused on abstract base classes
(pydantic models) that are intended to be useful for describing "specifications"
and "simulations" in general. Classes like ispl.Specification and ispl.Simulation
extend these, but the hopefully the base classes are more reusable.

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

    Incomplete by definition.
    """

    logger: typing.ClassVar = LOGGER
    Metadata: typing.ClassVar = SpecificationMetadata
    metadata: SpecificationMetadata = Field(
        description=(
            "Known metadata about this Specification.\n\n"
            "(Updated if/when the specification is analyzed or simulated)"
        ),
        default=SpecificationMetadata(),
    )

    @classmethod
    def _get_trivial_example(kls):
        """
        Subclassers must implement this.
        """
        raise NotImplementedError(f"{kls}")

    @classmethod
    def from_source(kls, txt) -> typing.Self:
        """
        Creates this piece of a specification from raw source-
        code.
        """
        raise NotImplementedError(f"{kls}")

    def model_dump_source(self) -> str:
        """
        Subclassers must implement this.
        """
        raise NotImplementedError(f"{self}")

    @property
    def concrete(self):
        """
        True if this agent is concrete, i.e. ready to run and not
        a fragment.
        """
        return not self.advice

    @property
    def advice(self) -> list:
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


Fragment = SpecificationFragment


class Specification(SpecificationFragment):
    """
    Pydantic models for a Specification.
    """


class SpecificationAnalysis(pydantic.BaseModel):
    """
    Base class for all Analysis results.
    """
