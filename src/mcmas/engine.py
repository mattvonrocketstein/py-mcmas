"""
mcmas.engine.

The main wrapper for the MCMAS engine. Core functionality to run
the CLI inside a docker container, then parse the output to
return JSON.  See also
"""

import os
import pathlib
import re
import tempfile
import time
from pathlib import Path, PosixPath
from typing import Dict, Union

import docker
import pydantic

from mcmas import models, util

LOGGER = util.get_logger(__name__)
DEFAULT_IMG = "ghcr.io/mattvonrocketstein/mcmas:v1.3.0"
DEFAULT_V = os.environ.get("MCMAS_VERBOSITY", "3")
MCMAS_DEBUG = os.environ.get("MCMAS_DEBUG", "0")
MCMAS_DEBUG = MCMAS_DEBUG == "1"
MCMAS_VERBOSE = os.environ.get("MCMAS_VERBOSE", "0")
MCMAS_VERBOSE = MCMAS_VERBOSE != "0"
docker_client = docker.from_env()


def relpath(fname):
    try:
        str(Path(fname).relative_to(os.getcwd()))
    except ValueError:
        return fname


@pydantic.validate_call
def parse_engine_output(text: str, file=None, exit_code=None) -> models.Simulation:
    formula_lines = re.findall(r"^\s*Formula number.*$", text, re.MULTILINE)
    true_props = [
        x[x.find(": ") + 2 : -len(", is TRUE in the model")]
        for x in formula_lines
        if x.endswith("is TRUE in the model")
    ]
    false_props = [
        x[x.find(": ") + 2 : -len(", is FALSE in the model")]
        for x in formula_lines
        if x.endswith("is FALSE in the model")
    ]
    match = re.search(r"BDD memory in use = (\d+)", text)
    bdd_memory = int(match.group(1)) if match else 0

    match = re.search(r"There is no deadlock state in the model!", text)
    deadlock = not bool(match)

    match = re.search(r"execution time = ([\d.]+)", text)
    execution_time = float(match.group(1)) if match else None

    match = re.search(r"It took ([\d.]+) seconds to generate state space.", text)
    gen_state_space = float(match.group(1)) if match else None

    match = re.search(r"It took ([\d.]+) seconds to encode transition relation.", text)
    enc_time = float(match.group(1)) if match else None
    match = re.search(r"number of reachable states = ([\d]+)", text)
    reachable_states = int(match.group(1)) if match else None

    match = re.search(r" has been parsed successfully.\n", text)
    parsed = bool(match)  # True if match else False

    match = re.search(r"(.*) has error\(s\)[.]", text)
    parsed = False if match else parsed

    model_validates = parsed and (len(formula_lines) == len(true_props))
    error = exit_code != 0
    metadata = models.Simulation.Metadata(
        parsed=parsed,
        file=file,
        exit_code=exit_code,
        validates=parsed and model_validates,
        deadlock=deadlock if parsed else None,
    )
    data = {"error": error and text, "metadata": metadata}
    if not error:
        metadata = metadata.model_copy(
            update={
                "timing": {
                    "generate_time": gen_state_space,
                    "execution_time": execution_time,
                    "encoding_time": enc_time,
                },
            }
        )
        data.update(
            metadata=metadata,
            text=text if not error else None,
            facts={"true": true_props, "false": false_props},
            state_space={
                "reachable_states": reachable_states,
                "memory": {"bdd": bdd_memory},
            },
        )
    out = models.Simulation(**data)
    return out


@pydantic.validate_call
def get_help() -> str:
    return (
        docker_client.containers.run(
            DEFAULT_IMG,
            stdout=True,
            stderr=True,
            detach=True,
        )
        .logs()
        .decode("utf-8")
    )


@pydantic.validate_call
def show_help() -> None:
    """
    
    """
    print(get_help())


@pydantic.validate_call
def mcmas(
    img: str = DEFAULT_IMG,
    cmd: str = "",
    # force: bool = False,
    output_format: str = "data",
    fname: Union[str, PosixPath] = "",
    model=None,
    # raw: bool = False,
    strict: bool = False,
    validate_only: bool = False,
) -> Union[Dict, str, bool]:
    """
    Proxies an invocation of the mcmas engine through to the
    containerized CLI.
    """
    LOGGER.debug(f"img={img} fname={fname} model={model}")
    cmd = f"-v {DEFAULT_V} " + cmd if "-v" not in cmd else cmd
    cmd = "-a " + cmd if "-a " not in cmd else cmd
    cmd = "-k " + cmd if "-k " not in cmd else cmd
    validate_only = validate_only or "--validate-only" in cmd
    if "--strict" in cmd:
        strict = True
        cmd = cmd.replace("--strict", "")
    if validate_only:
        LOGGER.info("validating..")
        cmd = f"-v {DEFAULT_V} -s"
    else:
        LOGGER.info(f"cmd={cmd}")
    assert fname or model
    volumes = []
    if fname:
        LOGGER.debug(f"fname={fname}")
        abspath = pathlib.Path(fname).absolute()
        command = f"{cmd} {abspath}"
        if abspath.exists():
            dirname = abspath.parent
            volumes = [f"{dirname}:{dirname}"]
            LOGGER.debug(f"file on host.. adding volume {volumes}")
        else:
            err = f"{abspath} does not exist on host"
            LOGGER.critical(err)
            raise SystemExit(1)
    else:
        raise Exception("not implemented yet")
    LOGGER.debug(f"command={command}")
    text = None
    exit_code = -1
    try:
        container = docker_client.containers.run(
            img,
            entrypoint="mcmas",
            command=command,
            volumes=volumes,
            stdout=True,
            stderr=True,
            detach=True,
        )
        container.wait()
        container.reload()
        while container.status != "exited":
            time.sleep(0.1)
            container.reload()
        text = container.logs(stdout=True, stderr=True).decode()
        exit_code = container.attrs["State"]["ExitCode"]
    except (docker.errors.ContainerError,) as exc:
        LOGGER.debug(f"\n stderr={exc.stderr.decode('utf-8')}")
        if strict:
            raise
        else:
            LOGGER.critical("failed ")
            text = str(exc)  # .stdout.decode("utf-8") + exc.stderr.decode("utf-8")
    if any([exit_code != 0, validate_only]):
        LOGGER.critical(f"exit_code={exit_code} validate_only={validate_only}")
        if validate_only:
            pattern = r"Global syntax checking.*?(?:\n1)*\nDone"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return True
            else:
                LOGGER.critical(f"Global syntax checking failed: {match}")
                LOGGER.critical(f"Cannot validate {fname}")
                return False
        try:
            sim = parse_engine_output(text, file=fname, exit_code=exit_code)
        except (Exception,) as exc:
            LOGGER.critical(text)
            LOGGER.critical(exc)
            raise
    elif exit_code != 0:
        LOGGER.critical(f"exit_code={exit_code}")
        if strict:
            raise SystemExit(1)
        else:
            tmp = parse_engine_output(
                text, file=fname, exit_code=exit_code
            ).model_dump()
            tmp.pop("error"), tmp.pop("text"), tmp.pop("exit_code")
            sim = models.Simulation(
                text=None,
                metadata=tmp.metadata.model_copy(update={"exit_code": exit_code}),
                error=text,
                **tmp,
            )
    else:
        LOGGER.critical(f"requested sim, not validation, exit_code={exit_code}")
        sim = parse_engine_output(text, file=relpath(fname), exit_code=exit_code)
        if model:
            model = model.model_copy(update={"metadata": sim.metadata})

        # .model_dump()
    if not text:
        err = "nothing returned from engine"
        LOGGER.critical(err)
        raise Exception(container)

    if output_format in ["data"]:
        return sim.model_dump()
    elif output_format in ["model"]:
        # raise Exception(sim.metadata.model_dump_json())
        return sim
    elif output_format in ["json"]:
        return sim.model_dump_json(exclude_none=True, indent=2)
    elif output_format in ["text"]:
        return "\n".join(sim.error or sim.text)
    else:
        raise Exception(f"unrecognized output format {output_format}")


@pydantic.validate_call
def validator(**kwargs) -> bool:
    return engine(validate_only=True, **kwargs)


@pydantic.validate_call
def engine(
    fname: Union[str, PosixPath] = "",
    text: str = "",
    model=None,
    data: dict = {},
    file: Union[str, PosixPath] = "",
    **kwargs,
) -> Union[Dict, str]:
    """
    Runs the engine on either a filename, a block of ISPL text,
    or an ISPL- Specification object.
    """
    if text:
        LOGGER.debug("------------")
        LOGGER.debug(text)
        LOGGER.debug("------------")
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, dir=".") as temp_file:
            temp_file.write(text)
            temp_file.flush()
            result = mcmas(fname=temp_file.name, **kwargs)
            # raise Exception(result.metadata)
            return result
    elif fname:
        return mcmas(fname=fname, **kwargs)
    elif model:
        return engine(data=model.model_dump(), **kwargs)
    elif data:
        return engine(text=util.dict2ispl(data), **kwargs)
    else:
        err = "No input, expected one of {text|model|data}"
        raise Exception(err)


mcmas.validate = validator
engine.validate = validator
engine.show_help = show_help

__all__ = [engine, validator]
