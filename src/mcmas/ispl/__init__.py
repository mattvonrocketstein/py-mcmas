"""
mcmas.ispl:

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
from mcmas.sim import SimType, Simulation

Actions = typing.ActionsType

LOGGER = util.get_logger(__name__)

###############################################################################


class Fragment(fmtk.Fragment):
    """
    A piece of an ISPL Specification.

    May or may not be "concrete" as of yet, i.e. this may not yet
    be useful for actually running a simulation!
    """

    # def model_dump_json(self, **kwargs):
    #     exclude=kwargs.pop('exclude', [])
    #     exclude= ['metadata']+exclude if 'metadata' not in exclude else exclude
    #     return super().model_dump_json(exclude=exclude, **kwargs)

    @pydantic.validate_call
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

    @pydantic.validate_call
    def spec_validate(self) -> typing.Dict:
        return dict(
            metadata=self.metadata.model_dump(),
            validates=self.validates,
            advice=self.advice,
        )

    def __invert__(self):
        """Model interpolation: returns this model"""
        if not self.advice:
            LOGGER.warning(f"{self} has no advice and appears complete, returning it.")
            return self
        else:
            err = f"Not sure how from complete object like {self}"
            LOGGER.critical(err)
            raise NotImplementedError(err)


###############################################################################


class Environment(Fragment):
    """
    A wrapper for ISPL Environments. Environments models the
    shared infrastructure and boundary conditions that all
    standard agents can observe.

    See
    http://mattvonrocketstein.github.io/py-mcmas/isplref/#environment
    """

    REQUIRED: typing.ClassVar = ["protocol", "evolution", "actions"]

    @classmethod
    @pydantic.validate_call
    def from_source(kls, txt: str) -> typing.Self:
        """
        Creates an Environment from string.
        """
        from mcmas import parser

        agents = parser.extract_agents(txt)
        env = agents.pop("Environment", None)
        assert env is not None
        return Environment(**env)

    actions: typing.ActionsType = Field(
        default=[],
        description="Defines the set of actions an agent can perform, which are visible to all other agents.",
    )
    evolution: typing.EvolType = Field(
        default=[],
        description="How variables change based on actions",
    )
    protocol: typing.ProtocolType = Field(
        default={},
        description="Action selection rules",
    )
    vars: typing.VarsType = Field(
        default={},
        description="Private variables - only the Environment can access",
    )
    obsvars: typing.ObsVarsType = Field(
        default={},
        description="Observable variables - can be seen by other agents",
    )


class Agent(Fragment):
    """
    A wrapper for ISPL Agents.

    See
    http://mattvonrocketstein.github.io/py-mcmas/isplref/#agent
    """

    TrivialAgent: typing.ClassVar
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
        description="Defines how an agent's local variables change in response to the actions performed by all agents.",
    )
    protocol: typing.ProtocolType = Field(
        description="Defines the rules for when an agent can perform specific actions based on its current state",
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

    def analyze_types(self) -> typing.List[str]:
        """
        
        """
        types = []
        types += self.vars.values()
        types += self.obsvars.values()
        types = sorted(list({x.strip() for x in types}))
        return types

    def analyze_symbols(self) -> typing.List[str]:
        """
        
        """
        return spec.SymbolMetadata(
            agents=[self.name],
            actions=self.actions,
            vars=[k.strip() for k in list(self.lobsvars) + list(self.vars)],
        )

    # def analyze_operators(self):
    #     """"""
    #     operators = []
    #     for frm in self.formulae:
    #         for op in ["AF", "X", "F", "G", "U", "A", "E", "AG", "EF", "AX", "EG", "K", "GK", "GCK", "DK"]:
    #             if f"{op}(" in frm:
    #                 operators.append(op)
    #     return sorted(list(set(operators)))

    @property
    @pydantic.validate_call
    def analysis(self) -> spec.Analysis:
        """
        Static-analysis for this ISPL specification.

        Returns details about symbols and logical operators.
        """
        return spec.Analysis(
            symbols=self.analyze_symbols(),
            operators=[],
            # self.analyze_operators(),
            types=self.analyze_types(),
        )
        # out.actions = [getattr(symbols, x) for x in sorted(list(set(out.actions)))]
        # out.vars = [getattr(symbols, x) for x in sorted(list(set(out.vars)))]
        # out.agents = [getattr(symbols, x) for x in sorted(list(set(out.agents)))]
        # return meta

    @pydantic.validate_call
    def __invert__(self) -> typing.Self:
        """Model interpolation: returns this model"""
        """
        Trigger completion for this Agent.

        This makes minimal changes to
        This is NOT backed by an LLM; see instead `mcmas.ai.agent_completion`.
        """
        if not self.advice:
            LOGGER.warning(
                f"{self} is already valid, returning it instead of completing"
            )
            return self
        else:
            tmp = self
            trivial = TrivialAgent
            defaults = dict(
                protocol=trivial.protocol,
                vars=trivial.vars,
                evolution=trivial.evolution,
            )
            for x in ["protocol", "vars", "evolution"]:
                if getattr(self, x, None):
                    pass
                else:
                    LOGGER.warning(f"could not find required {x}")
                    tmp = tmp.model_copy(update={x: defaults[x]})
            return tmp.model_copy(
                update=dict(actions=list(set(tmp.actions + trivial.actions)))
            )

    model_completion = __invert__

    @util.classproperty
    def TrivialAgent(kls):
        return kls._trivial_agent()

    @classmethod
    def _get_trivial_example(kls):
        """
        Smallest legal agent.
        """
        return kls(
            name="trivial",
            vars=dict(ticking="boolean"),
            actions=["tick"],
            protocol=["Other : {tick}"],
            # ["Other: {none};"]
            evolution=["ticking=true if Action=tick;"],
            # ["thinking=true if bob.Action = tool2;"]
        )

    def model_dump_source(self):
        """
        Dump the source-code for this piece of the specification.
        """
        return util.dict2ispl(dict(agents={self.name: self.model_dump()}))

    @util.classproperty
    def parser(self) -> typing.Callable:
        """
        Return an appropriate parser for this spec-fragment.
        """
        from mcmas import parser

        return parser.extract_agents

    @classmethod
    @pydantic.validate_call
    def from_pydantic_agent(kls, pagent, **extra) -> typing.Self:
        """
        Create ISPL agent from the given pydantic agent.
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
            ).model_completion()
        return out

    @classmethod
    @pydantic.validate_call
    def from_source(kls, txt, strict: bool = False) -> typing.Self:
        """
        Load ISPL agent from string.
        """
        agents = kls.parser(txt)
        agents.pop("Environment", None)
        if len(agents) != 1:
            LOGGER.critical("from_source: more than 1 agent! returning first..")
        return Agent(**list(agents.values())[0])

    @property
    def local_advice(self) -> list:
        return []


TrivialAgent = Agent._get_trivial_example()


class ISpec(fmtk.Specification):
    """
    
    """


class ISPL(Fragment):
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
        description=(
            "Specifies conditions that must hold infinitely often along "
            "all execution paths, used to rule out unrealistic behaviors."
        ),
    )
    init_states: typing.InitStateType = Field(
        default=[],
        description="Initial global states of the system when verification begins.",
    )
    evaluation: typing.EvalType = Field(
        default=[],
        description="Calculations, composites, aggregates that can be referenced in formulae",
    )
    groups: typing.GroupsType = Field(
        default={},
        description=(
            "A map of {group_name: [member1, .. ]}"
            "Defines collections of agents for use in group-based verification formulae."
        ),
    )

    formulae: typing.FormulaeType = Field(
        description=(
            "A list of formulas.\n\n"
            "These will be partitioned into true/false categories, per the rest of the model"
        ),
        default=[],
    )
    simulation: SimType = Field(
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
        from mcmas import parser

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
        """
        Return ISPL object from given string.
        """
        # from mcmas import parser
        return kls.parser(txt)

    @classmethod
    @pydantic.validate_call
    def load_from_ispl_file(kls, file: str = None, text=None):
        """
        Return ISPL object from contents of given file.
        """
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

    load_from_file = load_from_ispl_file

    @classmethod
    @pydantic.validate_call
    def load_from_json_file(kls, file: str = None, text=None):
        """
        Return ISPL object from the contents of given file.

        File *must* be JSON encoded.
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

    @property
    @pydantic.validate_call
    def analysis(self) -> spec.Analysis:
        """
        Static-analysis for this ISPL specification.

        Returns details about symbols and logical operators.
        """
        operators = []
        for frm in self.formulae:
            for op in [
                "AF",
                "X",
                "F",
                "G",
                "U",
                "A",
                "E",
                "AG",
                "EF",
                "AX",
                "EG",
                "K",
                "GK",
                "GCK",
                "DK",
            ]:
                if f"{op}(" in frm:
                    operators.append(op)
        types = []
        agents = list(self.agents.values()) + [self.environment]
        for agent in agents:
            types += agent.vars.values()
            types += agent.obsvars.values()
        types = sorted(list({x.strip() for x in types}))
        meta = spec.Analysis(
            symbols=spec.SymbolMetadata(agents=[], actions=[], vars=[]),
            operators=sorted(list(set(operators))),
            types=types,
        )
        out = meta.symbols
        ents = list(self.agents.items()) + [["Environment", self.environment]]
        for name, agent in ents:
            out.agents.append(name)
            if not isinstance(agent, (Environment,)):
                out.vars += [k.strip() for k in (agent.lobsvars or []) if k.strip()]
            out.vars += [k.strip() for k in (agent.vars or []) if k.strip()]
            for action in agent.actions:
                out.actions.append(action)
        out.actions = [getattr(symbols, x) for x in sorted(list(set(out.actions)))]
        out.vars = [getattr(symbols, x) for x in sorted(list(set(out.vars)))]
        out.agents = [getattr(symbols, x) for x in sorted(list(set(out.agents)))]
        return meta

    def exec(self, strict: bool = False, **kwargs):
        """
        Execute this ISPL specification.
        """
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
                        "simulation": Simulation(
                            error=err,
                            metadata=Simulation.Metadata(parsed=False, validates=False),
                        ),
                    }
                )

        self.logger.debug("starting..")
        sim = mcmas.engine(text=self.model_dump_source(), output_format="model")
        out = self.model_copy(
            update=dict(
                source_code=self.source_code or self.model_dump_source(),
                simulation=sim,
                metadata=self.metadata.model_dump(),
            )
        )
        self.logger.debug("done")
        return out

    run_sim = run_simulation = exec

    def repl(self):
        """
        Start a REPL shell with this object available as `spec`.
        """
        result_model = self.exec()
        return util.repl(spec=result_model)


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
