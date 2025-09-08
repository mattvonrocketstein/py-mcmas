"""
mcmas.bin:

Entrypoints for all scripts, as installed by setup.cfg.
"""

import json as json_module
import os
import sys
import typing
from pathlib import Path

import click
from pydantic import validate_call

from mcmas import engine, util
from mcmas.ispl import ISPL
from mcmas.sim import Simulation
from mcmas.util.lme import get_logger

LOGGER = get_logger(__name__)


def mcmas():
    """
    Wrapper for the MCMAS Engine.
    """
    special = ["--json"]
    args = [x for x in sys.argv if x not in special]
    args.pop(0)
    fname = ""
    if len(args) >= 1 and not args[-1].startswith("-"):
        fname = args[-1]
        args = args[:-1]
    data = {"cmd": " ".join(args), "fname": fname}
    LOGGER.debug(f"{data}")
    force_json = "--json" in sys.argv
    show_help = (not args and not fname) or "-h" in args or "--help" in args
    if show_help:
        return engine.show_help()
    output_format = "json" if force_json else "text"
    out = engine(output_format=output_format, **data)
    print(out)


entry = mcmas


@validate_call
def repl_ns(**kwargs) -> typing.Dict:
    """
    Default namespace that is used with the interactive REPL.
    """
    from mcmas import logic  # noqa
    from mcmas import ISPL, Agent, DefaultAgent, Environment, symbols  # noqa

    ispl = symbols
    fname = None
    Equal = Eq = logic.Eq
    If, And = logic.If, logic.And
    true = symbols.true
    false = symbols.false
    ns = dict(**locals())
    ns.pop("kwargs")
    ns.update(**kwargs)
    return ns


@click.command()
@click.option(
    "-j",
    "--json",
    is_flag=True,
    help="Load ISPL spec from JSON file.  (Implied if filename ends in .json)",
)
@click.option(
    "-i",
    "--ispl",
    is_flag=True,
    help="Load ISPL spec from the given ISPL  (Implied if filename ends in .ispl)",
)
@click.option("-r", "--repl", is_flag=True, help="Start a REPL with this context")
@click.option("-c", "--command", default="", help="Command to execute")
@click.option(
    "-s",
    "--sim",
    is_flag=True,
    help="Simulate the specification after loading one.  Returns JSON",
)
@click.option(
    "-a",
    "--analyze",
    is_flag=True,
    help="Analyze specification after loading one.  (Cannot be used with --sim)",
)
@click.option(
    "-p",
    "--python",
    is_flag=True,
    help="Load ISPL specification from python.  (Implied if filename ends in .py)",
)
@click.option(
    "-W",
    "--witness",
    is_flag=True,
    help=r"Generate witnesses (implies --sim).\Returns counter-examples only (witnesses for false formulae)",
)
@click.option(
    "-w",
    "--counter-example",
    is_flag=True,
    help="Generate ALL witnesses (implies --sim)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Generate ALL witnesses (implies --sim)",
)
@click.option(
    "--list-pydantic-models", is_flag=True, help="List available pydantic models"
)
@click.option("--schema", is_flag=True, help="Return JSON schema for named model")
@click.option("--validate", is_flag=True, help="Validate specification")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Do not include raw output from engine (used with --sim)",
)
@click.argument("fname", default=None, required=False)
@validate_call
def ispl_main(
    fname: typing.Union[str, None] = None,
    analyze: bool = False,
    schema: bool = False,
    list_pydantic_models: bool = False,
    repl: bool = False,
    verbose: bool = True,
    quiet: bool = False,
    json: bool = False,
    witness: bool = False,
    counter_example: bool = False,
    sim: bool = False,
    python: bool = False,
    ispl: bool = False,
    validate: bool = False,
    command="",
) -> None:
    """
    Helper for interacting with ISPL files.
    """

    def find_spec(ns, strict=False):
        model = None
        spec_names = ["__spec__", "__specification__"]
        for x in spec_names:
            if x in ns:
                model = ns[x]
                if not quiet:
                    LOGGER.info(f"extracted specification at `{x}`:")
                    LOGGER.info(f"{model}")
                return model
        if strict:
            err = f"no spec-name like {spec_names} were found in {list(ns.keys())}"
            assert model is not None, err
        # raise Exception(fmodel)

    witness = witness or counter_example
    sim = any([sim, witness])
    PYDANTIC_MODELS = ["ISPL", "Simulation"]
    path = fname and Path(fname)
    if schema and fname:
        schema = schema and fname
        fname = None
        assert schema in PYDANTIC_MODELS
        mdl = ISPL if schema == "ISPL" else Simulation
        print(json_module.dumps(mdl.model_json_schema(), indent=2))
        raise SystemExit(0)

    if list_pydantic_models:
        print(json_module.dumps(PYDANTIC_MODELS, indent=2))
        raise SystemExit(0)

    if path and not path.exists():
        LOGGER.critical(f"specified file not found: {fname}")
        raise SystemExit(1)

    # Namespace that will be used for REPLs,
    # or the execution context of python files that are invoked
    ns = repl_ns(command=command, __file__=fname)

    fmodel = {}
    exclude = []
    if not verbose:
        exclude += ["text"]

    if fname:
        if fname.endswith(".ispl"):
            ispl = True
            LOGGER.info(f"{fname} .. forcing ISPL")
        elif fname.endswith(".py"):
            python = True
            LOGGER.info(f"{fname} .. forcing python")
        elif fname.endswith(".json"):
            json = True
            LOGGER.info(f"{fname} .. forcing JSON")
        from mcmas import ISPL

        with open(str(path)) as fhandle:
            fmodel.update({"file": str(path)})
            if ispl:
                model = ISPL.load_from_ispl_file(**fmodel)
                fmodel.update(text=fhandle.read())
            elif json:
                model = ISPL.load_from_json_file(str(path))
                fmodel.update(
                    {
                        "model": model,
                    }
                )
            elif python:
                assert all([fname, os.path.exists(fname)]), f"{fname} is missing"
                LOGGER.critical([k for k in ns])
                with open(fname) as fhandle:
                    exec(fhandle.read(), ns)
                model = find_spec(ns)
                model.metadata.file = str(fname)
                fmodel = {
                    "model": model,
                }
            else:
                LOGGER.warning(
                    "must pass one of --python --json or --ispl to get a model."
                )
                model = None
        ns["__fmodel__"] = fmodel
        ns["spec"] = ns["__specification__"] = model
    else:
        model, fmodel = None, None
        if command:
            LOGGER.warning("No file to load specification from!")
            LOGGER.warning("Checking if command provides spec..")
            model = eval(command, ns)
            from mcmas import ISPL

            if isinstance(model, (ISPL,)):
                LOGGER.warning(f"Found spec: {model}")
            else:
                LOGGER.warning(f"Command is not spec, got {type(model)}")
            fmodel = dict(file="<<stream>>", model=model)

    if analyze:
        LOGGER.info(f"analyzing spec: {model.title}")
        analysis = ns["analysis"] = model.analysis
        print(
            analysis.model_dump_json(
                # exclude=exclude,
                exclude_none=True,
                exclude_unset=True,
                indent=2,
            )
        )

    if validate:
        LOGGER.info(f"validating .. {fname}")
        LOGGER.warning(model.advice)
        out = model.spec_validate()
        print(json_module.dumps(out, indent=2))
        LOGGER.warning(out)
        raise SystemExit(0 if out["validates"] else 1)

    if sim and not fmodel:
        LOGGER.warning("Requested --sim but no way to create a specification!")

    if fmodel and sim:
        verbose and LOGGER.info(f"Running simulation for {fname} (witnesses={witness})")
        sim_out = engine(output_format="model", witness=witness, **fmodel)
        metadata = sim_out.Metadata(
            **{
                **model.metadata.model_dump(),
                **sim_out.metadata.model_dump(),
            }
        )
        # raise Exception(sim_out.witnesses)
        sim_out = sim_out.model_copy(update={"metadata": metadata, "spec": model})
        if counter_example:
            if not sim_out.facts["false"]:
                LOGGER.critical(
                    "counter-examples were requested, but there are no false formulae!"
                )
                LOGGER.critical(
                    "Pass -W instead for ALL witnesses, including the ones for formulae that are true."
                )
                # sim_out = sim_out.model_copy(update=dict(witnesses={}))
            # raise Exception(sim_out.counter_examples)
            # sim_out=sim_out.model_copy(update=dict(witnesses = sim_out.counter_examples))
            # sim_out=sim_out.model_copy(update=dict(witnesses = dict([k,v] for k,v in ssim_outim.witnesses.items() if k in sim_out.facts.false)))
            # raise Exception(sim_out.counter_examples)
            else:
                sim_out = sim_out.model_copy(
                    update=dict(witnesses=sim_out.counter_examples)
                )
            # LOGGER.warning(f'witnesses {sim.witnesses}')
            # raise Exception(sim.witnesses)
        print(
            sim_out.model_dump_json(
                exclude=exclude,
                exclude_none=True,
                indent=2,
            )
        )
        verbose and LOGGER.info("Done running simulation. ")
        ns["sim"] = ns["__simulation__"] = sim_out

    if not any([sim, validate, analyze]):
        if repl:
            ns["sim"] = ns["__simulation__"] = Simulation()
            LOGGER.warning("No simulation requested with --sim")
            LOGGER.warning("Both `sim` and `__simulation__` will be null!")
        elif python and model:
            print(model.model_dump_source())
            LOGGER.warning(f"Converted `{fname or command}` to ISPL")
        elif json and model:
            print(model.model_dump_source())
            json and LOGGER.info(f"Converted `{fname or command}` to ISPL")
        elif ispl and model:
            print(model.model_dump_json(exclude=exclude, exclude_none=True, indent=2))
            ispl and LOGGER.warning(f"Converted `{fname or command}` to JSON")

        # warn = f"No type hints, try passing --sim to run spec"
        # # not any([command, analyze]) or
        # LOGGER.warning(warn)

    if command:
        exec(command, ns)
    if repl:
        return util.repl(command=ns.pop("command", None), **ns)
