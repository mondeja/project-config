"""Compatibility between Python versions."""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict


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
    "removeprefix",
    "removesuffix",
)
