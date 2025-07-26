"""
mcmas.util.typing.
"""

import typing
from pathlib import Path as BasePath

Union = typing.Union

OptionalAny = typing.Optional[typing.Any]
PathType = type(BasePath())

Bool = bool
NoneType = type(None)
BoolMaybe = typing.Optional[bool]
StringMaybe = typing.Optional[str]
CallableMaybe = typing.Optional[typing.Callable]
DictMaybe = typing.Optional[typing.Dict]
TagDict = typing.Dict[str, str]


Namespace = typing.Dict[str, typing.Any]
CallableNamespace = typing.Dict[str, typing.Callable]

# i.e. `obj,created = model.objects.get_or_create()`
GetOrCreateResult = typing.Tuple[object, bool]
