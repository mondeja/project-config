"""Persistent cache."""

from __future__ import annotations

import contextlib
import os
import shutil
from typing import Any

import appdirs
import diskcache


CACHE_DIR = appdirs.user_data_dir(
    appname="project-config",
    appauthor="m",
)


class Cache:
    """Wrapper for a unique :py:class:`diskcache.Cache` instance."""

    _cache = diskcache.Cache(CACHE_DIR)
    _expiration_time: float | int | None = 30

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Cache is a not instanceable interface.")

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
    def get(cls, *args: Any, **kwargs: Any) -> str | None:  # noqa: D102
        if os.environ.get("PROJECT_CONFIG_USE_CACHE") == "false":
            return None
        return cls._cache.get(  # type: ignore  # pragma: no cover
            *args, **kwargs
        )

    @staticmethod
    def clean() -> None:
        """Remove the cache directory."""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(CACHE_DIR)

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
