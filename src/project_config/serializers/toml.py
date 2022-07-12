"""TOML serializing."""

import tomlkit

import typing as t

def loads(string: str) -> t.Dict[str, t.Any]:
    """Converts a TOML file string to JSON.

    Args:
        string (str): TOML file string to convert.

    Returns:
        dict: Conversion result.
    """

    def iterate_key_values(obj: t.Dict[str, t.Any]) -> t.Iterator[t.Tuple[str, t.Any]]:
        if isinstance(obj, dict):
            _partial_result = {}
            for key, value in obj.items():
                key = str(key)
                if isinstance(value, dict):
                    value = dict(value)
                    _partial_result[key] = iterate_key_values(value)
                else:
                    if isinstance(value, list):
                        value = iterate_key_values(value)
                    elif isinstance(value, str):
                        value = str(value)
                    _partial_result[key] = value
        elif isinstance(obj, list):
            _partial_result = []
            for item in obj:
                if isinstance(item, dict):
                    item = dict(item)
                    _partial_result.append(iterate_key_values(item))
                else:
                    if isinstance(item, list):
                        item = iterate_key_values(item)
                    elif isinstance(item, str):
                        item = str(item)
                    _partial_result.append(item)

        return _partial_result

    return iterate_key_values(dict(tomlkit.loads(string)))
