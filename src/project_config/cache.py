"""Persistent cache."""

from __future__ import annotations

import base64
import hashlib
import os
import pickle
import re
import shutil
import sys
import time
from typing import Any, Iterator

import appdirs

from project_config.compat import importlib_metadata


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


def get_creation_time_from_fpath(fpath: str) -> int:
    """Get creation time of an entry in the cache given its path."""
    with open(fpath, "rb") as file:
        return int(file.readline())


def read_file(fpath: str) -> bytes:  # noqa: D102
    """Read a file from the cache."""
    with open(fpath, "rb") as f:
        fcontent = f.read()
        _, content = fcontent.split(b"\n", 1)
        return content


def write_file(fpath: str, value: Any) -> None:  # noqa: D102
    """Write a file to the cache."""
    with open(fpath, "wb") as f:
        f.write(str(int(time.time())).encode())
        f.write(b"\n")
        f.write(pickle.dumps(value))


class Cache:
    """Global cache to avoid recomputing expensive intermediate objects."""

    _expiration_time: float | int | None = 30

    def __init__(self) -> None:  # noqa: D107 pragma: no cover
        raise NotImplementedError("Cache is a not instanceable interface.")

    @staticmethod
    def clean() -> None:  # pragma: no cover
        """Remove the cache directory."""
        for possible_cache_dirpath in generate_possible_cache_dirs():
            if os.path.isdir(possible_cache_dirpath):
                shutil.rmtree(possible_cache_dirpath)

    @classmethod
    def generate_unique_key_from_tree_entry(cls, tree_entry: str) -> str:
        """Generate a unique key."""
        return base64.urlsafe_b64encode(
            hashlib.md5(tree_entry.encode()).digest(),
        ).decode("utf-8")

    @classmethod
    def get(cls, tree_entry: str) -> Any:  # noqa: D102
        key = cls.generate_unique_key_from_tree_entry(tree_entry)
        fpath = os.path.join(CACHE_DIR, key)
        if os.path.isfile(fpath):
            creation_time = get_creation_time_from_fpath(fpath)
            if time.time() < creation_time + (cls._expiration_time or 0):
                return pickle.loads(read_file(fpath))
            os.remove(fpath)
        return None

    @classmethod
    def set(cls, tree_entry: str, value: Any) -> None:  # noqa: D102
        key = cls.generate_unique_key_from_tree_entry(tree_entry)
        fpath = os.path.join(CACHE_DIR, key)
        if not os.path.isfile(fpath):
            write_file(fpath, value)
        elif time.time() > get_creation_time_from_fpath(fpath) + (
            cls._expiration_time or 0
        ):
            os.remove(fpath)
            write_file(fpath, value)

    @classmethod
    def ensure_dir(cls) -> None:
        """Ensure the cache directory exists."""
        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    @classmethod
    def set_expiration_time(
        cls,
        expiration_time: float | int | None = None,
    ) -> None:
        """Configure global cache.

        Args:
            expiration_time (float): Expiration time in seconds for cached
                objects.
        """
        cls._expiration_time = expiration_time
