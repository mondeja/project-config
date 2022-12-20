"""Pytest plugin helpers."""

from __future__ import annotations

import os
import pathlib
import types
from typing import TYPE_CHECKING, cast

import pytest

from project_config import tree


if TYPE_CHECKING:
    from project_config.compat import TypeAlias

    FileType: TypeAlias = str | bool | None
    FilesType: TypeAlias = dict[str, FileType]
    RootdirType: TypeAlias = str | pathlib.Path


def create_files(  # noqa: D103
    files: FilesType,
    rootdir: RootdirType,
) -> None:
    if isinstance(rootdir, pathlib.Path):
        rootdir = str(rootdir)
    _files = files.items() if isinstance(files, dict) else files
    for fpath, content in _files:
        if content is False:
            continue
        full_path = os.path.join(rootdir, fpath)

        if content is None:
            os.mkdir(full_path)
        else:
            # same name as an existent directory, means that `files` has been
            # passed as a list of tuples
            content = cast(str, content)
            # ensure parent path directory exists
            parent_fpath, ext = os.path.splitext(full_path)
            if not ext:
                parent_fpath = os.path.abspath(os.path.dirname(parent_fpath))
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)

            if os.path.isdir(full_path):
                continue

            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except OSError:
                # globs raising here on Windows
                continue


def create_tree(  # noqa: D103
    files: FilesType,
    rootdir: RootdirType,
    cache_files: bool = False,
) -> None:
    create_files(files, rootdir)
    if cache_files:
        _files = (
            list(files) if isinstance(files, dict) else [f[0] for f in files]
        )
        for fpath in _files:
            tree.cache_file(
                fpath,
                forbid_serializers=("py",),
                ignore_serialization_errors=True,
            )


def assert_expected_files(  # noqa: D103
    expected_files: FilesType,
    rootdir: RootdirType,
) -> None:
    if isinstance(rootdir, pathlib.Path):
        rootdir = str(rootdir)
    _expected_files = (
        expected_files.items()
        if isinstance(expected_files, dict)
        else expected_files
    )
    for fpath, content in _expected_files:
        full_path = os.path.join(rootdir, fpath)
        if content is False:
            assert not os.path.exists(full_path)
        else:
            assert os.path.exists(full_path)
            if content is not None:
                try:
                    with open(full_path, encoding="utf-8") as f:
                        assert f.read() == content
                except IsADirectoryError:
                    continue
                except PermissionError:
                    pytest.skip()
                    continue
                except OSError:
                    continue


def get_reporter_class_from_module(  # noqa: D103
    reporter_module: types.ModuleType,
    color: bool,
) -> type:
    for object_name in dir(reporter_module):
        if object_name.startswith(("_", "Base")):
            continue
        if (color and "ColorReporter" in object_name) or (
            not color
            and "Reporter" in object_name
            and "ColorReporter" not in object_name
        ):
            return getattr(reporter_module, object_name)  # type: ignore

    raise ValueError(
        f"No{' color' if color else ''} reporter class found in"
        f" module '{reporter_module.__name__}'",
    )


__all__ = (
    "assert_expected_files",
    "create_files",
    "create_tree",
    "get_reporter_class_from_module",
)
