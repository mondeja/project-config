"""Persistent cache."""

from __future__ import annotations

import contextlib
import importlib.util
import os
import shutil
from typing import Any

import appdirs

from project_config.compat import pickle_HIGHEST_PROTOCOL


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

CACHE_DIR = appdirs.user_data_dir(appname="project-config")


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
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(CACHE_DIR)

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
