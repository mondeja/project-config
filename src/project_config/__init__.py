"""Reproducible configuration across projects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from project_config import tree
from project_config.constants import Error, InterruptingError, ResultValue
from project_config.types import ActionsContext


__all__ = [
    "tree",
    "Rule",
    "Error",
    "InterruptingError",
    "ResultValue",
    "ActionsContext",
]


if TYPE_CHECKING:
    # TYPE_CHECKING guards have been added to the source code to avoid
    # runtime errors when using future annotations styles in TypeAlias(es)
    #
    # TODO: When the minimum Python version is 3.10, drop these
    # TYPE_CHECKING branches

    from project_config.types import Results, Rule  # noqa: F401

    __all__.extend(["Results", "Rule"])
