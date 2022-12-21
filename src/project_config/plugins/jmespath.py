"""JMESPath expressions plugin."""

from __future__ import annotations

import copy
import json
import os
import pprint
import stat
from typing import TYPE_CHECKING, Any

from project_config import (
    ActionsContext,
    Error,
    InterruptingError,
    ResultValue,
    tree,
)


if TYPE_CHECKING:
    from project_config import Results, Rule

from project_config.fetchers import FetchError
from project_config.serializers import SerializerError
from project_config.utils.jmespath import (
    JMESPathError,
    compile_JMESPath_expression_or_error,
    compile_JMESPath_or_expected_value_error,
    compile_JMESPath_or_expected_value_from_other_file_error,
    evaluate_JMESPath,
    evaluate_JMESPath_or_expected_value_error,
    fix_tree_serialized_file_by_jmespath,
    is_literal_jmespath_expression,
    smart_fixer_by_expected_value,
)


class JMESPathPlugin:
    @staticmethod
    def JMESPathsMatch(
        value: list[list[Any]],
        rule: Rule,  # noqa: U100
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The JMES path match tuples must be of type array",
                "definition": ".JMESPathsMatch",
            }
        if not value:
            yield InterruptingError, {
                "message": "The JMES path match tuples must not be empty",
                "definition": ".JMESPathsMatch",
            }
        for i, jmespath_match_tuple in enumerate(value):
            if not isinstance(jmespath_match_tuple, list):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of type array"
                    ),
                    "definition": f".JMESPathsMatch[{i}]",
                }
            if len(jmespath_match_tuple) not in (2, 3):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of length 2 or 3"
                    ),
                    "definition": f".JMESPathsMatch[{i}]",
                }
            if not isinstance(jmespath_match_tuple[0], str):
                yield InterruptingError, {
                    "message": (
                        "The JMES path expression must be of type string"
                    ),
                    "definition": f".JMESPathsMatch[{i}][0]",
                }
            if len(jmespath_match_tuple) == 2:
                jmespath_match_tuple.append(None)
            else:
                if not isinstance(jmespath_match_tuple[2], str):
                    yield InterruptingError, {
                        "message": (
                            "The JMES path fixer query must be of type string"
                        ),
                        "definition": f".JMESPathsMatch[{i}][2]",
                    }

        files = copy.copy(context.files)
        for f, fpath in enumerate(files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(fstat.st_mode):
                yield InterruptingError, {
                    "message": (
                        "A JMES path can not be applied to a directory"
                    ),
                    "definition": f".files[{f}]",
                    "file": f'{fpath.rstrip("/")}/',
                }

            instance = tree.cached_local_file(fpath)

            for e, (expression, expected_value, fixer_query) in enumerate(
                value,
            ):
                try:
                    compiled_expression = (
                        compile_JMESPath_or_expected_value_error(
                            expression,
                            expected_value,
                        )
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".JMESPathsMatch[{e}][0]",
                        "file": fpath,
                    }

                try:
                    expression_result = (
                        evaluate_JMESPath_or_expected_value_error(
                            compiled_expression,
                            expected_value,
                            instance,
                        )
                    )
                except JMESPathError as exc:
                    yield Error, {
                        "message": exc.message,
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }
                    continue

                if expression_result != expected_value:
                    if not fixer_query:
                        fixer_query = smart_fixer_by_expected_value(
                            compiled_expression,
                            expected_value,
                        )
                    if context.fix and fixer_query:
                        try:
                            compiled_fixer_query = (
                                compile_JMESPath_expression_or_error(
                                    fixer_query,
                                )
                            )
                        except JMESPathError as exc:
                            yield InterruptingError, {
                                "message": exc.message,
                                "definition": f".JMESPathsMatch[{e}][2]",
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
                                "definition": f".JMESPathsMatch[{e}][2]",
                            }
                        else:
                            fixed = True
                            if not changed:  # pragma: no cover
                                continue
                    else:
                        fixed = False

                    yield Error, {
                        "message": (
                            f"JMESPath '{expression}' does not match."
                            f" Expected {pprint.pformat(expected_value)},"
                            f" returned {pprint.pformat(expression_result)}"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                        "fixed": fixed,
                        "fixable": bool(fixer_query),
                    }

    @staticmethod
    def ifJMESPathsMatch(
        value: dict[str, list[list[str]]],
        rule: Rule,  # noqa: U100
        context: ActionsContext,  # noqa: U100
    ) -> Results:
        if not isinstance(value, dict):
            yield InterruptingError, {
                "message": (
                    "The files - JMES path match tuples must be"
                    " of type object"
                ),
                "definition": ".ifJMESPathsMatch",
            }
        elif not value:
            yield InterruptingError, {
                "message": (
                    "The files - JMES path match tuples must not be empty"
                ),
                "definition": ".ifJMESPathsMatch",
            }
        for fpath, jmespath_match_tuples in value.items():
            if not isinstance(jmespath_match_tuples, list):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuples must be of type array"
                    ),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                }
            if not jmespath_match_tuples:
                yield InterruptingError, {
                    "message": ("The JMES path match tuples must not be empty"),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                }
            for i, jmespath_match_tuple in enumerate(jmespath_match_tuples):
                if not isinstance(jmespath_match_tuple, list):
                    yield InterruptingError, {
                        "message": (
                            "The JMES path match tuple must be of type array"
                        ),
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}]",
                    }
                if len(jmespath_match_tuple) != 2:
                    yield InterruptingError, {
                        "message": (
                            "The JMES path match tuple must be of length 2"
                        ),
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}]",
                    }
                if not isinstance(jmespath_match_tuple[0], str):
                    yield InterruptingError, {
                        "message": "The JMES path must be of type string",
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}][0]",
                    }

        for fpath, jmespath_match_tuples in value.items():
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                yield InterruptingError, {
                    "message": (
                        "The file to check if matches against JMES paths does"
                        " not exist"
                    ),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }
            if stat.S_ISDIR(fstat.st_mode):
                yield InterruptingError, {
                    "message": "A JMES path can not be applied to a directory",
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": f'{fpath.rstrip("/")}/',
                }

            try:
                instance = tree.cached_local_file(fpath)
            except SerializerError as exc:
                yield InterruptingError, {
                    "message": exc.message,
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }

            for e, (expression, expected_value) in enumerate(
                jmespath_match_tuples,
            ):
                try:
                    compiled_expression = (
                        compile_JMESPath_or_expected_value_error(
                            expression,
                            expected_value,
                        )
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".ifJMESPathsMatch[{fpath}][{e}][0]",
                        "file": fpath,
                    }

                try:
                    expression_result = (
                        evaluate_JMESPath_or_expected_value_error(
                            compiled_expression,
                            expected_value,
                            instance,
                        )
                    )
                except JMESPathError as exc:
                    yield Error, {
                        "message": exc.message,
                        "definition": f".ifJMESPathsMatch[{fpath}][{e}]",
                        "file": fpath,
                    }
                    continue

                if expression_result != expected_value:
                    yield ResultValue, False
                    return

        yield ResultValue, True

    @staticmethod
    def crossJMESPathsMatch(
        value: list[list[Any]],
        rule: Rule,  # noqa: U100
        context: ActionsContext,  # noqa: U100
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The pipes must be of type array",
                "definition": ".crossJMESPathsMatch",
            }
        if not value:
            yield InterruptingError, {
                "message": "The pipes must not be empty",
                "definition": ".crossJMESPathsMatch",
            }

        # each pipe is evaluated for each file
        for f, fpath in enumerate(context.files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(fstat.st_mode):
                yield InterruptingError, {
                    "message": (
                        "A JMES path can not be applied to a directory"
                    ),
                    "definition": f".files[{f}]",
                    "file": f'{fpath.rstrip("/")}/',
                }

            for i, pipe in enumerate(value):
                if not isinstance(pipe, list):
                    yield InterruptingError, {
                        "message": "The pipe must be of type array",
                        "definition": f".crossJMESPathsMatch[{i}]",
                    }
                elif len(pipe) < 3:
                    yield InterruptingError, {
                        "message": "The pipe must be, at least, of length 3",
                        "definition": f".crossJMESPathsMatch[{i}]",
                    }

                files_expression = pipe[0]

                # the first value in the array is the expression for `files`
                if not isinstance(files_expression, str):
                    yield InterruptingError, {
                        "message": "The file expression must be of type string",
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                    }
                elif not files_expression:
                    yield InterruptingError, {
                        "message": "The file expression must not be empty",
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                    }
                else:
                    files_expression = files_expression.strip()

                final_expression = pipe[-2]
                if not isinstance(final_expression, str):
                    yield InterruptingError, {
                        "message": (
                            "The final expression must be of type string"
                        ),
                        "definition": (
                            f".crossJMESPathsMatch[{i}][{len(pipe) - 2}]"
                        ),
                    }
                elif not final_expression:
                    yield InterruptingError, {
                        "message": "The final expression must not be empty",
                        "definition": (
                            f".crossJMESPathsMatch[{i}][{len(pipe) - 2}]"
                        ),
                    }

                expected_value = pipe[-1]

                try:
                    final_compiled_expression = (
                        compile_JMESPath_or_expected_value_error(  # noqa: E501
                            final_expression,
                            expected_value,
                        )
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": (
                            f".crossJMESPathsMatch[{i}][{len(pipe) - 2}]"
                        ),
                        "file": fpath,
                    }

                if is_literal_jmespath_expression(files_expression):
                    files_result = json.loads(files_expression[1:-1])
                else:
                    files_instance = tree.cached_local_file(fpath)

                    try:
                        files_compiled_expression = (
                            compile_JMESPath_expression_or_error(  # noqa: E501
                                files_expression,
                            )
                        )
                    except JMESPathError as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": f".crossJMESPathsMatch[{i}][0]",
                        }

                    try:
                        files_result = evaluate_JMESPath(
                            files_compiled_expression,
                            files_instance,
                        )
                    except JMESPathError as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": f".crossJMESPathsMatch[{i}][0]",
                            "file": fpath,
                        }

                other_results = []

                for other_index, other_data in enumerate(pipe[1:-2]):
                    pipe_index = other_index + 1

                    if not isinstance(other_data, list):
                        yield InterruptingError, {
                            "message": (
                                "The file path and expression tuple must be of"
                                " type array"
                            ),
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}]"
                            ),
                        }
                    elif len(other_data) != 2:
                        yield InterruptingError, {
                            "message": (
                                "The file path and expression tuple must be of"
                                " length 2"
                            ),
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}]"
                            ),
                        }

                    other_fpath, other_expression = other_data

                    if not isinstance(other_fpath, str):
                        yield InterruptingError, {
                            "message": "The file path must be of type string",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                        }
                    elif not other_fpath:
                        yield InterruptingError, {
                            "message": "The file path must not be empty",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                        }

                    if not isinstance(other_expression, str):
                        yield InterruptingError, {
                            "message": "The expression must be of type string",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][1]"
                            ),
                        }
                    elif not other_expression:
                        yield InterruptingError, {
                            "message": "The expression must not be empty",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][1]"
                            ),
                        }

                    try:
                        other_compiled_expression = compile_JMESPath_or_expected_value_from_other_file_error(  # noqa: E501
                            other_expression,
                            other_fpath,
                            other_expression,
                        )
                    except JMESPathError as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}]"
                            ),
                            "file": other_fpath,
                        }

                    try:
                        other_instance = tree.fetch_remote_file(other_fpath)
                    except (SerializerError, FetchError) as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                            "file": other_fpath,
                        }
                    except FileNotFoundError:
                        yield InterruptingError, {
                            "message": f"'{other_fpath}' file not found",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                            "file": other_fpath,
                        }

                    try:
                        other_result = evaluate_JMESPath(
                            other_compiled_expression,
                            other_instance,
                        )
                    except JMESPathError as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}]"
                            ),
                            "file": other_fpath,
                        }
                    else:
                        other_results.append(other_result)

                try:
                    final_result = evaluate_JMESPath(
                        final_compiled_expression,
                        [files_result, *other_results],
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": (
                            f".crossJMESPathsMatch[{i}][{len(pipe) - 2}]"
                        ),
                        "file": fpath,
                    }

                if final_result != expected_value:
                    yield Error, {
                        "message": (
                            f"JMESPath '{final_expression}' does not match."
                            f" Expected {pprint.pformat(expected_value)},"
                            f" returned {pprint.pformat(final_result)}"
                        ),
                        "definition": f".crossJMESPathsMatch[{i}]",
                        "file": fpath,
                    }
