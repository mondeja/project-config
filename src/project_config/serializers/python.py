"""Object serializing for Python scripts namespaces."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from project_config.compat import TypeAlias

    Namespace: TypeAlias = dict[str, Any]

DEFAULT_NAMESPACE: Namespace = {}


def loads(
    string: str,
    namespace: Namespace = DEFAULT_NAMESPACE,
) -> Namespace:
    """Execute a Python file and exposes their namespace as a dictionary.

    The logic is based in Sphinx's configuration file loader:
    https://github.com/sphinx-doc/sphinx/blob/4d7558e9/sphinx/config.py#L332

    Args:
        string (str): Python script.
        namespace (dict): Namespace to update.

    Returns:
        dict: Global namespace of the Python script as an object.
    """
    exec(compile(string, "utf-8", "exec"), namespace)  # noqa: DUO105,DUO110
    try:
        del namespace["__builtins__"]  # we don't care about builtins
    except KeyError:  # pragma: no cover
        pass
    return namespace


def _pyobject_to_string(value: Any) -> str:
    if isinstance(value, str):
        escaped_value = re.sub(r"([\"])", r"\\\1", value)
        return f'"{escaped_value}"'
    if isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, type):
        value = value.__name__
    elif isinstance(value, dict):
        if len(str(value)) > 60:
            newline = "\n    "
            delimiter = "\n"
        else:
            newline = " "
            delimiter = ""
        result = (
            "{"
            + (newline if newline != " " else "")
            + f",{newline}".join(
                f'"{key}": {str(_pyobject_to_string(item))}'
                for key, item in value.items()
            )
        )
        if newline != " ":
            result += ","

        result += delimiter + "}"
        return result
    elif isinstance(value, list):
        if len(str(value)) > 60:
            newline = "\n    "
            delimiter = "\n"
        else:
            newline = " "
            delimiter = ""
        result = (
            "["
            + (newline if newline != " " else "")
            + f",{newline}".join(
                str(_pyobject_to_string(item)) for item in value
            )
        )
        if newline != " ":
            result += ","

        result += delimiter + "]"
        return result
    return cast(str, value)


def dumps(obj: Any) -> str:
    """Converts a namespace to a Python script.

    Args:
        obj (dict): Namespace to convert.

    Returns:
        str: Python script.
    """
    result = ""
    for key, value in obj.items():
        result += f"{key} = {_pyobject_to_string(value)}\n"

    return result
