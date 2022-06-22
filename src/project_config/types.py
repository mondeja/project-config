"""Types."""

import typing as t

from project_config.compat import NotRequired, TypeAlias, TypedDict


class ErrorDict(TypedDict):
    """Error data type."""

    file: NotRequired[str]
    message: str
    definition: str


class Rule(TypedDict, total=False):
    """Style rule."""

    files: t.List[str]


# Note that the real second item in the tuple would be
# `t.Union[bool, ErrorDict]`, but mypy does not like multiple types.
# TODO: investigate a generic type here?
ResultType: TypeAlias = t.Tuple[str, t.Any]
ResultsType: TypeAlias = t.Iterator[ResultType]

Results = ResultsType

__all__ = (
    "Rule",
    "Results",
    "ErrorDict",
)
