"""
mcmas.util: for logging, repl-helpers, model-validators, etc.
"""

import contextlib
import gc
import inspect
import os
import re
import sys
import typing
from typing import Any, get_type_hints

import pydantic

from . import lme  # noqa
from .lme import get_logger  # noqa

OptionalAny = typing.Optional[typing.Any]

LOGGER = lme.get_logger(__name__)


def repl(fname=None, command=None, **ns):
    """
    Drop to a REPL, optionally loading a model into the context,
    optionally executing the model.
    """
    LOGGER.warning("REPL // namespace: ")
    for k, v in sorted(ns.items()):
        LOGGER.warning(f"  {k} {type(v)}")
    try:
        import IPython  # noqa
    except (ImportError,) as exc:
        LOGGER.critical(str(exc))
        LOGGER.critical("pip install ")
    # setup builtins for the repl namespace
    from mcmas import engine  # noqa
    from mcmas import ISPL, Agent, Environment  # noqa

    if fname:
        assert os.path.exists(fname)
        ns["__file__"] = fname
    else:
        LOGGER.warning("no file to load.")
    if command:
        LOGGER.info(f"// BEGIN command: {command}")
        exec(command, ns)
        LOGGER.info(f"// END command: {command}")
    else:
        LOGGER.info("no command given, starting interactive mode")
        IPython.embed(confirm_exit=False, user_ns=ns)  # noqa


def normalize_stderr_stdout(text: str) -> typing.List[str]:
    """
    Normalize the raw output from the mcmas engine.
    """
    if text is None:
        return None
    if not text:
        return []
    if isinstance(text, (list,)):
        return text
    text = text.split(
        "\n************************************************************************\n\n"
    )
    if len(text) >= 2:
        return [s for s in text[1].split("\n") if s.strip()]
    if len(text) == 1:
        return [text[0]]
    else:
        raise Exception("text empty")


class classproperty:
    """
    Like `@property`, but for classes.
    """

    def __init__(self, fxn):
        self.fxn = fxn
        self.__doc__ = fxn.__doc__

    def __get__(self, obj, owner) -> OptionalAny:  # noqa
        return self.fxn(owner)


class classproperty_cached(classproperty):
    """
    Like `classproperty`, but cached.
    """

    CLASSPROP_CACHES = {}

    def __get__(self, obj, owner) -> OptionalAny:  # noqa
        result = self.__class__.CLASSPROP_CACHES.get(self.fxn, self.fxn(owner))
        self.__class__.CLASSPROP_CACHES[self.fxn] = result
        return self.__class__.CLASSPROP_CACHES[self.fxn]


def find_instances(cls) -> typing.List:
    """
    Finds all instances of a class and its subclasses in memory.
    """
    instances = []
    for obj in gc.get_objects():
        if isinstance(obj, cls):
            instances.append(obj)
    return instances


@pydantic.validate_call
def dict2ispl(data: dict) -> str:
    """
    Python dictionary --> pydantic ISPL --> ISPL source.
    """
    from mcmas import rendering
    from mcmas.ispl import ISPL

    model = ISPL(**data)
    rendering.get_jinja_env()
    template = rendering.get_template("ISPL.j2")
    return template.render(model=model)


@pydantic.validate_call
def accepts_posargs(func: typing.Callable) -> bool:
    """
    Check if a function accepts positional arguments.
    """
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        if param.kind in (param.POSITIONAL_ONLY,):
            return True
    return False


def fxn_sig(func: typing.Callable) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    """
    Return string version of functiuon signature.
    """
    sig = inspect.signature(func)
    src = inspect.getsource(func)
    pattern = r"(def.*?):\s*\n\s+"
    match = re.search(pattern, src, re.DOTALL)
    if match:
        header = match.group(1) + ":"
    else:
        # Fallback: if no indented content found, just match until ':'
        pattern = r"(def.*?):"
        match = re.search(pattern, src, re.DOTALL)
        header = match.group(1) + ":" if match else src.strip()
    # header = src[: src.find(":")]
    anno = sig.return_annotation
    anno = anno.__name__ if anno != inspect._empty else "typing.Any"
    return f"{header} -> {anno}"


def fxn_sig_as_dict(func) -> typing.Dict[str, typing.Any]:
    """
    Extract function signature as a { param_name: type }
    """
    sig = inspect.signature(func)
    signature_dict = {}
    type_hints = {}
    try:
        type_hints = get_type_hints(func)
    except contextlib.suppress(NameError, AttributeError, TypeError):
        # get_type_hints can fail, so we'll use direct annotations instead
        pass
    for param_name, param in sig.parameters.items():
        # Use type hint if available, otherwise use annotation from parameter
        if param_name in type_hints:
            signature_dict[param_name] = type_hints[param_name]
        elif param.annotation != inspect.Parameter.empty:
            signature_dict[param_name] = param.annotation
        # Here we'll use Any to indicate no specific type was provided
        else:
            signature_dict[param_name] = Any
    return signature_dict


def fxn_sig_as_ispl_types(func: typing.Callable):
    """
    Converts python type-signatures to something closer to ISPL.
    """
    sig = fxn_sig_as_dict(func)
    vars = {}
    for k, v in sig.items():
        conversion = None
        if v in (bool,):
            conversion = "boolean"
        elif v in (int,):
            _type = f"0..{sys.maxsize}"
            LOGGER.warning(
                f"detected that {k} is an unbounded integer, setting type={_type}"
            )
            conversion = _type
        else:
            LOGGER.warning(f"could not convert type to ISPL: {v}")
            conversion = v
        vars[k] = conversion
    return vars


# FIXME: real object/class
fxn_sig.as_dict = fxn_sig_as_dict
fxn_sig.as_ispl_types = fxn_sig_as_ispl_types
