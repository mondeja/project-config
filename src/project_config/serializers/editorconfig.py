"""Editorconfig INI-like configuration file to JSON converter.

Based on https://github.com/editorconfig/editorconfig-core-py/blob/master/editorconfig/ini.py
"""  # noqa: E501

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from project_config.compat import TypeAlias

    EditorConfigConfigType: TypeAlias = dict[str, dict[str, str | int]]


SECTCRE = re.compile(
    r"""
    \s *                                # Optional whitespace
    \[                                  # Opening square brace
    (?P<header>                         # One or more characters excluding
        ( [^\#;] | \\\# | \\; ) +       # unescaped # and ; characters
    )
    \]                                  # Closing square brace
    """,
    re.VERBOSE,
)

OPTCRE = re.compile(
    r"""
    \s *                                # Optional whitespace
    (?P<option>                         # One or more characters excluding
        [^:=\s]                         # : a = characters (and first
        [^:=] *                         # must not be whitespace)
    )
    \s *                                # Optional whitespace
    (?P<vi>
        [:=]                            # Single = or : character
    )
    \s *                                # Optional whitespace
    (?P<value>
        . *                             # One or more characters
    )
    $
    """,
    re.VERBOSE,
)


def loads(string: str) -> EditorConfigConfigType:
    """Converts a .editorconfig configuration file string to JSON.

    Args:
        string (str): Configuration file string.
    """
    result: EditorConfigConfigType = {}

    sectname = None

    # Strip UTF-8 BOM if present and convert to lines
    string_lines = string.lstrip("\ufeff").splitlines()

    for line in string_lines:
        # comment or blank line?
        if line.strip() == "" or line[0] in "#;":
            continue

        # a section header or option header?
        mo = SECTCRE.match(line)
        if mo:
            sectname = mo.group("header")
            result[sectname] = {}
            continue

        mo = OPTCRE.match(line)
        if mo:
            optname, vi, optval = mo.group("option", "vi", "value")
            if ";" in optval or "#" in optval:
                # ';' and '#' are comment delimiters only if
                # preceeded by a spacing character
                m = re.search("(.*?) [;#]", optval)
                if m:
                    optval = m.group(1)
            optval = optval.strip()
            # allow empty values
            if optval == '""':
                optval = ""
            optname = optname.lower().rstrip()
            if sectname:
                result[sectname][optname] = (
                    int(optval)
                    if optname in ("indent_size", "tab_width")
                    else (
                        optval.lower() == "true"
                        if optname
                        in ("trim_trailing_whitespace", "insert_final_newline")
                        else optval
                    )
                )
            elif not sectname and optname == "root":
                if "" not in result:
                    result[""] = {}
                result[""][optname] = optval.lower() == "true"
            continue

    return result


def _pyobject_to_ini_str(obj: Any) -> str:
    """Converts a Python object to a string.

    Args:
        obj (Any): Python object.

    Returns:
        str: String representation of the object.
    """
    if isinstance(obj, str):
        if not obj:
            return '""'
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    return str(obj)


def dumps(obj: Any) -> str:
    """Converts a JSON object to a .editorconfig configuration file string.

    Args:
        obj (Any): JSON object.
    """
    result = ""

    for key, value in obj.items():
        if key == "":
            for optname, optvalue in value.items():
                result += f"{optname} = {_pyobject_to_ini_str(optvalue)}\n"
        else:
            result += f"\n[{key}]\n"
            for optname, optvalue in value.items():
                result += f"{optname} = {_pyobject_to_ini_str(optvalue)}\n"

    return result
