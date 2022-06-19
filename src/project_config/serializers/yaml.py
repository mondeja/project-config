"""YAML to JSON converter."""

import io
import typing as t

import ruamel.yaml


def dumps(
    obj: t.Dict[str, t.Any], *args: t.Tuple[t.Any], **kwargs: t.Any
) -> str:
    """Deserializes a JSON object converting to string in YAML format."""
    f = io.StringIO()
    kws = {"default_flow_style": False, "width": 88888}
    kws.update(kwargs)
    ruamel.yaml.safe_dump(obj, f, *args, **kws)
    return f.getvalue()


def loads(string: str, *args: t.Any, **kwargs: t.Any) -> t.Any:
    """Deserializes a YAML string to a dictionary."""
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    return yaml.load(string, *args, **kwargs)
