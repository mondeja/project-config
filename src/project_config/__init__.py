import importlib
import typing as t


# PEP 562
modules_objects = {
    "Files": "project_config.plugins._types",
    "Rule": "project_config.plugins._types",
    "VerbResult": "project_config.plugins._types",
}


def __getattr__(name: str) -> t.Any:
    try:
        module_dotpath = modules_objects[name]
    except KeyError:
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
