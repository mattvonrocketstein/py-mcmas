"""
mcmas.models.util: ....
"""

import typing
from typing import List

import pydantic

from mcmas.logic import Symbol
from mcmas.util import normalize_stderr_stdout

StringOrSymbol = typing.Annotated[
    typing.Union[str, Symbol], pydantic.BeforeValidator(str)
]
Str2List = typing.Annotated[
    typing.Union[str, None, List], pydantic.BeforeValidator(normalize_stderr_stdout)
]
Str2List = typing.Annotated[
    typing.Union[str, None, List], pydantic.BeforeValidator(normalize_stderr_stdout)
]
BoolMaybe = typing.Union[bool, None]
