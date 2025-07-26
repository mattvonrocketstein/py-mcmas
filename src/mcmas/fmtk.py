"""
mcmas.fmtk:

A growing formal methods toolkit. This is focused on abstract base classes
(pydantic models) that are intended to be useful for describing "specifications"
and "simulations" in general. For py-mcmas *specifically*, of course we need to
cover ISPL.  (See instead `mcmas.ispl` if that's what you're interested in)

Hopefully the stuff here is much more reusable and generic, and might be reused to wrap other kinds of formalisms like:

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

# from mcmas.models.util import PathType


LOGGER = util.get_logger(__name__)


class SpecificationMetadata(pydantic.BaseModel):
    """
    
    """

    file: PathType = Field(description="", default=None)
    engine: str = Field(description="", default="mcmas")
    parser: str = Field(description="", default="mcmas.parser")


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
    def from_source(kls, txt) -> typing.Self:
        """
        Creates this piece of a specification from raw source-
        code.
        """
        raise NotImplementedError(f"{kls}")

    def model_dump_source(self) -> str:
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
        return []

    def __add__(self, other):
        raise TypeError(f"Cannot add {self} and {other}")


Fragment = SpecificationFragment


class Specification(SpecificationFragment):
    """
    Pydantic models for a Specification.
    """


class SpecificationAnalysis(pydantic.BaseModel):
    """
    
    """
