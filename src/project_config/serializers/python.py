"""Object serializing for Python scripts namespaces."""

from __future__ import annotations

import typing as t

from project_config.compat import TypeAlias


Namespace: TypeAlias = t.Dict[str, t.Any]


def loads(string: str, namespace: Namespace = {}) -> Namespace:
    """Execute a Python file and exposes their namespace as a dictionary.

    The logic is based in Sphinx's configuration file loader:
    https://github.com/sphinx-doc/sphinx/blob/4d7558e9/sphinx/config.py#L332

    Args:
        string (str): Python script.
        namespace (dict): Namespace to update.

    Returns:
        dict: Global namespace of the Python script as an object.
    """
    code = compile(string, "utf-8", "exec")
    exec(code, namespace)
    del namespace["__builtins__"]  # we don't care about builtins
    return namespace


def dumps(object: Namespace) -> str:
    """Converts a namespace to a Python script.

    Args:
        object (dict): Namespace to convert.

    Returns:
        str: Python script.
    """
    return (
        "\n".join(f"{key} = {value!r}" for key, value in object.items()) + "\n"
    )
