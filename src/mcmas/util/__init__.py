"""
mcmas.util: for logging, repl-helpers, model-validators, etc.
"""

import gc
import importlib.util
import inspect
import os
import sys
import typing

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

    def __get__(self, obj, owner) -> OptionalAny:  # noqa
        """
        
        """
        return self.fxn(owner)


class classproperty_cached(classproperty):
    """
    Like `classproperty`, but cached.
    """

    CLASSPROP_CACHES = {}

    def __get__(self, obj, owner) -> OptionalAny:  # noqa
        """
        
        """
        result = self.__class__.CLASSPROP_CACHES.get(self.fxn, self.fxn(owner))
        self.__class__.CLASSPROP_CACHES[self.fxn] = result
        return self.__class__.CLASSPROP_CACHES[self.fxn]


def find_instances(cls):
    """
    Finds all instances of a class and its subclasses in memory.
    """
    instances = []
    for obj in gc.get_objects():
        if isinstance(obj, cls):
            instances.append(obj)
    return instances


def lazy_module(fullname):
    """
    
    """
    try:
        return sys.modules[fullname]
    except KeyError:
        spec = importlib.util.find_spec(fullname)
        module = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)
        # Make module with proper locking and get it inserted into sys.modules.
        loader.exec_module(module)
        return module


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


def fxn_metadata(func) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    """
    
    """
    # sig = inspect.signature(func)
    src = inspect.getsource(func)
    header = src[: src.find(":")]
    result = header
    # result = {}
    # for param_name, param in sig.parameters.items():
    #     param_info = {
    #         'name': param.name,
    #         'kind': param.kind.name,  # POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, etc.
    #         'default': param.default if param.default != inspect.Parameter.empty else None,
    #         'annotation': param.annotation if param.annotation != inspect.Parameter.empty else None,
    #         'has_default': param.default != inspect.Parameter.empty
    #     }
    #     result[param_name] = param_info

    # # Add return annotation if present
    # if sig.return_annotation != inspect.Signature.empty:
    #     result['__return__'] = {
    #         'annotation': sig.return_annotation
    #     }
    return result
