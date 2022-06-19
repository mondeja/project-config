"""Reproducible configuration across projects."""

import importlib
import typing as t


# PEP 562
modules_objects = {
    "Tree": "project_config.tree",
    "Rule": "project_config.plugins._types",
    "Results": "project_config.plugins._types",
    "Error": "project_config.plugins._constants",
    "InterruptingError": "project_config.plugins._constants",
    "ResultValue": "project_config.plugins._constants",
}


def __getattr__(name: str) -> t.Any:
    try:
        module_dotpath = modules_objects[name]
    except KeyError:  # pragma: no cover
        raise ImportError(
            f"cannot import name '{name}' from 'project_config' ({__file__})",
            name=name,
            path="project_config",
        ) from None
    return getattr(
        importlib.import_module(module_dotpath),
        name,
    )


__all__ = list(modules_objects)
