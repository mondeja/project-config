"""Compatibility between Python versions."""

from __future__ import annotations

import functools
import shlex
import sys
from typing import TYPE_CHECKING


if sys.version_info < (3, 8):
    if TYPE_CHECKING:
        from typing_extensions import Literal, Protocol, TypedDict

    def shlex_join(cmd_list: list[str]) -> str:  # noqa: D103
        return " ".join(shlex.quote(x) for x in cmd_list)

    # For some reason pickle is failing on Python3.7 saying that the
    # protocol 4 is not supported.
    pickle_HIGHEST_PROTOCOL = 3
else:
    import pickle
    from typing import Literal, Protocol, TypedDict

    shlex_join = shlex.join

    pickle_HIGHEST_PROTOCOL = pickle.HIGHEST_PROTOCOL


if sys.version_info < (3, 9):
    cached_function = functools.lru_cache(maxsize=None)

    def removeprefix(string: str, prefix: str) -> str:  # noqa: D103
        return string[len(prefix) :] if string.startswith(prefix) else string

    def removesuffix(string: str, suffix: str) -> str:  # noqa: D103
        return string[: -len(suffix)] if string.endswith(suffix) else string

else:
    cached_function = functools.cache

    removeprefix = str.removeprefix
    removesuffix = str.removesuffix

if sys.version_info < (3, 10):
    import importlib_metadata

    if TYPE_CHECKING:
        from typing_extensions import TypeAlias
else:
    import importlib.metadata as importlib_metadata
    from typing import TypeAlias

if sys.version_info < (3, 11):
    from typing import NoReturn as Never

    if TYPE_CHECKING:
        from typing_extensions import NotRequired

    tomllib_package_name = "tomli"
else:
    from typing import Never, NotRequired

    tomllib_package_name = "tomllib"


__all__ = (
    "Protocol",
    "TypeAlias",
    "TypedDict",
    "Literal",
    "NotRequired",
    "Never",
    "cached_function",
    "tomllib_package_name",
    "importlib_metadata",
    "shlex_join",
    "removeprefix",
    "removesuffix",
    "pickle_HIGHEST_PROTOCOL",
)
