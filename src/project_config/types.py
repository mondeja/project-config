"""Types."""

from __future__ import annotations

import typing as t

from project_config.compat import NotRequired, TypeAlias, TypedDict


class ErrorDict(TypedDict):
    """Error data type."""

    message: str
    definition: str
    file: NotRequired[str]
    hint: NotRequired[str]
    fixed: NotRequired[bool]
    fixable: NotRequired[bool]


class Rule(TypedDict, total=False):
    """Style rule."""

    files: t.List[str]


StrictResultType: TypeAlias = t.Tuple[str, t.Union[bool, ErrorDict]]

# Note that the real second item in the tuple would be
# `t.Union[bool, ErrorDict]`, but mypy does not like multiple types.
# TODO: investigate a generic type here?
LazyGenericResultType: TypeAlias = t.Tuple[str, t.Any]
Results: TypeAlias = t.Iterator[LazyGenericResultType]


class ActionsContext(t.NamedTuple):
    """Context of global data passed to rule verbs."""

    fix: bool


__all__ = ("Rule", "Results", "ErrorDict", "ActionsContext")
