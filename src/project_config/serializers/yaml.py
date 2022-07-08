"""YAML to JSON converter."""

from __future__ import annotations

import io
import typing as t

import ruamel.yaml


def dumps(
    obj: t.Dict[str, t.Any],
    *args: t.Tuple[t.Any],
    **kwargs: t.Any,
) -> str:
    """Deserializes an object converting it to string in YAML format."""
    f = io.StringIO()
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    yaml.width = 88888
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(obj, f, *args, **kwargs)
    return f.getvalue()


def loads(string: str, *args: t.Any, **kwargs: t.Any) -> t.Any:
    """Deserializes a YAML string to a dictionary."""
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    return yaml.load(string, *args, **kwargs)
