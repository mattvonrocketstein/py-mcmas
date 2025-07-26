"""
mcmas.models.sim Pydantic models for Simulations, i.e. data
available after running model-checking.
"""

import typing
from typing import Dict, List, Union

import pydantic
from pydantic import Field

from mcmas import fmtk, util  # import SpecificationMetadata
from mcmas.models.util import BoolMaybe, Str2List

# from mcmas.util import get_logger


LOGGER = util.get_logger(__name__)


class BaseModel(pydantic.BaseModel):
    """
    
    """


class FormulaeResult(BaseModel):
    """
    FormulaeResult partitions Formulae as True/False.

    This is part of a Simulation object, only available after
    model- check runs.
    """

    true: List[str] = Field(description="true", default=[])
    false: List[str] = Field(description="false", default=[])


IntMaybe = Union[None, int]


class SimMetadata(fmtk.SpecificationMetadata):
    """
    SimMetadata describes status-related metadata from a
    simulation.

    This is part of a Simulation object, only available after
    model- check runs.
    """

    # specification: SpecificationMetadata = Field(description="", default=SpecificationMetadata())
    exit_code: IntMaybe = Field(description="", default=None)
    deadlock: BoolMaybe = Field(
        description=("Whether the simulation deadlocked"), default=None
    )
    validates: BoolMaybe = Field(
        description=(
            "Whether the Specification parsed successfully *and* had only has True facts"
        ),
        default=None,
    )
    parsed: BoolMaybe = Field(
        description="Whether or not the Specification parsed successfully",
        default=None,
    )
    timing: Dict = Field(
        default={},
        description="Timing details for execution, compilation, etc",
    )


SimMetadataType = Union[SimMetadata, None]


class SimBase(BaseModel):
    """
    A Simulation object is the result of having run a spec.

    NB: SimBase only has one use-case currently, but is intended to be
    generic. Don't overfit to ISPL/MCMAS
    """

    Metadata: typing.ClassVar = SimMetadata
    text: Str2List = Field(description="text", default=None)  # , exclude=True)
    error: Str2List = Field(description="error", default=None)  # , exclude=True)
    metadata: SimMetadataType = Field(description="model", default=None)
    state_space: Dict = Field(description="", default={})

    @property
    def failed(self):
        """
        
        """
        return bool(self.error)


class Simulation(SimBase):
    """
    A Simulation object is the result of having run a spec.

    In practice a Simulation in `py-mcmas` is always an ISPL program
    running on an MCMAS engine, but see `SimBase` for something more
    generic.
    """

    facts: FormulaeResult = Field(
        description="facts",
        default=FormulaeResult(),
    )


SimType = Union[Simulation, None]
