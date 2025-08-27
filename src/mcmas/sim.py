"""
mcmas.models.sim Pydantic models for Simulations, i.e. data
available after running model-checking.
"""

import re

import pydantic
from pydantic import Field

from mcmas import fmtk, typing, util
from mcmas.models.util import BoolMaybe, Str2List

IntMaybe = typing.Union[None, int]
WitnessType = typing.List[typing.StringOrSymbol]  # , typing.StringOrSymbol]
WitnessesType = typing.Union[typing.Dict[str, WitnessType], None]


LOGGER = util.get_logger(__name__)


@pydantic.validate_call
def normalize_formula(expression: str) -> typing.List:
    """
    Find all alphanumeric words in an expression.
    """
    pattern = r"[a-zA-Z0-9._-]+"
    return list(re.findall(pattern, expression))


class FormulaeResult(pydantic.BaseModel):
    """
    FormulaeResult partitions Formulae as True/False.

    This is part of a Simulation object, only available after
    model- check runs.
    """

    true: typing.List[str] = Field(description="true", default=[])
    false: typing.List[str] = Field(description="false", default=[])

    def __getitem__(self, k):
        """
        
        """
        return getattr(self, k)


class SimMetadata(fmtk.SpecificationMetadata):
    """
    SimMetadata describes status-related metadata from a
    simulation.

    This is part of a Simulation object, only available after
    model- check runs.
    """

    exit_code: IntMaybe = Field(
        default=None, description="Posix exit code from the sim process"
    )
    deadlock: BoolMaybe = Field(
        default=None,
        description=("Whether this simulation deadlocked"),
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
    timing: typing.Dict = Field(
        default={},
        description="Timing details for execution, compilation, etc",
    )


SimMetadataType = typing.Union[SimMetadata, None]


class SimBase(pydantic.BaseModel):
    """
    A Simulation object is the result of having run a spec.

    NB: SimBase only has one use-case currently, but is intended to be
    generic. Don't overfit to ISPL/MCMAS
    """

    Metadata: typing.ClassVar = SimMetadata
    # spec: typing.Any = Field(description='Back-link to specification',)
    text: Str2List = Field(description="text", default=None)
    error: Str2List = Field(description="error", default=None)
    metadata: SimMetadataType = Field(description="model", default=None)
    state_space: typing.Dict = Field(description="", default={})
    witnesses: WitnessesType = Field(
        description=(
            "Witnesses, counter-examples, traces.  "
            "These are obtained by parsing mcmas .info files.  "
            "By default witnesses cover as many facts as possible; "
            "Use instead `counter_examples` to limit this to only FALSE statements."
        ),
        default=None,
    )
    facts: FormulaeResult = Field(
        description="Input formulae partitioned as true / false",
        default=FormulaeResult(),
    )

    @property
    def spec(self):
        """
        Backlink to the specification for this Sim.
        """
        from mcmas import ispl

        return ispl.ISPL.load_from_file(self.metadata.file)

    @property
    def counter_examples(self) -> WitnessesType:
        """
        That subset of witnesses which refer to FALSE formulae.
        """
        spec = self.spec
        assert spec, f"spec not set for {self}"
        witnesses = self.witnesses.items()
        if not witnesses:
            LOGGER.critical(f"no witnesses are available yet for {self}")
        falseys = self.facts["false"]
        truth = self.facts["true"]
        truth = [normalize_formula(x) for x in truth]
        falseys = [normalize_formula(x) for x in falseys]
        # from mcmas.logic import symbols
        # # raise Exception(list(map(eval,truth)))
        out = {}
        for i, item in enumerate(witnesses):
            formula, states = item
            nform = normalize_formula(formula)
            if nform in falseys:
                LOGGER.critical(f"found {formula}")
                out[formula] = states
            else:
                assert (
                    nform in truth
                ), f"{formula} missing from all facts?\n{self.facts}"
        return out

    @property
    def failed(self) -> typing.Bool:
        """
        True if this simulation failed.
        """
        return bool(self.error)


class Simulation(SimBase):
    """
    A Simulation object is the result of having run a spec.

    In practice a Simulation in `py-mcmas` is always an ISPL program
    running on an MCMAS engine, but see `SimBase` for something more
    generic.
    """


SimType = typing.Union[Simulation, None]
