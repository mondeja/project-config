import configparser
import re


# Extracted from https://github.com/editorconfig/editorconfig-core-py/blob/master/editorconfig/ini.py
# but modified to become an editorconfig configuration to JSON converter


class EditorConfigError(Exception):
    """Parent class of all exceptions raised by EditorConfig"""


class ParsingError(configparser.ParsingError, EditorConfigError):
    """Error raised if an EditorConfig file could not be parsed"""


MAX_SECTION_LENGTH = 4096
MAX_PROPERTY_LENGTH = 50
MAX_VALUE_LENGTH = 255

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


def loads(string: str):
    result = {}

    sectname, error = None, None

    for i, line in enumerate(string.replace("\r\n", "\n").split("\n")):
        if i == 0 and line.startswith("\ufeff"):
            line = line[1:]  # Strip UTF-8 BOM
        # comment or blank line?
        if line.strip() == "" or line[0] in "#;":
            continue

        # a section header or option header?
        mo = SECTCRE.match(line)
        if mo:
            sectname = mo.group("header")
            if len(sectname) > MAX_SECTION_LENGTH:
                continue
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
            if len(optname) > MAX_PROPERTY_LENGTH or len(optval) > MAX_VALUE_LENGTH:
                continue
            if sectname:
                result[sectname][optname] = optval
            elif not sectname and optname == "root":
                if "" not in result:
                    result[""] = {}
                result[""] = optval.lower() == "true"
            continue

        # a non-fatal parsing error occurred.  set up the
        # exception but keep going. the exception will be
        # raised at the end of the file and will contain a
        # list of all bogus lines
        if not error:
            error = ParsingError("")
        error.append(i, line)

    if error:
        raise error
    return result
