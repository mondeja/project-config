"""Array serializing for text files."""

import typing as t


def loads(string: str) -> t.List[str]:
    """Converts a string to an array of lines.

    Args:
        string: The string to convert.

    Returns:
        list: Array of lines created from string splitting.
    """
    return string.splitlines()
