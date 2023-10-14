"""TOML serializing."""

from __future__ import annotations

from typing import Any

import tomlkit


def loads(string: str) -> dict[str, Any]:
    """Converts a TOML file string to an object.

    Args:
        string (str): TOML file string to convert.

    Returns:
        dict: Conversion result.
    """

    def iterate_key_values(obj: Any) -> Any:
        partial_result: dict[str, Any] | list[Any]

        if isinstance(obj, dict):
            partial_result = {}
            for k, value in obj.items():
                key = str(k)
                if isinstance(value, dict):
                    partial_result[key] = iterate_key_values(dict(value))
                elif isinstance(value, list):
                    partial_result[key] = iterate_key_values(value)
                elif isinstance(value, str):
                    partial_result[key] = str(value)
                else:
                    partial_result[key] = value

        elif isinstance(obj, list):
            partial_result = []
            for item in obj:
                if isinstance(item, dict):
                    partial_result.append(iterate_key_values(dict(item)))
                elif isinstance(item, list):
                    partial_result.append(iterate_key_values(item))
                elif isinstance(item, str):
                    partial_result.append(str(item))
                else:
                    partial_result.append(item)

        return partial_result

    return iterate_key_values(dict(tomlkit.loads(string)))  # type: ignore
