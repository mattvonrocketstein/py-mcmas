"""
mcmas.bin: entrypoints for all scripts, as installed by
setup.cfg.
"""

import json as json_module
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


# @click.command()
# # @click.option("--execute", is_flag=True, help="Execute the generated code")
# @click.argument("fname")
# def ispl_to_json(fname, execute=False):
#     """
#     Generates JSON from ISPL source code

#     http://mattvonrocketstein.github.io/py-mcmas/schema
#     """
#     LOGGER.debug(f"{fname}")
#     from mcmas import parser

#     with open(fname) as fhandle:
#         print(parser.parse(fhandle.read()).model_dump_json(indent=2))


# @click.command()
# @click.option("--execute", is_flag=True, help="Execute the generated code")
# @click.argument("fname")
# def ispl_from_json(fname, execute=False) -> None:
#     """
#     Generates ISPL code from JSON

#     http://mattvonrocketstein.github.io/py-mcmas/schema
#     """
#     LOGGER.debug(f"{fname}")
#     model = ISPL.load_from_json_file(fname=fname)
#     assert model
#     # raise Exception(type(data))
#     if not execute:
#         print(model.model_dump_source())
#     else:
#         print(engine(model=model, output_format="json"))
#         # if out:
#         #     print(out)
# json2ispl = ispl_from_json


@validate_call
def repl_ns(**kwargs) -> typing.Dict:
    """
    
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
    "--list-pydantic-models", is_flag=True, help="List available pydantic models"
)
@click.option("--schema", is_flag=True, help="Return JSON schema for named model")
@click.option("--validate", is_flag=True, help="Validate specification")
@click.option(
    "-q",
    "--quiet",
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
    quiet: bool = True,
    json: bool = False,
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

    PYDANTIC_MODELS = ["ISPL", "Simulation"]
    path = fname and Path(fname)
    if schema and fname:
        from mcmas import ispl

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
    if quiet:
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
            if ispl:
                # fmodel = parser.parse(fhandle.read())
                fmodel = {"file": str(path), "text": fhandle.read()}
                model = ISPL.load_from_ispl_file(**fmodel)
            elif json:
                model = ISPL.load_from_json_file(str(path))
                fmodel = {
                    "file": str(path),
                    "model": model,
                }
            elif python:
                import os

                assert all([fname, os.path.exists(fname)])
                LOGGER.critical([k for k in ns.keys()])
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
                fmodel = {
                    "file": str(path),
                    "model": model,
                }
            else:
                LOGGER.warning(
                    "must pass one of --python --json or --ispl to get a model."
                )
                model = None
                fmodel = {}
        ns["__fmodel__"] = fmodel
        ns["spec"] = ns["__specification__"] = model
    else:
        model, fmodel = None, None

    if analyze:
        LOGGER.critical("analyzing ..")
        # LOGGER.warning(f"{model.metadata}")
        analysis = ns["analysis"] = model.model_dump_analysis()
        LOGGER.warning(f"{analysis}")
        # print(analysis.symbols.model_dump_json(indent=2))
        print(analysis.model_dump_json(indent=2))
        # analysis.model_dump_json(indent=2))
        # util.repl(**{**locals(),**globals()})
        # raise SystemExit(0)

    if validate:
        LOGGER.critical("validating ..")
        LOGGER.warning(model.advice)
        out = model.model_validate()
        print(json_module.dumps(out, indent=2))
        LOGGER.warning(out)
        raise SystemExit(0 if out["validates"] else 1)
    if sim and not fmodel:
        LOGGER.critical("requested --sim but no way to create a specification")
    if fmodel and sim:
        quiet or LOGGER.critical(f"running simulation for {fmodel}")
        sim = engine(output_format="model", **fmodel)
        metadata = {
            **sim.metadata.model_dump(),
            **model.metadata.model_dump(),
        }
        sim = sim.model_copy(update={"metadata": metadata})
        quiet or LOGGER.critical(f"done running {fmodel}")
        print(sim.model_dump_json(exclude=exclude, exclude_none=True, indent=2))
        quiet or LOGGER.info("done running simulation. ")
        ns["sim"] = ns["__simulation__"] = sim
        # raise SystemExit(0)

    if not any([sim, validate, analyze]):
        warn = "No simulation requested, try passing --sim to run spec"
        not any([command, analyze]) or LOGGER.warning(warn)
        if repl:
            ns["sim"] = ns["__simulation__"] = models.Simulation()
            LOGGER.warning(
                "NB: `sim` and `__simulation__` will be populated with EmptySim!"
            )
        elif python and model:
            print(model.model_dump_source())
            LOGGER.warning(f"converted {fname} to ISPL")
        elif json and model:
            print(model.model_dump_source())
            json and LOGGER.warning(f"converted {fname} to ISPL")
        elif ispl and model:
            print(model.model_dump_json(exclude=exclude, exclude_none=True, indent=2))
            ispl and LOGGER.warning(f"converted {fname} to JSON")
    if command:
        exec(command, ns)
    if repl:
        return util.repl(command=ns.pop("command", None), **ns)
