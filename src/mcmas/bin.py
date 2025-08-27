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
    from mcmas import ISPL, Agent, Environment, symbols  # noqa

    ispl = symbols
    fname = None
    ns = dict(**locals())
    ns.pop("kwargs")
    ns.update(**kwargs)
    return ns


@click.command()
@click.option("-j", "--json", is_flag=True, help="Load MCMAS spec from json file")
@click.option("-i", "--ispl", is_flag=True, help="Load MCMAS spec from the given ISPL")
@click.option("-r", "--repl", is_flag=True, help="Start a REPL with this context")
@click.option("-c", "--command", default="", help="Command to execute")
@click.option("-s", "--sim", is_flag=True, help="spec after loading one")
@click.option("-a", "--analyze", is_flag=True, help="analyze spec after loading one")
@click.option("-p", "--python", is_flag=True, help="Load spec from python")
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
    from mcmas import models

    witness = witness or counter_example
    sim = any([sim, witness])
    PYDANTIC_MODELS = ["ISPL", "Simulation"]
    path = fname and Path(fname)
    if schema and fname:
        schema = schema and fname
        fname = None
        assert schema in PYDANTIC_MODELS
        mdl = getattr(models, schema)
        print(json_module.dumps(mdl.model_json_schema(), indent=2))
        raise SystemExit(0)

    if list_pydantic_models:
        # raise NotImplementedError(f"{PYDANTIC_MODELS}")
        print(json_module.dumps(PYDANTIC_MODELS, indent=2))
        raise SystemExit(0)

    if path and not path.exists():
        LOGGER.critical(f"specified file not found: {fname}")
        raise SystemExit(1)

    ns = repl_ns(command=command, __file__=fname)

    exclude = []
    if not verbose:
        exclude += ["text"]
    if fname:
        if fname.endswith(".ispl"):
            ispl = True
            LOGGER.warning("forced ispl from fname")
        if fname.endswith(".py"):
            python = True
            LOGGER.warning("forced python from fname")
        if fname.endswith(".json"):
            json = True
            LOGGER.warning("forced json from fname")
        with open(str(path)) as fhandle:
            fmodel = {}
            if ispl:
                # fmodel = parser.parse(fhandle.read())
                fmodel.update({"file": str(path), "text": fhandle.read()})
                model = ISPL.load_from_ispl_file(**fmodel)
            elif json:
                model = ISPL.load_from_json_file(str(path))
                fmodel.update(
                    {
                        "file": str(path),
                        "model": model,
                    }
                )
            elif python:

                assert all([fname, os.path.exists(fname)])
                LOGGER.critical([k for k in ns])
                with open(fname) as fhandle:
                    exec(fhandle.read(), ns)
                model = None
                spec_names = ["__spec__", "__specification__"]
                for x in spec_names:
                    if x in ns:
                        model = ns[x]
                        break
                err = f"no spec-name like {spec_names} were found in {list(ns.keys())}"
                assert model is not None, err
                fmodel.update(
                    {
                        "file": str(path),
                        "model": model,
                    }
                )
            else:
                LOGGER.warning(
                    "must pass one of --python --json or --ispl to get a model."
                )
                model = None
        ns["__fmodel__"] = fmodel
        ns["spec"] = ns["__specification__"] = model
    else:
        model, fmodel = None, None

    if analyze:
        LOGGER.info("analyzing ..")
        analysis = ns["analysis"] = model.model_dump_analysis()
        print(
            analysis.model_dump_json(
                # exclude=exclude,
                # exclude_none=True,
                indent=2
            )
        )

    if validate:
        LOGGER.info("validating ..")
        LOGGER.warning(model.advice)
        out = model.spec_validate()
        print(json_module.dumps(out, indent=2))
        LOGGER.warning(out)
        raise SystemExit(0 if out["validates"] else 1)
    if sim and not fmodel:
        LOGGER.info("requested --sim but no way to create a specification!")
    if fmodel and sim:
        verbose and LOGGER.info(f"Running simulation for {fname} (witnesses={witness})")
        sim_out = engine(output_format="model", witness=witness, **fmodel)
        metadata = {
            **sim_out.metadata.model_dump(),
            **model.metadata.model_dump(),
        }
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
            ns["sim"] = ns["__simulation__"] = models.Simulation()
            LOGGER.warning("No simulation requiested with --sim")
            LOGGER.warning("Both `sim` and `__simulation__` will be null!")
        elif python and model:
            print(model.model_dump_source())
            LOGGER.warning(f"Converted {fname} to ISPL")
        elif json and model:
            print(model.model_dump_source())
            json and LOGGER.info(f"Converted {fname} to ISPL")
        elif ispl and model:
            print(model.model_dump_json(exclude=exclude, exclude_none=True, indent=2))
            ispl and LOGGER.warning(f"Converted {fname} to JSON")
        warn = "No simulation requested, try passing --sim to run spec"
        # not any([command, analyze]) or
        LOGGER.warning(warn)

    if command:
        exec(command, ns)
    if repl:
        return util.repl(command=ns.pop("command", None), **ns)
