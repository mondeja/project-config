"""Pytest plugin helpers."""

from __future__ import annotations

import os
import pathlib
import types
import typing as t

from project_config.compat import TypeAlias
from project_config.tree import Tree


FileType: TypeAlias = t.Optional[t.Union[str, bool]]
FilesType: TypeAlias = t.Union[
    t.List[t.Tuple[str, FileType]],
    t.Dict[str, FileType],
]
RootdirType: TypeAlias = t.Union[str, pathlib.Path]


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
            content = t.cast(str, content)
            # ensure parent path directory exists
            parent_fpath, _ = os.path.splitext(full_path)
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)

            if os.path.isdir(full_path):
                continue

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)


def create_tree(  # noqa: D103
    files: FilesType,
    rootdir: RootdirType,
    cache_files: bool = False,
) -> Tree:
    create_files(files, rootdir)
    tree = Tree(str(rootdir))
    if cache_files:
        _files = (
            list(files) if isinstance(files, dict) else [f[0] for f in files]
        )
        tree.cache_files(_files)
    return tree


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
    "create_files",
    "create_tree",
    "get_reporter_class_from_module",
)
