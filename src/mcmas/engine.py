"""
mcmas.engine.

The main wrapper for the MCMAS engine. Core functionality to run
the CLI inside a docker container, then parse the output to
return JSON.  See also
"""

import atexit
import os
import pathlib
import re
import tempfile
import time
from pathlib import Path, PosixPath
from typing import Dict, Union

import docker
import pydantic

from mcmas import ispl, parser, sim, util

LOGGER = util.get_logger(__name__)
DEFAULT_IMG = "ghcr.io/mattvonrocketstein/mcmas:v1.3.0"
DEFAULT_V = os.environ.get("MCMAS_VERBOSITY", "3")
MCMAS_DEBUG = os.environ.get("MCMAS_DEBUG", "0")
MCMAS_DEBUG = MCMAS_DEBUG == "1"
MCMAS_VERBOSE = os.environ.get("MCMAS_VERBOSE", "0")
MCMAS_VERBOSE = MCMAS_VERBOSE != "0"

try:
    docker_client = docker.from_env()
except (docker.errors.DockerException,) as exc:
    LOGGER.critical(f"ERROR: could not create docker client: {exc}")
    LOGGER.critical("Simulations will not be able to run!")
    docker_client = None


def relpath(fname):
    try:
        return str(Path(fname).relative_to(os.getcwd()))
    except ValueError:
        return fname


@pydantic.validate_call
def parse_engine_output(text: str, file=None, exit_code=None) -> sim.Simulation:
    """
    Parses raw engine output to Simulation.
    """
    LOGGER.critical(f"file={file} exit_code={exit_code}")

    formula_lines = re.findall(r"^\s*Formula number.*$", text, re.MULTILINE)
    true_props = [
        x[x.find(": ") + 2 : -len(", is TRUE in the model")].replace(" && ", " and ")
        for x in formula_lines
        if x.endswith("is TRUE in the model")
    ]
    false_props = [
        x[x.find(": ") + 2 : -len(", is FALSE in the model")].replace(" && ", " and ")
        for x in formula_lines
        if x.endswith("is FALSE in the model")
    ]

    # trim the extra parens output includes
    # so that these *exactly* match input formulae
    # true_props=[x.lstrip().rstrip()[1:-1] for x in true_props]
    # false_props=[x.lstrip().rstrip()[1:-1] for x in false_props]
    # true_props = [x.replace(' && ',' and ') for x in true_props]

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

    spec_validates = parsed and (len(formula_lines) == len(true_props))
    error = exit_code not in [0, 139]
    error and LOGGER.critical(f"error {error}")
    metadata = sim.Simulation.Metadata(
        parsed=parsed,
        file=file,
        exit_code=exit_code,
        validates=parsed and spec_validates,
        deadlock=deadlock if parsed else None,
    )
    data = {"error": error and text, "metadata": metadata}
    if not error:
        metadata = metadata.model_copy(
            update={
                "file": relpath(file),
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
    out = sim.Simulation(**data)
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
    witness: bool = False,
    model=None,
    # raw: bool = False,
    strict: bool = False,
    validate_only: bool = False,
) -> Union[Dict, str, bool]:
    """
    Proxies an invocation of the mcmas engine through to the
    containerized CLI.
    """

    def create_witness_folder(tmpd, img):
        container = docker_client.containers.run(
            img,
            entrypoint="bash",
            command=f"-x -c 'mkdir {tmpd}'",
            working_dir="/workspace",
            volumes=volumes,
            stdout=True,
            stderr=True,
            detach=True,
        )
        container.wait()
        container.reload()
        exit_code = container.attrs["State"]["ExitCode"]
        assert exit_code == 0, "failed creating {tmpd} from container {img}!"

    def clean_witness_folder(tmpd, img):
        """
        Registered with atexit module.

        Removes the .info and .dot files created by `mcmas`,
        using the same container to avoid permissions issues
        """
        LOGGER.info("cleaning folder for witnesses")
        docker_client.containers.run(
            img,
            volumes=volumes,
            entrypoint="bash",
            working_dir="/workspace",
            stdout=True,
            stderr=True,
            command=f"-c 'mv {tmpd} /tmp'",
        )

    LOGGER.debug(f"running mcmas with img={img} fname={fname} model={model}")
    cmd = f"-v {DEFAULT_V} " + cmd if "-v" not in cmd else cmd
    cmd = "-a " + cmd if "-a " not in cmd else cmd
    cmd = "-k " + cmd if "-k " not in cmd else cmd
    volumes = [
        f"{os.getcwd()}:/workspace",
    ]
    if witness:
        tmpd = f".tmp.mcmas_{time.time()}"
        cmd = "-c 2 " + cmd if "-c " not in cmd else cmd
        cmd = f"-p ./{tmpd} " + cmd if "-p " not in cmd else cmd
        LOGGER.debug(f"paving tmpdir for witnesses: {tmpd}")
        create_witness_folder(tmpd, img)
        LOGGER.debug("registering cleanup at exit")
        atexit.register(clean_witness_folder, tmpd, img)

    validate_only = validate_only or "--validate-only" in cmd
    if "--strict" in cmd:
        strict = True
        cmd = cmd.replace("--strict", "")
    if validate_only:
        LOGGER.info(f"Requested validation (strict={strict})")
        cmd = f"-v {DEFAULT_V} -s"
    else:
        LOGGER.info(f"cmd={cmd}")
    assert fname or model

    if fname and not str(fname).startswith("<<"):
        LOGGER.debug(f"fname={fname}")
        abspath = pathlib.Path(fname).absolute()
        command = f"{cmd} {abspath}"
        if abspath.exists():
            dirname = abspath.parent
            volumes += [f"{dirname}:{dirname}"]
            LOGGER.debug(f"file on host @{dirname}.. adding volume {volumes}")
        else:
            err = f"{abspath} does not exist on host"
            LOGGER.critical(err)
            raise SystemExit(1)
    else:
        raise NotImplementedError("expected an argument for filename")
    LOGGER.debug(f"command={command}")
    text = None
    exit_code = -1
    try:
        container = docker_client.containers.run(
            img,
            entrypoint="mcmas",
            command=command,
            working_dir="/workspace",
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
        err = f"failed trying to use the container: stderr=\n\n{exc.stderr.decode('utf-8')}"
        LOGGER.debug(err)
        if strict:
            raise
        else:
            text = str(exc)
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
            sim = sim.Simulation(
                text=None,
                metadata=tmp.metadata.model_copy(update={"exit_code": exit_code}),
                error=text,
                **tmp,
            )
    else:
        LOGGER.critical(
            f"requested sim, not validation, file={fname} exit_code={exit_code}"
        )
        sim = parse_engine_output(text, file=fname, exit_code=exit_code)
        if model:
            model = model.model_copy(update={"metadata": sim.metadata})
    if not text:
        err = "nothing returned from engine"
        LOGGER.critical(err)
        raise Exception(container)

    if witness and sim:
        sim = load_witnesses(tmpd=tmpd, fname=fname, model=model, sim=sim)

    if output_format in ["data"]:
        return sim.model_dump()
    elif output_format in ["model"]:
        return sim
    elif output_format in ["json"]:
        return sim.model_dump_json(
            # exclude_none=True,
            indent=2
        )
    elif output_format in ["text"]:
        return "\n".join(sim.error or sim.text)
    else:
        raise Exception(f"unrecognized output format {output_format}")


def load_witnesses(tmpd=None, model=None, fname: Union[str, PosixPath] = "", sim=None):
    """
    
    """
    LOGGER.warning("loading witnesses..")
    witnesses = dict()
    for wfile in Path(tmpd).iterdir():
        if str(wfile).endswith(".info"):
            with open(wfile) as fhandle:
                content = fhandle.read()
                witnesses[wfile.stem] = parser.extract_witnesses(content, fname=wfile)
    ordered = sorted([k for k in witnesses])
    tmp = {}
    for k in ordered:
        tmp[k] = witnesses[k]
    witnesses = {}

    model = model or ispl.ISPL.load_from_ispl_file(file=str(fname))
    forms = model.formulae
    for i, fname_stem in enumerate(tmp.keys()):
        witnesses[forms[i]] = tmp[fname_stem]
    if len(forms) > len(witnesses):
        LOGGER.warning("could not find witnesses for some formulae.")
        missing = []
        present = []
        for fname_stem in tmp:
            match = re.search(r"(\d+)$", fname_stem)
            i = int(match.group(1))
            present.append(i)
        missing = [forms[i] for i in [x for x in range(len(tmp)) if x not in present]]
        for m in missing:
            LOGGER.warning(f" - {m}")
            witnesses[m] = []
        sim = sim.model_copy(update=dict(witnesses=witnesses))
    sim = sim.model_copy(update=dict(witnesses=witnesses))
    LOGGER.critical(
        f"found witnesses for {len(witnesses)} of {len(model.formulae)} formulae"
    )
    return sim


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
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".ispl", delete=True, dir="."
        ) as temp_file:
            temp_file.write(text)
            temp_file.flush()
            result = mcmas(fname=temp_file.name, **kwargs)
            # raise Exception(result.metadata)
            return result
    # elif file and file=='/dev/stdin':
    #     import sys
    #     raise Exception(sys.stdin.read())
    #     return engine(text=sys.stdin.read())
    elif model:
        return engine(data=model.model_dump(), **kwargs)
    elif fname or file:
        return mcmas(fname=fname or file, **kwargs)
    elif data:
        return engine(text=util.dict2ispl(data), **kwargs)
    else:
        err = "No input, expected one of {text|model|data}"
        raise Exception(err + f"\n{[fname,text,model,data,file]}")


mcmas.validate = validator
engine.validate = validator
engine.show_help = show_help

__all__ = [engine, validator]
