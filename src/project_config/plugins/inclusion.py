"""Inclusions checker plugin."""

from __future__ import annotations

import os
import pprint
import typing as t

from project_config import (
    ActionsContext,
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)
from project_config.utils.jmespath import (
    JMESPathError,
    compile_JMESPath_expression_or_error,
    fix_tree_serialized_file_by_jmespath,
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
        rule: Rule,  # noqa: U100
        context: ActionsContext,
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
            fixer_query = ""

            if isinstance(line, list):
                # Fixer query expression
                if len(line) != 2:
                    yield InterruptingError, {
                        "message": (
                            "The '[expected-line, fixer_query]' array"
                            f" '{pprint.pformat(line)}'"
                            " must be of length 2"
                        ),
                        "definition": f".includeLines[{i}]",
                    }
                    return

                line, fixer_query = line

                if not isinstance(line, str) or not isinstance(
                    fixer_query,
                    str,
                ):
                    yield InterruptingError, {
                        "message": (
                            "The '[expected-line, fixer_query]' array items"
                            f" '{pprint.pformat([line, fixer_query])}'"
                            " must be of type string"
                        ),
                        "definition": f".includeLines[{i}]",
                    }
                    return

            elif not isinstance(line, str):
                yield InterruptingError, {
                    "message": (
                        f"The expected line '{pprint.pformat(line)}'"
                        " must be of type string or array"
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
                    if context.fix:
                        if not fixer_query:
                            fixer_query = f"insert(@, `-1`, '{expected_line}')"

                        try:
                            compiled_fixer_query = (
                                compile_JMESPath_expression_or_error(
                                    fixer_query,
                                )
                            )
                        except JMESPathError as exc:
                            yield InterruptingError, {
                                "message": exc.message,
                                "definition": f".includeLines[{line_index}]",
                            }
                            continue

                        _, instance = tree.serialize_file(fpath)

                        try:
                            diff = fix_tree_serialized_file_by_jmespath(
                                compiled_fixer_query,
                                instance,
                                fpath,
                                tree,
                            )
                        except JMESPathError as exc:
                            yield InterruptingError, {
                                "message": exc.message,
                                "definition": f".includeLines[{line_index}]",
                            }
                            continue
                        else:
                            fixed = True
                            if not diff:
                                continue
                    else:
                        fixed = False

                    yield Error, {
                        "message": f"Expected line '{expected_line}' not found",
                        "file": fpath,
                        "definition": f".includeLines[{line_index}]",
                        "fixed": fixed,
                        "fixable": True,
                    }

    @staticmethod
    def ifIncludeLines(
        value: t.Dict[str, t.List[str]],
        tree: Tree,
        rule: Rule,  # noqa: U100
        context: ActionsContext,  # noqa: U100
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
    def excludeContent(
        value: t.List[str],
        tree: Tree,
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        # TODO: allow to fix this rule passing a JMESPath as plain text
        #   (content as string)
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
                fixer_query = ""
                if isinstance(content, str) or isinstance(content, list):
                    if isinstance(content, list):
                        content, fixer_query = content

                        if not isinstance(content, str) or not isinstance(
                            fixer_query,
                            str,
                        ):
                            content_query = pprint.pformat(
                                [content, fixer_query],
                            )
                            yield InterruptingError, {
                                "message": (
                                    "The '[content-to-exclude, fixer_query]'"
                                    f" array  items '{content_query}'"
                                    " must be of type string"
                                ),
                                "definition": f".excludeContent[{i}]",
                            }
                            return
                else:
                    yield InterruptingError, {
                        "message": (
                            "The content to exclude"
                            f" '{pprint.pformat(content)}'"
                            " must be of type string or array"
                        ),
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }
                    return

                if not content:
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
                    if fixer_query:
                        fixable = True
                        fixed = False
                        if context.fix:
                            try:
                                compiled_fixer_query = (
                                    compile_JMESPath_expression_or_error(
                                        fixer_query,
                                    )
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": f".excludeContent[{i}]",
                                }
                                return

                            _, instance = tree.serialize_file(fpath)

                            try:
                                diff = fix_tree_serialized_file_by_jmespath(
                                    compiled_fixer_query,
                                    instance,
                                    fpath,
                                    tree,
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": f".excludeContent[{i}]",
                                }
                                return
                            else:
                                fixed = True
                                if not diff:
                                    continue
                    else:
                        fixed = False
                        fixable = False
                    yield Error, {
                        "message": (
                            f"Found expected content to exclude '{content}'"
                        ),
                        "file": fpath,
                        "definition": f".excludeContent[{i}]",
                        "fixed": fixed,
                        "fixable": fixable,
                    }
                else:
                    checked_content.append(content)
