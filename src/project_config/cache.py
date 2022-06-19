"""Persistent cache."""

import typing as t

import appdirs
import diskcache

from project_config.compat import cached_function, importlib_metadata


class Cache:
    """Wrapper for a unique :py:class:`diskcache.Cache` instance."""

    class Keys:  # noqa: D106
        expiration = "_project_config_cache_expiration"

    @staticmethod
    @cached_function
    def _get_cache() -> diskcache.Cache:
        project_config_metadata = importlib_metadata.metadata("project_config")
        data_dir = appdirs.user_data_dir(
            appname=project_config_metadata["name"],
            appauthor=project_config_metadata["author"],
            version=project_config_metadata["version"],
        )
        return diskcache.Cache(data_dir)

    @classmethod
    def set(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:  # noqa: A003, D102
        return cls._get_cache().set(*args, **kwargs)

    @classmethod
    def get(cls, *args: t.Any, **kwargs: t.Any) -> t.Any:  # noqa: D102
        return cls._get_cache().get(*args, **kwargs)
