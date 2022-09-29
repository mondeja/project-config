"""Persistent cache."""

from __future__ import annotations

import contextlib
import os
import shutil
import typing as t

import appdirs
import diskcache

from project_config.compat import cached_function, importlib_metadata


@cached_function
def _directory() -> str:
    project_config_metadata = importlib_metadata.metadata("project_config")
    return appdirs.user_data_dir(
        appname=project_config_metadata["name"],
        appauthor=project_config_metadata["author"],
    )


class Cache:
    """Wrapper for a unique :py:class:`diskcache.Cache` instance."""

    _cache = diskcache.Cache(_directory())
    _expiration_time = 30

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Cache is a not instanceable interface.")

    @classmethod
    def set(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:  # noqa: A003, D102
        return cls._cache.set(
            *args,
            **dict(
                expire=cls._expiration_time,
                **kwargs,
            ),
        )

    @classmethod
    def get(  # noqa: D102
        cls, *args: t.Any, **kwargs: t.Any
    ) -> t.Optional[str]:
        if os.environ.get("PROJECT_CONFIG_USE_CACHE") == "false":
            return None
        return cls._cache.get(  # type: ignore  # pragma: no cover
            *args, **kwargs
        )

    @staticmethod
    def clean() -> bool:
        """Remove the cache directory."""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(_directory())
        return True

    @staticmethod
    def get_directory() -> str:
        """Return the cache directory."""
        return _directory()

    @classmethod
    def set_expiration_time(
        cls,
        expiration_time: t.Optional[float] = None,
    ) -> None:
        """Set the expiration time for the cache.

        Args:
            expiration_time (float): Time in seconds.
        """
        cls._expiration_time = expiration_time  # type: ignore
