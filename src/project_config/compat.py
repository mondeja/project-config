"""Compatibility between Python versions."""

import functools
import sys


if sys.version_info < (3, 8):
    from typing_extensions import Protocol, TypedDict
else:
    from typing import Protocol, TypedDict

if sys.version_info < (3, 9):
    cached_function = functools.lru_cache(maxsize=None)
else:
    cached_function = functools.cache

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
)
