"""INI to JSON converter."""

from __future__ import annotations

import configparser
import io
from typing import Any


def loads(string: str) -> dict[str, Any]:
    """Converts an INI file string to JSON.

    Args:
        string (str): INI file string to convert.

    Returns:
        dict: Conversion result.
    """
    result: dict[str, Any] = {}
    ini = configparser.ConfigParser()
    ini.read_string(string)
    for section in ini.sections():
        result[section] = {}
        for option in ini.options(section):
            result[section][option] = ini.get(section, option)
    return result


def dumps(obj: Any) -> str:
    """Converts a JSON object to an INI file string.

    Args:
        object (dict): JSON object to convert.

    Returns:
        str: Conversion result.
    """
    stream = io.StringIO()
    ini = configparser.ConfigParser(interpolation=None)
    for section, options in obj.items():
        ini.add_section(section)
        for option, value in options.items():
            ini.set(section, option, value)
    ini.write(stream)
    return stream.getvalue()
