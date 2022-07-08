"""Compatibility between Python versions."""

from __future__ import annotations

import functools
import shlex
import sys
import typing as t


if sys.version_info < (3, 8):
    from typing_extensions import Protocol, TypedDict

    def shlex_join(cmd_list: t.List[str]) -> str:  # noqa: D103
        return " ".join(shlex.quote(x) for x in cmd_list)

else:
    from typing import Protocol, TypedDict

    shlex_join = shlex.join


if sys.version_info < (3, 9):
    cached_function = functools.lru_cache(maxsize=None)

    def removeprefix(string: str, prefix: str) -> str:
        return string[len(prefix) :] if string.startswith(prefix) else string

    def removesuffix(string: str, suffix: str) -> str:
        return string[: -len(suffix)] if string.endswith(suffix) else string

else:
    cached_function = functools.cache

    removeprefix = str.removeprefix
    removesuffix = str.removesuffix

if sys.version_info < (3, 10):
    import importlib_metadata

    from typing_extensions import TypeAlias
else:
    import importlib.metadata as importlib_metadata
    from typing import TypeAlias

if sys.version_info < (3, 11):
    tomllib_package_name = "tomli"
else:
    tomllib_package_name = "tomllib"

from typing_extensions import NotRequired


__all__ = (
    "Protocol",
    "TypeAlias",
    "TypedDict",
    "NotRequired",
    "cached_function",
    "tomllib_package_name",
    "importlib_metadata",
    "shlex_join",
)
