"""Types."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, NamedTuple

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

    files: list[str]
    hint: NotRequired[str]


if TYPE_CHECKING:
    StrictResultType: TypeAlias = tuple[str, bool | ErrorDict]
    LazyGenericResultType: TypeAlias = tuple[str, bool | ErrorDict]
    Results: TypeAlias = Iterator[LazyGenericResultType]


class ActionsContext(NamedTuple):
    """Context of global data passed to rule verbs."""

    fix: bool


__all__ = ("Rule", "Results", "ErrorDict", "ActionsContext")
