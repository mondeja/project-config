"""Inclusions checker plugin."""

from __future__ import annotations

import os
import pprint
import stat
from typing import TYPE_CHECKING

from project_config import (
    ActionsContext,
    Error,
    InterruptingError,
    ResultValue,
    tree,
)
from project_config.utils.jmespath import (
    JMESPathError,
    compile_JMESPath_expression_or_error,
    fix_tree_serialized_file_by_jmespath,
)


if TYPE_CHECKING:
    from project_config import Results, Rule
    from project_config.types import ErrorDict


def _directories_not_accepted_as_inputs_error(
    action_type: str,
    action_name: str,
    dir_path: str,
    definition: str,
) -> ErrorDict:
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
        value: list[str],
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The value must be of type array",
                "definition": ".includeLines",
            }
        elif not value:
            yield InterruptingError, {
                "message": "The value must not be empty",
                "definition": ".includeLines",
            }

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

            elif not isinstance(line, str):
                yield InterruptingError, {
                    "message": (
                        f"The expected line '{pprint.pformat(line)}'"
                        " must be of type string or array"
                    ),
                    "definition": f".includeLines[{i}]",
                }
            clean_line = line.strip("\r\n")
            if clean_line in expected_lines:
                yield InterruptingError, {
                    "message": f"Duplicated expected line '{clean_line}'",
                    "definition": f".includeLines[{i}]",
                }
            elif not clean_line:
                yield InterruptingError, {
                    "message": "Expected line must not be empty",
                    "definition": f".includeLines[{i}]",
                }
            expected_lines.append(clean_line)

        for f, fpath in enumerate(context.files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(fstat.st_mode):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "includeLines",
                        fpath,
                        f".files[{f}]",
                    ),
                )

            fcontent_lines = tree.cached_local_file(fpath)
            for line_index, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    if context.fix:
                        instance = tree.cached_local_file(
                            fpath,
                            serializer="text",
                        )

                        if not fixer_query:
                            instance.append(expected_line)
                            tree.edit_local_file(fpath, instance)
                            fixed = True
                        else:
                            try:
                                compiled_fixer_query = (
                                    compile_JMESPath_expression_or_error(
                                        fixer_query,
                                    )
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": (
                                        f".includeLines[{line_index}]"
                                    ),
                                }

                            try:
                                changed = fix_tree_serialized_file_by_jmespath(
                                    compiled_fixer_query,
                                    instance,
                                    fpath,
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": (
                                        f".includeLines[{line_index}]"
                                    ),
                                }
                            else:
                                fixed = True
                                if not changed:  # pragma: no cover
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
        value: dict[str, list[str]],
        rule: Rule,  # noqa: U100
        context: ActionsContext,  # noqa: U100
    ) -> Results:
        if not isinstance(value, dict):
            yield InterruptingError, {
                "message": "The value must be of type object",
                "definition": ".ifIncludeLines",
            }
        elif not value:
            yield InterruptingError, {
                "message": "The value must not be empty",
                "definition": ".ifIncludeLines",
            }

        for fpath, expected_lines in value.items():
            if not fpath:
                yield InterruptingError, {
                    "message": "File paths must not be empty",
                    "definition": ".ifIncludeLines",
                }

            if not isinstance(expected_lines, list):
                yield InterruptingError, {
                    "message": (
                        f"The expected lines '{pprint.pformat(expected_lines)}'"
                        " must be of type array"
                    ),
                    "definition": f".ifIncludeLines[{fpath}]",
                }
            elif not expected_lines:
                yield InterruptingError, {
                    "message": "Expected lines must not be empty",
                    "definition": f".ifIncludeLines[{fpath}]",
                }

            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                yield InterruptingError, {
                    "message": (
                        "File specified in conditional 'ifIncludeLines'"
                        " not found"
                    ),
                    "file": fpath,
                    "definition": f".ifIncludeLines[{fpath}]",
                }
            if stat.S_ISDIR(fstat.st_mode):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "conditional",
                        "ifIncludeLines",
                        fpath,
                        f".ifIncludeLines[{fpath}]",
                    ),
                )

            fcontent_lines = tree.cached_local_file(
                fpath,
                serializer="text",
            )
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
                clean_line = line.strip("\r\n")
                if not clean_line:
                    yield InterruptingError, {
                        "message": "Expected line must not be empty",
                        "definition": f".ifIncludeLines[{fpath}][{i}]",
                        "file": fpath,
                    }
                elif clean_line in checked_lines:
                    yield InterruptingError, {
                        "message": f"Duplicated expected line '{clean_line}'",
                        "definition": f".ifIncludeLines[{fpath}][{i}]",
                        "file": fpath,
                    }

                if clean_line not in fcontent_lines:
                    yield ResultValue, False
                else:
                    checked_lines.append(clean_line)

    @staticmethod
    def excludeLines(
        value: list[str],
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The value must be of type array",
                "definition": ".excludeLines",
            }
        elif not value:
            yield InterruptingError, {
                "message": "The value must not be empty",
                "definition": ".excludeLines",
            }

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
                        "definition": f".excludeLines[{i}]",
                    }

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
                        "definition": f".excludeLines[{i}]",
                    }

            elif not isinstance(line, str):
                yield InterruptingError, {
                    "message": (
                        f"The expected line '{pprint.pformat(line)}'"
                        " must be of type string or array"
                    ),
                    "definition": f".excludeLines[{i}]",
                }
            clean_line = line.strip("\r\n")
            if clean_line in expected_lines:
                yield InterruptingError, {
                    "message": f"Duplicated expected line '{clean_line}'",
                    "definition": f".excludeLines[{i}]",
                }
            elif not clean_line:
                yield InterruptingError, {
                    "message": "Expected line must not be empty",
                    "definition": f".excludeLines[{i}]",
                }
            expected_lines.append(clean_line)

        for f, fpath in enumerate(context.files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(fstat.st_mode):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "excludeLines",
                        fpath,
                        f".files[{f}]",
                    ),
                )

            fcontent_lines = tree.cached_local_file(fpath)
            for line_index, expected_line in enumerate(expected_lines):
                if expected_line in fcontent_lines:
                    if context.fix:
                        instance = tree.cached_local_file(
                            fpath,
                            serializer="text",
                        )

                        if not fixer_query:
                            instance.remove(expected_line)
                            tree.edit_local_file(fpath, instance)
                            fixed = True
                        else:
                            try:
                                compiled_fixer_query = (
                                    compile_JMESPath_expression_or_error(
                                        fixer_query,
                                    )
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": (
                                        f".excludeLines[{line_index}]"
                                    ),
                                }

                            try:
                                changed = fix_tree_serialized_file_by_jmespath(
                                    compiled_fixer_query,
                                    instance,
                                    fpath,
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": (
                                        f".excludeLines[{line_index}]"
                                    ),
                                }
                            else:
                                fixed = True
                                if not changed:  # pragma: no cover
                                    continue
                    else:
                        fixed = False

                    yield Error, {
                        "message": (
                            f"Found expected line to exclude '{expected_line}'"
                        ),
                        "file": fpath,
                        "definition": f".excludeLines[{line_index}]",
                        "fixed": fixed,
                        "fixable": True,
                    }

    @staticmethod
    def includeContent(
        value: list[str],
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The contents to include must be of type array",
                "definition": ".includeContent",
            }
        elif not value:
            yield InterruptingError, {
                "message": "The contents to include must not be empty",
                "definition": ".includeContent",
            }

        for f, fpath in enumerate(context.files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue

            if stat.S_ISDIR(fstat.st_mode):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "includeContent",
                        fpath,
                        f".files[{f}]",
                    ),
                )

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
                                    "The '[content-to-include, fixer_query]'"
                                    f" array  items '{content_query}'"
                                    " must be of type string"
                                ),
                                "definition": f".includeContent[{i}]",
                            }
                else:
                    yield InterruptingError, {
                        "message": (
                            "The content to include"
                            f" '{pprint.pformat(content)}'"
                            " must be of type string or array"
                        ),
                        "definition": f".includeContent[{i}]",
                        "file": fpath,
                    }

                if not content:
                    yield InterruptingError, {
                        "message": "The content to include must not be empty",
                        "definition": f".includeContent[{i}]",
                        "file": fpath,
                    }
                elif content in checked_content:
                    yield InterruptingError, {
                        "message": f"Duplicated content to include '{content}'",
                        "definition": f".includeContent[{i}]",
                        "file": fpath,
                    }

                fcontent = tree.cached_local_file(fpath, serializer="_plain")
                if content not in fcontent:
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
                                    "definition": f".includeContent[{i}]",
                                }

                            instance = tree.cached_local_file(
                                fpath,
                                serializer="text",
                            )

                            try:
                                changed = fix_tree_serialized_file_by_jmespath(
                                    compiled_fixer_query,
                                    instance,
                                    fpath,
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": f".includeContent[{i}]",
                                }
                            else:
                                fixed = True
                                if not changed:  # pragma: no cover
                                    continue
                    else:
                        fixed = False
                        fixable = False
                    yield Error, {
                        "message": (
                            f"Content '{content}' expected to be"
                            " included not found"
                        ),
                        "file": fpath,
                        "definition": f".includeContent[{i}]",
                        "fixed": fixed,
                        "fixable": fixable,
                    }
                else:
                    checked_content.append(content)

    @staticmethod
    def excludeContent(
        value: list[str],
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The contents to exclude must be of type array",
                "definition": ".excludeContent",
            }
        elif not value:
            yield InterruptingError, {
                "message": "The contents to exclude must not be empty",
                "definition": ".excludeContent",
            }

        for f, fpath in enumerate(context.files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue

            if stat.S_ISDIR(fstat.st_mode):
                yield (
                    InterruptingError,
                    _directories_not_accepted_as_inputs_error(
                        "verb",
                        "excludeContent",
                        fpath,
                        f".files[{f}]",
                    ),
                )

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

                if not content:
                    yield InterruptingError, {
                        "message": "The content to exclude must not be empty",
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }
                elif content in checked_content:
                    yield InterruptingError, {
                        "message": f"Duplicated content to exclude '{content}'",
                        "definition": f".excludeContent[{i}]",
                        "file": fpath,
                    }

                fcontent = tree.cached_local_file(fpath, serializer="_plain")
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

                            instance = tree.cached_local_file(
                                fpath,
                                serializer="text",
                            )

                            try:
                                changed = fix_tree_serialized_file_by_jmespath(
                                    compiled_fixer_query,
                                    instance,
                                    fpath,
                                )
                            except JMESPathError as exc:
                                yield InterruptingError, {
                                    "message": exc.message,
                                    "definition": f".excludeContent[{i}]",
                                }
                            else:
                                fixed = True
                                if not changed:  # pragma: no cover
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
