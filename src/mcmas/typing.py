"""
mcmas.typing.
"""

import typing
from pathlib import Path
from typing import *  # noqa
from typing import Annotated, ClassVar, Dict, List, Self, Union  # noqa

import pydantic

from mcmas import util
from mcmas.logic import Symbol

NoneType = type(None)
Bool = bool

PathType = typing.Annotated[
    typing.Union[str, NoneType, Path], pydantic.BeforeValidator(str)
]

PathList = typing.List[PathType]

OptionalAny = typing.Optional[typing.Any]
BoolMaybe = typing.Optional[bool]
StringMaybe = typing.Optional[str]
CallableMaybe = typing.Optional[typing.Callable]
DictMaybe = typing.Optional[typing.Dict]
TagDict = typing.Dict[str, str]


Namespace = typing.Dict[str, typing.Any]
CallableNamespace = typing.Dict[str, typing.Callable]


@pydantic.validate_call
def ensure_list(value: typing.Any) -> typing.List:
    """
    
    """
    if isinstance(value, str):
        tmp = value.replace("{", "").replace("}", "").replace(";", "")
        return [x.strip() for x in tmp.split(",")]
    elif value is None:
        return []
    else:
        return [str(v) for v in value]


@pydantic.validate_call
def ensure_groups(val) -> typing.Dict:
    """
    
    """
    if val is None:
        return {}
    elif isinstance(val, (list,)):
        out = {}
        for line in val:
            # line=line.replace
            k, v = line.split("=")
            out[k.strip()] = ensure_list(v.strip())
            # .strip().replace('{}')
        return out
    else:
        return val


@pydantic.validate_call
def ensure_protocol(value) -> typing.Dict:
    """
    
    """
    if isinstance(value, (list,)):
        out = {}
        for line in value:
            k, v = line.split(":")
            # out[tmp.pop(0)] = ":".join(tmp)
            out[k.strip()] = v.strip()
        return out
    if isinstance(value, (dict,)):
        for k, v in value.items():
            if isinstance(v, (list,)):
                value[k] = "{" + ",".join([str(i) for i in v]) + "};"
    return value


@pydantic.validate_call
def ensure_dict(val) -> typing.Dict:
    """
    
    """
    if val is None:
        return {}
    if isinstance(val, (list,)):
        out = {}
        for line in val:
            k, v = line.split(":")
            out[k] = v
        return out
    if not val:
        return {}
    return val


StringOrSymbol = typing.Annotated[
    typing.Union[str, Symbol], pydantic.BeforeValidator(str)
]
Str2List = typing.Annotated[
    typing.Union[str, None, typing.List],
    pydantic.BeforeValidator(util.normalize_stderr_stdout),
]
Str2List = typing.Annotated[
    typing.Union[str, None, typing.List],
    pydantic.BeforeValidator(util.normalize_stderr_stdout),
]
SymbolDict = typing.Dict[StringOrSymbol, StringOrSymbol]
SymbolList = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]
SymbolList2 = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.PlainSerializer(lambda v: [str(x) for x in v])
]

ActionsType = SymbolList
VarsType = typing.Annotated[
    typing.Union[None, SymbolDict], pydantic.BeforeValidator(ensure_dict)
]
ObsVarsType = typing.Annotated[SymbolDict, pydantic.BeforeValidator(ensure_dict)]
ProtocolType = typing.Annotated[
    typing.Union[SymbolDict], pydantic.BeforeValidator(ensure_protocol)
]
GroupsType = typing.Annotated[
    typing.Union[None, typing.Dict[str, typing.List[StringOrSymbol]]],
    pydantic.BeforeValidator(ensure_groups),
]
LobsvarsType = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]

FormulaeType = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]
InitStateType = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]
EvolType = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]
EvalType = typing.Annotated[
    typing.List[StringOrSymbol], pydantic.BeforeValidator(ensure_list)
]
