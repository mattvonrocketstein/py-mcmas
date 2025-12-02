"""
mcmas.ispl:

Pydantic models for holding ISPL programs and program- fragments.
"""

import inspect
import json
import os
import sys
from typing import Optional

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


def check_slice(*args):
    assert len(args) in [0, 1]
    slice_maybe = args and args[0]
    if slice_maybe == Ellipsis or isinstance(slice_maybe, (slice, tuple, type(None))):
        return {}
    elif isinstance(slice_maybe, (dict,)):
        return slice_maybe
    else:
        err = f"expected slice or dict for posargs, got {[args, type(args)]}"
        LOGGER.warning(err)
        raise ValueError(err)


###############################################################################
ObsvarsField = Field(
    default={},
    description=("Observable variables.  Can be seen by other agents"),
)
VarsField = Field(
    default={},
    description=("Private variables. Only the Environment can access"),
)
ActionsField = Field(
    default=[],
    description=(
        "Defines the set of actions an agent can perform."
        "Visible to all other agents."
    ),
)
ProtocolField = Field(
    description=(
        "Action selection rules; how and when an agent can perform "
        "specific actions based on its current state"
    ),
    default=[],
)
EvolutionField = Field(
    default=[],
    description=(
        "Defines how an agent's local variables change in "
        "response to the actions performed by all agents."
    ),
)
###############################################################################


class Fragment(fmtk.Fragment):
    """
    A piece of an ISPL Specification.

    May or may not be "concrete" as of yet, i.e. this may not yet
    be useful for actually running a simulation!
    """

    PROMPT_HINTS: typing.ClassVar = ""
    logger: typing.ClassVar = LOGGER

    def __init__(self, *args, **kwargs):
        """
        
        """
        if args and args[0] and args[0] == Ellipsis:
            tmp = self.__class__.get_trivial().model_dump()
            tmp.update(**kwargs)
            super().__init__(**tmp)
        else:
            super().__init__(*args, **kwargs)

    def __call__(self, **kwargs):
        """
        
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def __lt__(self, other) -> bool:
        """
        Specification algebra.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot compare {type(self)} and {type(other)}")
        return self.COMPARATOR(self) < self.COMPARATOR(other)

    def __gt__(self, other) -> bool:
        """
        Specification algebra.
        """
        return not self.__lt__(other)

    def __class_getitem__(kls, other):
        """
        
        """
        if other == Ellipsis:
            return kls(other)
        else:
            mod_name = other.__class__.__module__
            cname = "_load_from_" + mod_name.replace(".", "_")
            tname = "_load_from_" + type(other).__name__
            alt = getattr(kls, tname, None)
            constructor = getattr(kls, cname, alt)
            if constructor is None:
                err = (
                    f"could not find constructor for `{kls}.{cname}` or `{kls}.{tname}`"
                )
                LOGGER.critical(err)
                raise ValueError(err)
            else:
                LOGGER.info(f"using constructor: {constructor}")
                return constructor(other)

    @classmethod
    def _load_from_prompt(kls, txt, **extra) -> typing.Self:
        """
        Create ISPL agent from the given prompt.
        """
        import pydantic_ai

        from mcmas.ai import DEFAULT_PROMPT, config

        hints = """"""
        prompt = DEFAULT_PROMPT + kls.PROMPT_HINTS
        LOGGER.info(f"Attempting to load object from prompt:\n\n{prompt}")
        agent = (
            pydantic_ai.Agent(
                config.DEFAULT_MODEL,
                output_type=pydantic_ai.PromptedOutput(
                    [kls],
                    template=prompt,
                ),
            )
            .run_sync(txt)
            .output
        )
        # FIXME: agent-only post-processing; move to subclass
        if hasattr(agent, "name"):
            agent.name = agent.name.lower()
        agent.metadata.parser = f"{kls.__module__}.{kls.__name__}._load_from_prompt"
        return agent

    _load_from_str = _load_from_prompt

    def analyze_types(self) -> typing.List[str]:
        """
        
        """
        types = []
        types += getattr(self, "vars", {}).values()
        types += getattr(self, "obsvars", {}).values()
        types = sorted(list({x.strip() for x in types}))
        return types

    def analyze_complexity(self) -> typing.Dict:
        """
        
        """
        from mcmas.models import spec

        return [spec.ComplexityAnalysis()]

    @pydantic.validate_call
    def update(self, data: dict) -> typing.Self:
        """
        
        """
        for k, v in self.model_dump().items():
            setattr(self, k, v)
        return self

    @pydantic.validate_call
    def spec_validate(self) -> typing.Dict:
        """
        Full validation output for this fragment (not a simple
        bool!)
        """
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


class Environment(Fragment):
    """
    Python wrapper for ISPL Environments. Environments model the
    shared information and boundary conditions that all other
    agents can observe.

    See also the relevant [ISPL reference](http://mattvonrocketstein.github.io/py-mcmas/isplref/#environment)
    """

    REQUIRED: typing.ClassVar = ["protocol", "actions"]
    DefaultEnvironment: typing.ClassVar
    actions: typing.ActionsType = ActionsField
    vars: typing.VarsType = VarsField
    obsvars: typing.ObsVarsType = ObsvarsField
    evolution: typing.EvolType = EvolutionField
    protocol: typing.ProtocolType = ProtocolField

    def __len__(self):
        """
        Specification Algebra.

        The length of an agent is the number of items in the
        description length
        """
        return sum(
            map(
                len,
                [
                    self.actions,
                    self.evolution,
                    self.obsvars,
                    self.protocol,
                    self.vars,
                    getattr(self, "lobsvars", []),
                    getattr(self, "red_states", []),
                ],
            )
        )

    @util.classproperty
    def DefaultEnvironment(kls):
        return kls(...)

    @classmethod
    def get_trivial(kls, *args, **kwargs):
        kwargs.update(check_slice(*args))
        actions = kwargs.pop("actions", [symbols.tick])
        protocol = kwargs.pop("protocol", dict(Other=[symbols.tick]))
        vars = kwargs.pop("vars", dict(ticking="boolean"))
        return kls(vars=vars, actions=actions, protocol=protocol, **kwargs)

    @classmethod
    @pydantic.validate_call
    def load_from_source(kls, txt: str) -> typing.Self:
        """
        Creates an Environment from string.
        """
        from mcmas import parser

        agents = parser.extract_agents(txt)
        env = agents.pop("Environment", None)
        assert env is not None
        return Environment(**env)


class Agent(Fragment):
    """
    Python wrapper for ISPL Agents.

    See also the relevant [ISPL reference](http://mattvonrocketstein.github.io/py-mcmas/isplref/#agent)
    """

    COMPARATOR: typing.ClassVar = len
    DefaultAgent: typing.ClassVar
    REQUIRED: typing.ClassVar = ["protocol", "evolution", "actions"]
    parser: typing.ClassVar

    name: str = Field(
        default="player",
        description=("Name of this agent"),
    )
    actions: typing.ActionsType = ActionsField
    evolution: typing.EvolType = EvolutionField
    obsvars: typing.ObsVarsType = ObsvarsField
    protocol: typing.ProtocolType = ProtocolField
    vars: typing.VarsType = VarsField

    lobsvars: typing.LobsvarsType = Field(
        description="",
        default=[],
    )
    red_states: typing.List[str] = Field(
        description="",
        default=[],
    )

    __len__ = Environment.__len__

    @util.classproperty
    def DefaultAgent(kls):
        """
        Returns the trivial agent.
        """
        return kls(...)

    @classmethod
    def _load_from_pydantic_ai_agent(kls, pagent, **extra) -> typing.Self:
        """
        Create ISPL agent from the given pydantic agent.
        """
        kls.logger.info(f"_load_from_pydantic_ai_agent: {pagent}")
        from mcmas import util

        name = pagent.name or f"Agent_{id(pagent)}"
        actions = list(pagent._function_toolset.tools.keys())
        tools = list(pagent._function_toolset.tools.values())
        tool = tools[0]
        if len(tools) > 1:
            kls.logger.warning(f"pydantic agent `{name}` has multiple tools!")
            kls.logger.warning(f"using just the first one: {tool}")
        # naive conversion from function signature to ISPL types.
        vars = util.fxn_sig.as_ispl_types(tool.function)
        vars.pop("ctx", None)
        return Agent(
            name=name,
            actions=actions,
            vars=vars,
            metadata=dict(
                parser=f"{kls.__module__}.{kls.__name__}._load_from_pydantic_ai_agent",
                file=inspect.getfile(pagent.__class__),
            ),
            **extra,
        ).model_completion()

    def analyze_symbols(self) -> typing.List[str]:
        """
        Returns symbol-related metadata including agent-names,
        actions, variables, and type info.
        """
        return spec.SymbolMetadata(
            agents=[self.name],
            actions=self.actions,
            vars=[k.strip() for k in list(self.lobsvars) + list(self.vars)],
            types=self.analyze_types(),
        )

    @property
    @pydantic.validate_call
    def analysis(self) -> spec.Analysis:
        """
        Static-analysis for this Agent specification.

        Returns details about symbols and logical operators.
        """
        return spec.Analysis(
            symbols=self.analyze_symbols(),
            types=self.analyze_types(),
            complexity=self.analyze_complexity(),
        )
        # out.actions = [getattr(symbols, x) for x in sorted(list(set(out.actions)))]
        # out.vars = [getattr(symbols, x) for x in sorted(list(set(out.vars)))]
        # out.agents = [getattr(symbols, x) for x in sorted(list(set(out.agents)))]
        # return meta

    def __pow__(self, other: float = 0.1) -> typing.Self:
        """
        
        """
        from mcmas import ai

        return ai.model_mutation(obj=self, model_settings=dict(top_p=other))

    def __invert__(self) -> typing.Self:
        """
        Trigger completion for this Agent.

        This is NOT backed by an LLM; see instead `mcmas.ai.agent_completion`.
        """
        if not self.advice:
            err = f"{self} is already valid, returning it instead of completing"
            LOGGER.warning(err)
            return self
        else:
            tmp = self
            trivial = DefaultAgent
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

    @classmethod
    def get_trivial(kls, *args, **kwargs):
        """
        Smallest legal agent.
        """
        kwargs.update(check_slice(*args))
        return kls(
            name="trivial",
            vars=dict(ticking="boolean"),
            actions=["tick"],
            protocol=["Other : {tick}"],
            evolution=["ticking=true if Action=tick;"],
        )

    def model_dump_source(self):
        """
        Dump the source-code for this piece of the specification.
        """
        from mcmas import rendering

        return rendering.get_template("Agent.j2").render(
            name=self.name, agent=self.model_dump()
        )

    @util.classproperty
    def parser(self) -> typing.Callable:
        """
        Return an appropriate parser for this spec-fragment.
        """
        from mcmas import parser

        return parser.extract_agents

    @classmethod
    @pydantic.validate_call
    def load_from_source(kls, txt, strict: bool = False) -> typing.Self:
        """
        Load ISPL agent from string.
        """
        agents = kls.parser(txt)
        agents.pop("Environment", None)
        if len(agents) != 1:
            LOGGER.critical("load_from_source: more than 1 agent! returning first..")
        return Agent(**list(agents.values())[0])

    @property
    def local_advice(self) -> list:
        return []


DefaultAgent = Agent.DefaultAgent
DefaultEnvironment = Environment.DefaultEnvironment


class ISpec(fmtk.Specification):
    """
    
    """


import functools
import operator


class ISPL(Fragment):
    """
    Python wrapper for ISPL specifications.

    This permits partials or "fragments", i.e. the specification need not be complete and ready to run.

    See the ISPL reference here: http://mattvonrocketstein.github.io/py-mcmas/isplref
    """

    PROMPT_HINTS: typing.ClassVar = "Individual proper nouns refer to separate agents."

    def __str__(self):
        return f"<ISPL: agents={len(self.agents)} vars={len(self.environment.vars)}>"

    def analyze_types(self):
        types = super().analyze_types()
        for agent in self.agents.values():
            types += agent.analyze_types()
        return list(set(types))

    @classmethod
    def get_trivial(kls, *args, **kwargs):
        """
        ISPL(...) notation.  Unlike ISPL(..)

        This returns the trivial specification, with just enough
        structure to validate and run, plus any optional
        overrides.
        """
        kwargs.update(check_slice(*args))
        title = kwargs.pop("title", "Minimal valid ISPL specification")
        agents = kwargs.pop("agents", {"DefaultAgent": DefaultAgent})
        environment = kwargs.pop("environment", Environment(...))
        evaluation = kwargs.pop("evaluation", ["ticking if Environment.ticking=true"])
        init_states = kwargs.pop("init_states", ["Environment.ticking=true"])
        formulae = kwargs.pop("formulae", ["ticking"])
        return kls(
            title=title,
            environment=environment,
            evaluation=evaluation,
            init_states=init_states,
            formulae=formulae,
            agents=agents,
            **kwargs,
        )

    # Metadata: typing.ClassVar = fmtk.SpecificationMetadata
    COMPARATOR: typing.ClassVar = abs
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

    def __contains__(self, other):
        """
        Specification algebra.
        """
        if isinstance(other, Agent):
            return other in self.agents.values()
        else:
            raise TypeError(f"__contains__ undefined for {[type(self), type(other)]}")

    def __abs__(self) -> float:
        """
        Specification algebra.

        Used in __lt__ and __gt__. For ISPL specifications this
        is the cumulative sum of formulae complexity
        """
        return sum([c.score for c in self.analyze_complexity()])

    def __iadd__(self, other):
        """
        Specification algebra.

        This is for in-place addition, i.e. `spec+=Agent(..)`
        """
        upd = self + other
        self.update(upd.model_dump())
        return self

    def __sub__(self, other):
        """
        Specification algebra.

        ISPL - agent => removes agent from this agent list, if present.
        """
        # if isinstance(other, (ISPL,)):
        #     return self.model_copy(update=other.model_dump())
        # if isinstance(other, (Environment,)):
        #     return self.model_copy(update=dict(environment=other))
        if isinstance(other, (Agent,)):
            agents = {}
            for a in self.agents.values():
                if a.name != other.name:
                    agents[a.name] = a
            return self.model_copy(update=dict(agents=agents))
        raise TypeError(f"Cannot add {type(self)} and {type(other)}")

    def __add__(self, other):
        """
        Specification algebra.

        ISPL + agent => adds agent to spec ISPL + ISPL =>
        overrides first spec with values from 2nd
        """
        if isinstance(other, (ISPL,)):
            return self.model_copy(update=other.model_dump())
        if isinstance(other, (Environment,)):
            return self.model_copy(update=dict(environment=other))
        if isinstance(other, (Agent,)):
            agents = self.agents
            agents.update(**{other.name: other})
            return self.model_copy(update=dict(agents=agents))
        raise TypeError(f"Cannot add {type(self)} and {type(other)}")

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
        
        """
        out = []
        for agent in self.agents:
            agentish = self.agents[agent]
            out += agentish.advice
        return out

    @classmethod
    @pydantic.validate_call
    def load_from_source(
        kls, txt, strict: bool = False
    ) -> typing.Dict[str, typing.Self]:
        """
        Return ISPL object from given string.
        """
        # from mcmas import parser
        return kls.parser(txt)

    @classmethod
    @pydantic.validate_call
    def load_from_ispl_file(
        kls,
        file: Optional[str] = None,
    ):
        """
        Return ISPL object from contents of given file.
        """
        LOGGER.debug(f"ISPL.load_from_ispl_file: {file}")
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
    def load_from_json_file(kls, file: Optional[str] = None, text=None):
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
        Asks the engine directly whether this spec validates.

        Note that this is ground-truth and not heuristic like the `valid` property elsewhere!
        """
        return mcmas.engine.validate(model=self)

    @property
    @pydantic.validate_call
    def analysis(self) -> spec.Analysis:
        """
        Static-analysis for this ISPL specification.

        Returns details about symbols and logical operators.
        """
        ents = list(self.agents.values())
        ents += [self.environment]
        vars = []
        for agent in ents:
            if isinstance(agent, (Agent,)):
                vars += [k.strip() for k in (agent.lobsvars or []) if k.strip()]
            vars += [k.strip() for k in (agent.vars or []) if k.strip()]
        vars = list(set(vars))
        meta = dict(
            symbols=spec.SymbolMetadata(
                agents=[agent for agent in self.agents],
                vars=vars,
                actions=list(
                    set(
                        functools.reduce(
                            operator.add,
                            [self.agents[agent].actions for agent in self.agents],
                        )
                    )
                ),
            ),
            types=self.analyze_types(),
            complexity=self.analyze_complexity(),
        )
        meta = spec.Analysis(**meta)
        return meta

    def analyze_complexity(self) -> typing.List:
        from mcmas.logic import complexity

        return [
            complexity.analyzer.analyze(f.lstrip().rstrip(), index=i)
            for i, f in enumerate(self.formulae)
        ]

    def exec(self, strict: bool = False, **kwargs) -> typing.Self:
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


DefaultISPL = ISPL(...)
