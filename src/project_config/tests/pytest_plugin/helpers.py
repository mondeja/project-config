"""Pytest plugin helpers."""

import os
import pathlib
import types
import typing as t

from project_config.compat import TypeAlias
from project_config.tree import Tree


FilesType: TypeAlias = t.Dict[str, t.Optional[t.Union[str, bool]]]
RootdirType: TypeAlias = t.Union[str, pathlib.Path]


def create_files(  # noqa: D103
    files: FilesType,
    rootdir: RootdirType,
) -> None:
    if isinstance(rootdir, pathlib.Path):
        rootdir = str(rootdir)
    for fpath, content in files.items():
        if content is False:
            continue
        full_path = os.path.join(rootdir, fpath)

        if content is None:
            os.mkdir(full_path)
        else:
            content = t.cast(str, content)
            # ensure parent path directory exists
            parent_fpath, _ = os.path.splitext(full_path)
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)
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
        tree.cache_files(list(files))
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
