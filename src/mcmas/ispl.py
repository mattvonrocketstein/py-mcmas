"""
**mcmas.ispl**:

Pydantic models for holding ISPL programs and program- fragments.
"""

import inspect
import json
import os
import sys

import pydantic
from pydantic import Field

import mcmas

# from . import typing
from mcmas import fmtk, typing, util
from mcmas.logic import symbols  # noqa
from mcmas.models import spec

from . import sim

Actions = typing.ActionsType

LOGGER = util.get_logger(__name__)
parser = util.lazy_module("mcmas.parser")

###############################################################################


class IFragment(fmtk.Fragment):
    """
    A piece of an ISPL Specification.

    May or may not be "concrete" as of yet, i.e. this may not yet
    be useful for actually running a simulation!
    """

    def update(self, data: dict) -> typing.Self:
        for k, v in self.model_dump().items():
            setattr(self, k, v)
        return self
        # update = self.dict()
        # update.update(data)
        # for k,v in self.validate(update).dict(exclude_defaults=True).items():
        # # .debug(f"updating value of '{k}' from '{getattr(self, k, None)}' to '{v}'")
        #     setattr(self, k, v)
        # return self

    def model_validate(self) -> typing.Dict:
        return dict(
            metadata=self.metadata.model_dump(),
            validates=self.validates,
            advice=self.advice,
        )


class ISpec(fmtk.Specification):
    """
    
    """


###############################################################################


class Environment(IFragment):
    """
    A wrapper for ISPL Environments.

    See
    http://mattvonrocketstein.github.io/py-mcmas/isplref/#environment
    """

    REQUIRED: typing.ClassVar = ["protocol", "evolution", "actions"]

    @classmethod
    @pydantic.validate_call
    def from_source(kls, txt: str) -> typing.Self:
        agents = parser.extract_agents(txt)
        env = agents.pop("Environment", None)
        assert env is not None
        return Environment(**env)

    actions: typing.ActionsType = Field(
        default=[],
        description="",
    )
    evolution: typing.EvolType = Field(
        default=[],
        description="",
    )
    protocol: typing.ProtocolType = Field(
        default={},
        description="",
    )
    vars: typing.VarsType = Field(
        description="",
        default={},
    )
    obsvars: typing.ObsVarsType = Field(
        description="",
        default={},
    )


class Agent(IFragment):
    """
    A wrapper for ISPL Agents.

    See
    http://mattvonrocketstein.github.io/py-mcmas/isplref/#agent
    """

    REQUIRED: typing.ClassVar = ["protocol", "evolution", "actions"]
    parser: typing.ClassVar

    name: str = Field(
        default="player",
        description=("Name of this agent"),
    )
    actions: typing.ActionsType = Field(
        default=[],
        description="Set of actions that are available to this agent",
    )

    vars: typing.VarsType = Field(
        default={},
        description="",
    )
    evolution: typing.EvolType = Field(
        default=[],
        description="",
    )
    protocol: typing.ProtocolType = Field(
        description="",
        default=[],
    )
    obsvars: typing.ObsVarsType = Field(
        description="",
        default={},
    )
    lobsvars: typing.LobsvarsType = Field(
        description="",
        default=[],
    )
    red_states: typing.List[str] = Field(
        description="",
        default=[],
    )

    @classmethod
    def trivial_agent(kls):
        """
        Smallest legal agent.
        """
        return kls(
            name="trivial",
            vars=dict(ticking="boolean"),
            actions=["tick"],
            protocol=["Other : {tick}"],
            evolution=["waiting=true if Action=wait;"],
        )

    def model_dump_source(self):
        """
        Dump the source-code for this piece of the specification.
        """
        return util.dict2ispl(dict(agents={self.name: self.model_dump()}))

    def model_complete(self):
        if not self.advice:
            return self
        else:
            tmp = self
            defaults = dict(
                protocol=["Other: {none};"],
                vars=dict(thinking="boolean"),
                evolution=["thinking=true if bob.Action = tool2;"],
            )
            for x in ["protocol", "vars", "evolution"]:
                if getattr(self, x, None):
                    pass
                else:
                    LOGGER.warning(f"could not find required {x}")
                    tmp = tmp.model_copy(update={x: defaults[x]})
            return tmp

    @util.classproperty
    def parser(self):
        return parser.extract_agents

    @classmethod
    @pydantic.validate_call
    def from_pydantic_agent(kls, pagent, **extra) -> typing.Self:
        """
        
        """
        from mcmas import ctx

        pydantic_ai = ctx.get_pydantic_ai()
        out = None
        if pydantic_ai and pagent:
            actions = list(pagent._function_toolset.tools.keys())
            return kls(
                name=pagent.name,
                actions=actions,
                metadata=dict(
                    parser=f"{kls.__module__}.{kls.__name__}.from_pydantic_agent",
                    file=inspect.getfile(pagent.__class__),
                ),
                **extra,
            )
        return out

    @classmethod
    @pydantic.validate_call
    def from_source(kls, txt, strict: bool = False) -> typing.Self:
        # def from_source(kls, txt, strict: bool = False) -> Dict[str, Self]:
        """
        
        """
        agents = kls.parser(txt)
        agents.pop("Environment", None)
        if len(agents) != 1:
            LOGGER.critical("from_source: more than 1 agent! returning first..")
        return Agent(**list(agents.values())[0])

    @property
    def local_advice(self) -> list:
        return []


class ISPL(IFragment):
    """
    An A wrapper for ISPL specifications.

    This permits partials or "fragments", i.e. the specification
    need not be complete and ready to run.

    See
    http://mattvonrocketstein.github.io/py-mcmas/isplref
    """

    # Metadata: typing.ClassVar = fmtk.SpecificationMetadata
    REQUIRED: typing.ClassVar = ["agents", "evaluation", "formulae"]
    parser: typing.ClassVar
    title: str = Field(
        default="Untitled Model",
        description="Optional title.  Used as a comment at the top of the file",
    )
    agents: typing.Dict[str, Agent] = Field(
        default={},
        description="All agents involved in this specification.  A map of {name: agent_object}",
    )
    environment: Environment = Field(
        default={},
        description="The environment for this specification",
    )
    fairness: typing.Dict[str, typing.List[str]] = Field(
        default={},
        description="",
    )
    init_states: typing.InitStateType = Field(
        default=[],
        description="Initial states for this specification.",
    )
    evaluation: typing.EvalType = Field(
        default=[],
        description="Calculations, composites, aggregates that can be referenced in formulae",
    )
    groups: typing.GroupsType = Field(
        default={},
        description="Group memberships.  A map of {group_name: [member1, .. ]}",
    )

    formulae: typing.FormulaeType = Field(
        description=(
            "A list of formulas.\n\n"
            "These will be partitioned into true/false categories, per the rest of the model"
        ),
        default=[],
    )
    simulation: sim.SimType = Field(
        default=None,
        description=(
            "The result of simulating this specification.  "
            "Empty if simulation has never been run"
        ),
    )
    source_code: typing.Union[str, None] = Field(
        default=None,
        description=(
            "Source code for this specification.  "
            "Only available if the specification was loaded from raw ISPL"
        ),
    )

    def __invert__(self):
        """Model interpolation: returns this model"""
        if not self.advice:
            LOGGER.warning(f"{self} has no advice and appears complete, returning it.")
            return self
        else:
            raise NotImplementedError([self])

    def __iadd__(self, other):
        """
        Specification algebra.

        This is for in-place addition, i.e. `spec+=Agent(..)`
        """
        upd = self + other
        self.update(upd.model_dump())
        return self

    def __add__(self, other):
        """
        Specification algebra.

        ISPL + agent => adds agent to spec ISPL + ISPL => update
        1st with 2nd ISPL+ environment => adds agent to
        """
        if isinstance(other, (ISPL,)):
            return self.model_copy(update=other.model_dump())
        if isinstance(other, (Environment,)):
            return self.model_copy(update=dict(environment=other))
        if isinstance(other, (Agent,)):
            agents = self.agents
            agents.update(**{other.name: other})
            return self.model_copy(update=dict(agents=agents))
        if isinstance(other, (ISPL,)):
            raise Exception(f"niy {type(other)}")

    def model_dump_source(self):
        """
        Dump the source-code for this piece of the specification.
        """
        # from mcmas.engine import dict2ispl
        return util.dict2ispl(self.model_dump())

    @util.classproperty
    def parser(self):
        """
        Shortcut for `mcmas.parser.parse`
        """
        return parser.parse

    @property
    def local_advice(self) -> list:
        """
        Returns advice (known blockers for validation/execute)
        for this object and known subcomponents.
        """
        out = []
        for agent in self.agents:
            agentish = self.agents[agent]
            out += agentish.advice
        return out

    @classmethod
    @pydantic.validate_call
    def from_source(kls, txt, strict: bool = False) -> typing.Dict[str, typing.Self]:
        # from mcmas import parser
        return kls.parser(txt)

    # @classmethod
    # def from_file(kls, fname: str):
    #     import mcmas
    #     with open(fname) as fhandle:
    #         data = mcmas.parser.parse(fhandle.read())
    #     return kls(**data)

    @classmethod
    @pydantic.validate_call
    def load_from_ispl_file(kls, file: str = None, text=None):
        LOGGER.critical(f"ISPL.load_from_ispl_file: {file}")
        metadata = dict(file=file)
        if file:
            assert os.path.exists(file), f"no such file: {file}"
            if file.endswith("ispl"):
                with open(file) as fhandle:
                    text = fhandle.read()
                    tmp = kls.parser(text, file=file)
                    data = tmp.model_dump(exclude="metadata")
                    return ISPL(metadata=ISPL.Metadata(**metadata), **data)
            #    return ISPL(metadata=dict(file=file, engine="bonk"), **data)
            elif file.endswith("json"):
                raise ValueError("refusing to work with ispl file")
            elif file in ["-", "/dev/stdin"]:
                metadata.update(file="<<stream>>")
                text = sys.stdin.read().strip()
                data = kls.parser(text).model_dump(exclude="metadata")
                return ISPL(metadata=ISPL.Metadata(**metadata), **data)
            else:
                LOGGER.critical(f"could not create model from {file}")
                raise Exception(file)
        if text:
            LOGGER.critical("NIY")
            raise Exception(text)

    @classmethod
    @pydantic.validate_call
    def load_from_json_file(kls, file: str = None, text=None):
        """
        
        """
        LOGGER.critical(f"ISPL.load_from_json_file: {file}")
        metadata = dict(file=file)
        if file:
            assert os.path.exists(file), f"no such file: {file}"
            if file.endswith("json"):
                with open(file) as fhandle:
                    data = json.loads(fhandle.read())
                return ISPL(metadata=ISPL.Metadata(**metadata), **data)
            elif file.endswith("ispl"):
                raise ValueError("refusing to work with ispl file")
            elif file in ["-", "/dev/stdin"]:
                metadata.update(file="<<stream>>")
                text = sys.stdin.read().strip()
                data = json.loads(text)
                return ISPL(
                    metadata=ISPL.Metadata(**{**data.pop("metadata", {}), **metadata}),
                    **data,
                )
            else:
                LOGGER.critical(f"could not create model from {file}")
                raise Exception(file)

        if text:
            LOGGER.critical("NIY")
            raise Exception(text)

    @property
    @pydantic.validate_call
    def validates(self) -> bool:
        """
        Asks the engine whether this spec validates.

        NB: no caching
        """
        return mcmas.engine.validate(model=self)

    @pydantic.validate_call
    def model_dump_analysis(self) -> spec.Analysis:
        """
        
        """

        meta = spec.Analysis(
            symbols=spec.SymbolMetadata(agents=[], actions=[], vars=[])
        )
        out = meta.symbols
        ents = list(self.agents.items()) + [["Environment", self.environment]]
        for name, agent in ents:
            out.agents.append(name)
            if not isinstance(agent, (Environment,)):
                out.vars += [k for k in (agent.lobsvars or [])]
            out.vars += [k for k in (agent.vars or [])]
            for action in agent.actions:
                out.actions.append(action)
        out.actions = [getattr(symbols, x) for x in sorted(list(set(out.actions)))]
        out.vars = [getattr(symbols, x) for x in sorted(list(set(out.vars)))]
        out.agents = [getattr(symbols, x) for x in sorted(list(set(out.agents)))]
        return meta

    def exec(self, strict: bool = False, **kwargs):
        """
        
        """
        import mcmas

        required = ["init_states"]
        self.logger.debug(f"validating: {self.source_code or self.model_dump_source()}")

        # check advice before execution
        if self.advice:
            msg = "exec: Model has non-empty advice!"
            LOGGER.critical(msg)
            if strict:
                raise RuntimeError(msg)

        for k in required:
            if not getattr(self, k):
                err = f"Validation failed.  Required key `{k}` is missing."
                return self.model_copy(
                    update={
                        # "source_code": src,
                        "simulation": mcmas.models.Simulation(
                            error=err,
                            metadata=mcmas.models.Simulation.Metadata(
                                parsed=False, validates=False
                            ),
                        ),
                    }
                )

        self.logger.debug("starting..")
        # sim = engine(output_format="model", **model_dump_source
        sim = mcmas.engine(text=self.model_dump_source(), output_format="model")
        # metadata = {
        #     # **sim.metadata.model_dump(),
        #     **self.metadata,
        # }
        out = self.model_copy(
            update=dict(
                source_code=self.source_code or self.model_dump_source(),
                simulation=sim,
                metadata=self.metadata.model_dump(),
            )
        )
        self.logger.debug("done")
        return out

    def repl(self):
        result_model = self.exec()
        return util.repl(model=result_model)


# def make_strict(model: type[spec.Specification]) -> type[spec.Specification]:
#     """
#     Creates a new Pydantic model where all fields from the input model are
#     required, effectively removing any default values.
#     """
#     strict_fields = {}
#     for field_name, field_info in model.model_fields.items():
#         # if field_name=='obsvars': raise Exception(field_info)
#         # Create a new FieldInfo object without default values
#         # data = field_info.model_dump()
#         if not field_info.is_required:
#             LOGGER.critical(f"not required {field_info}")
#             field = Field(
#                 default=field_info.default,
#                 is_required=field_info.is_required,
#                 alias=field_info.alias)
#         else:
#             field = Field(default=PydanticUndefined, alias=field_info.alias)
#         strict_fields[field_name] = field_info.annotation, field
#     # Dynamically create the new model
#     strict_model = create_model(f"Strict{model.__name__}", **strict_fields)
#     return strict_model
# class strict:
#     Agent = make_strict(Agent)
#     ISPL = make_strict(ISPL)
