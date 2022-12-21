"""Persistent cache."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
from typing import Any, Iterator

import appdirs

from project_config.compat import importlib_metadata, pickle_HIGHEST_PROTOCOL


# ---

# Workaround for https://github.com/grantjenks/python-diskcache/pull/269
# TODO: Remove this workaround once the PR is merged and released.

_diskcache_init_path = importlib.util.find_spec(
    "diskcache",
).origin  # type: ignore
_diskcache_core_spec = importlib.util.spec_from_file_location(
    "diskcache.core",
    os.path.join(
        os.path.dirname(_diskcache_init_path),  # type: ignore
        "core.py",
    ),
)
_diskcache_core = importlib.util.module_from_spec(
    _diskcache_core_spec,  # type: ignore
)
_diskcache_core_spec.loader.exec_module(_diskcache_core)  # type: ignore

DiskCache = _diskcache_core.Cache

# ---

CACHE_DIR = appdirs.user_data_dir(
    appname=(
        # Pickle protocols could change between Python versions. If a cache
        # is created with a version of Python using an incompatible pickle
        # protocol, errors like the next will probably occur:
        #
        # ValueError: unsupported pickle protocol: 5
        #
        # To avoid this, we create a different cache directory for each
        # Python version
        f"project-config-py{sys.version_info.major}{sys.version_info.minor}"
    ),
)


def generate_possible_cache_dirs() -> Iterator[str]:
    """Generate the possible cache directories."""
    requires_python = importlib_metadata.metadata(
        "project-config",
    )["Requires-Python"]

    max_minor_version = re.search(  # type: ignore
        "<\\d+\\.(\\d+)",
        requires_python,
    ).group(1)
    for possible_py_dir in range(7, int(max_minor_version) + 1):
        yield appdirs.user_data_dir(
            appname=f"project-config-py3{possible_py_dir}",
        )


class Cache:
    """Wrapper for a unique :py:class:`diskcache.core.Cache` instance."""

    _cache = DiskCache(
        directory=CACHE_DIR,
        disk_pickle_protocol=pickle_HIGHEST_PROTOCOL,
    )
    _expiration_time: float | int | None = 30

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Cache is a not instanceable interface.")

    @staticmethod
    def clean() -> None:  # pragma: no cover
        """Remove the cache directory."""
        for possible_cache_dirpath in generate_possible_cache_dirs():
            if os.path.isdir(possible_cache_dirpath):
                shutil.rmtree(possible_cache_dirpath)

    @classmethod
    def set(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: A003, D102
        return cls._cache.set(
            *args,
            **dict(
                expire=cls._expiration_time,
                **kwargs,
            ),
        )

    @classmethod
    def get(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: D102
        return cls._cache.get(*args, **kwargs)  # pragma: no cover

    @classmethod
    def set_expiration_time(
        cls,
        expiration_time: float | int | None = None,
    ) -> None:
        """Set the expiration time for the cache.

        Args:
            expiration_time (float): Time in seconds.
        """
        cls._expiration_time = expiration_time
