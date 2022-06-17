"""Python namespace for dictionary serializing."""

import typing as t

from project_config.compat import TypeAlias


Namespace: TypeAlias = t.Dict[str, t.Any]


def loads(string: str, namespace: Namespace = {}) -> Namespace:
    """Execute a Python file and exposes their namespace as a dictionary.

    The logic is based in Sphinx's configuration file loader:
    https://github.com/sphinx-doc/sphinx/blob/4d7558e9/sphinx/config.py#L332
    """
    code = compile(string, "utf-8", "exec")
    exec(code, namespace)
    del namespace["__builtins__"]  # we don't care about builtins
    return namespace
