"""INI to JSON converter."""

import configparser
import typing as t


def loads(string: str) -> t.Dict[str, t.Any]:
    """Converts an INI file string to JSON.

    Args:
        string (str): INI file string to convert.

    Returns:
        dict: Conversion result.
    """
    result: t.Dict[str, t.Any] = {}
    ini = configparser.ConfigParser()
    ini.read_string(string)
    for section in ini.sections():
        result[section] = {}
        for option in ini.options(section):
            result[section][option] = ini.get(section, option)
    return result
