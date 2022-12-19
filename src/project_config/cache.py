"""Persistent cache."""

from __future__ import annotations

import contextlib
import os
import shutil
from typing import Any

import appdirs


CACHE_DIR = appdirs.user_data_dir(
    appname="project-config",
    appauthor="m",
)


class BaseCache:  # noqa: D101
    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Cache is a not instanceable interface.")

    @staticmethod
    def clean() -> None:
        """Remove the cache directory."""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(CACHE_DIR)


if os.environ.get("PROJECT_CONFIG_USE_CACHE") == "false":

    class Cache(BaseCache):  # noqa: D101
        @classmethod
        def set(  # noqa: A003, D102
            cls,
            *args: Any,  # noqa: U100
            **kwargs: Any,  # noqa: U100
        ) -> None:
            pass

        @classmethod
        def get(cls, *args: Any, **kwargs: Any) -> None:  # noqa: D102, U100
            pass

        @classmethod
        def set_expiration_time(  # noqa: D102
            cls,
            expiration_time: float | int | None = None,  # noqa: U100
        ) -> None:
            pass

else:
    # Workaround for https://github.com/grantjenks/python-diskcache/pull/269
    # TODO: Remove this workaround once the PR is merged and released.
    import importlib.util

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

    class Cache(BaseCache):  # type: ignore
        """Wrapper for a unique :py:class:`diskcache.core.Cache` instance."""

        _cache = DiskCache(CACHE_DIR)
        _expiration_time: float | int | None = 30

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
            return cls._cache.get(  # type: ignore  # pragma: no cover
                *args, **kwargs
            )

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
