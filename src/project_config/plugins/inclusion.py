"""Inclusions checker plugin."""

import os
import pprint
import typing as t

from project_config import (
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)


def _directories_not_accepted_as_inputs_error(
    action_type: str,
    action_name: str,
    dir_path: str,
    definition: str,
) -> t.Dict[str, str]:
    return {
        "message": (
            f"Directory found but the {action_type} '{action_name}' does not"
            " accepts directories as inputs"
        ),
        "file": f"{dir_path.rstrip(os.sep)}/",
        "definition": definition,
    }


class InclusionPlugin:
    @staticmethod
    def includeLines(
        value: t.List[str],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The value must be of type array",
                "definition": ".includeLines",
            }
            return
        elif not value:
            yield InterruptingError, {
                "message": "The value must not be empty",
                "definition": ".includeLines",
            }
            return

        expected_lines = []
        for i, line in enumerate(value):
            if not isinstance(line, str):
                yield InterruptingError, {
                    "message": (
                        f"The expected line '{pprint.pformat(line)}'"
                        " must be of type string"
                    ),
                    "definition": f".includeLines[{i}]",
                }
                return
            clean_line = line.strip("\r\n")
            if clean_line in expected_lines:
                yield InterruptingError, {
                    "message": f"Duplicated expected line '{clean_line}'",
                    "definition": f".includeLines[{i}]",
                }
                return
            elif not clean_line:
                yield InterruptingError, {
                    "message": "Expected line must not be empty",
                    "definition": f".includeLines[{i}]",
                }
                return
            expected_lines.append(clean_line)

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "includeLines",
                        fpath,
                        f".files[{f}]",
                    ),
                )
                continue

            fcontent_lines = fcontent.splitlines()
            for line_index, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    yield Error, {
                        "message": f"Expected line '{expected_line}' not found",
                        "file": fpath,
                        "definition": f".includeLines[{line_index}]",
                    }

    @staticmethod
    def ifIncludeLines(
        value: t.Dict[str, t.List[str]],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, dict):
            yield InterruptingError, {
                "message": "The value must be of type object",
                "definition": ".ifIncludeLines",
            }
            return
        elif not value:
            yield InterruptingError, {
                "message": "The value must not be empty",
                "definition": ".ifIncludeLines",
            }
            return

        for fpath, expected_lines in value.items():
            if not fpath:
                yield InterruptingError, {
                    "message": "File paths must not be empty",
                    "definition": ".ifIncludeLines",
                }
                return

            if not isinstance(expected_lines, list):
                yield InterruptingError, {
                    "message": (
                        f"The expected lines '{pprint.pformat(expected_lines)}'"
                        " must be of type array"
                    ),
                    "definition": f".ifIncludeLines[{fpath}]",
                }
                return
            elif not expected_lines:
                yield InterruptingError, {
                    "message": "Expected lines must not be empty",
                    "definition": f".ifIncludeLines[{fpath}]",
                }
                return

            fcontent = tree.get_file_content(fpath)

            if fcontent is None:
                yield InterruptingError, {
                    "message": (
                        "File specified in conditional 'ifIncludeLines'"
                        " not found"
                    ),
                    "file": fpath,
                    "definition": f".ifIncludeLines[{fpath}]",
                }
                return
            elif not isinstance(fcontent, str):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "conditional",
                        "ifIncludeLines",
                        fpath,
                        f".ifIncludeLines[{fpath}]",
                    ),
                )
                return

            fcontent_lines = fcontent.splitlines()
            checked_lines = []
            for i, line in enumerate(expected_lines):
                if not isinstance(line, str):
                    yield InterruptingError, {
                        "message": (
                            f"The expected line '{pprint.pformat(line)}'"
                            " must be of type string"
                        ),
                        "definition": f".ifIncludeLines[{fpath}][{i}]",
                        "file": fpath,
                    }
                    return
                clean_line = line.strip("\r\n")
                if not clean_line:
                    yield InterruptingError, {
                        "message": "Expected line must not be empty",
                        "definition": f".ifIncludeLines[{fpath}][{i}]",
                        "file": fpath,
                    }
                    return
                elif clean_line in checked_lines:
                    yield InterruptingError, {
                        "message": f"Duplicated expected line '{clean_line}'",
                        "definition": f".ifIncludeLines[{fpath}][{i}]",
                        "file": fpath,
                    }
                    return

                if clean_line not in fcontent_lines:
                    yield ResultValue, False
                    return
                else:
                    checked_lines.append(clean_line)

    @staticmethod
    def excludeContent(value: t.List[str], tree: Tree, rule: Rule) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The contents to exclude must be of type array",
                "definition": ".excludeContent",
            }
            return
        elif not value:
            yield InterruptingError, {
                "message": "The contents to exclude must not be empty",
                "definition": ".excludeContent",
            }
            return

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "excludeContent",
                        fpath,
                        f".files[{f}]",
                    ),
                )
                continue

            # Normalize newlines
            checked_content = []
            for i, content in enumerate(value):
                if not isinstance(content, str):
                    yield InterruptingError, {
                        "message": (
                            "The content to exclude"
                            f" '{pprint.pformat(content)}'"
                            " must be of type string"
                        ),
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }
                    return
                elif not content:
                    yield InterruptingError, {
                        "message": "The content to exclude must not be empty",
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }
                    return
                elif content in checked_content:
                    yield InterruptingError, {
                        "message": f"Duplicated content to exclude '{content}'",
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }
                    return

                if content in fcontent:
                    yield Error, {
                        "message": (
                            f"Found expected content to exclude '{content}'"
                        ),
                        "file": fpath,
                        "definition": f".excludeContent[{i}]",
                    }
                else:
                    checked_content.append(content)
