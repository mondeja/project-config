"""Types."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from typing import TYPE_CHECKING


if TYPE_CHECKING:
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

    StrictResultType: TypeAlias = tuple[str, bool | ErrorDict]
    LazyGenericResultType: TypeAlias = tuple[str, bool | ErrorDict]
    Results: TypeAlias = Iterator[LazyGenericResultType]


@dataclasses.dataclass
class ActionsContext:
    """State of project config when executing rule verbs."""

    fix: bool
    files: list[str] = dataclasses.field(default_factory=list)


__all__ = ("Rule", "Results", "ErrorDict", "ActionsContext")
