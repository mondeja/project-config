"""Array serializing for text files."""

from __future__ import annotations


def loads(string: str) -> list[str]:
    """Converts a string to an array of lines.

    Args:
        string: The string to convert.

    Returns:
        list: Array of lines created from string splitting.
    """
    return string.splitlines()


def dumps(obj: list[str]) -> str:
    """Converts an array of lines to a string.

    Args:
        obj: The array of lines to convert.

    Returns:
        str: The string created from joining the array of lines.
    """
    result = "\n".join(obj)
    if result:
        result += "\n"
    return result
