"""JMESPath expressions plugin."""

import operator
import pprint
import re
import shlex
import typing as t
import warnings

import jmespath

from project_config import (
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)
from project_config.compat import cached_function, shlex_join
from project_config.exceptions import ProjectConfigException
from project_config.fetchers import FetchError
from project_config.serializers import SerializerError


ALL_JMESPATH_FUNCTION_TYPES = list(jmespath.functions.REVERSE_TYPES_MAP.keys())

OPERATORS_FUNCTIONS = {
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
    "is": operator.is_,
    "is_not": operator.is_not,
    "is-not": operator.is_not,
    "is not": operator.is_not,
    "isNot": operator.is_not,
    "+": operator.add,
    "&": operator.and_,
    "and": operator.and_,
    "//": operator.floordiv,
    "<<": operator.lshift,
    "%": operator.mod,
    "*": operator.mul,
    "@": operator.matmul,
    "|": operator.or_,
    "or": operator.or_,
    "**": operator.pow,
    ">>": operator.rshift,
    "-": operator.sub,
    "/": operator.truediv,
    "^": operator.xor,
    "count_of": operator.countOf,
    "count of": operator.countOf,
    "count-of": operator.countOf,
    "countOf": operator.countOf,
    "index_of": operator.indexOf,
    "index of": operator.indexOf,
    "index-of": operator.indexOf,
    "indexOf": operator.indexOf,
}

SET_OPERATORS = {"<", ">", "<=", ">=", "and", "&", "or", "|", "-", "^"}
SET_OPERATORS_THAT_RETURN_SET = {"and", "&", "or", "|", "-", "^"}

# map from jmespath exceptions class names to readable error types
JMESPATH_READABLE_ERRORS = {
    "ParserError": "parsing error",
    "IncompleteExpressionError": "incomplete expression error",
    "LexerError": "lexing error",
    "ArityError": "arity error",
    "VariadictArityError": "arity error",
    "JMESPathTypeError": "type error",
    "EmptyExpressionError": "empty expression error",
    "UnknownFunctionError": "unknown function error",
}


class JMESPathProjectConfigFunctions(
    jmespath.functions.Functions,  # type: ignore
):
    """JMESPath class to include custom functions."""

    @jmespath.functions.signature(  # type: ignore
        {"types": ["string"]},
        {"types": ["string"]},
    )
    def _func_regex_match(self, regex: str, value: str) -> bool:
        return bool(re.match(regex, value))

    @jmespath.functions.signature(  # type: ignore
        {"types": ["string"]},
        {"types": ["array", "object"]},
    )
    def _func_regex_matchall(self, regex: str, container: str) -> bool:
        warnings.warn(
            "The JMESPath function 'regex_matchall' is deprecated and"
            " will be removed in 1.0.0. Use 'regex_match' as child"
            " elements of subexpression filtering the output. See"
            " https://github.com/mondeja/project-config/issues/69 for"
            " a more detailed explanation.",
            DeprecationWarning,
            stacklevel=2,
        )
        return all(bool(re.match(regex, value)) for value in container)

    @jmespath.functions.signature(  # type: ignore
        {"types": ["string"]},
        {"types": ["string"]},
    )
    def _func_regex_search(self, regex: str, value: str) -> t.List[str]:
        match = re.search(regex, value)
        if not match:
            return []
        return [match.group(0)] if not match.groups() else list(match.groups())

    @jmespath.functions.signature(  # type: ignore
        {"types": ALL_JMESPATH_FUNCTION_TYPES},
        {"types": ["string"]},
        {"types": ALL_JMESPATH_FUNCTION_TYPES},
    )
    def _func_op(self, a: float, operator: str, b: float) -> t.Any:
        try:
            func = OPERATORS_FUNCTIONS[operator]
        except KeyError:
            raise jmespath.exceptions.JMESPathError(
                f"Invalid operator '{operator}' passed to op() function,"
                f" expected one of: {', '.join(list(OPERATORS_FUNCTIONS))}",
            )
        if (
            isinstance(b, list)
            and isinstance(a, list)
            and operator in SET_OPERATORS
        ):
            # both values are lists and the operator is only valid for sets,
            # so convert both values to set applying the operator
            b, a = set(b), set(a)
            if operator in SET_OPERATORS_THAT_RETURN_SET:
                return list(func(a, b))
        return func(a, b)

    @jmespath.functions.signature({"types": ["array"]})  # type: ignore
    def _func_shlex_join(self, cmd_list: t.List[str]) -> str:
        return shlex_join(cmd_list)

    @jmespath.functions.signature({"types": ["string"]})  # type: ignore
    def _func_shlex_split(self, cmd_str: str) -> t.List[str]:
        return shlex.split(cmd_str)


jmespath_options = jmespath.Options(
    custom_functions=JMESPathProjectConfigFunctions(),
)


class JMESPathError(ProjectConfigException):
    """Class to wrap all JMESPath errors of the plugin."""


@cached_function
def _compile_JMESPath_expression(
    expression: str,
) -> jmespath.parser.ParsedResult:
    return jmespath.compile(expression)


def _compile_JMESPath_expression_or_error(
    expression: str,
) -> jmespath.parser.ParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
    except jmespath.exceptions.JMESPathError as exc:
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath expression {pprint.pformat(expression)}."
            f" Raised JMESPath {error_type}: {str(exc)}",
        )


def _compile_JMESPath_or_expected_value_error(
    expression: str,
    expected_value: t.Any,
) -> jmespath.parser.ParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
    except jmespath.exceptions.JMESPathError as exc:
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath expression {pprint.pformat(expression)}."
            f" Expected to return {pprint.pformat(expected_value)}, raised"
            f" JMESPath {error_type}: {str(exc)}",
        )


def _compile_JMESPath_or_expected_value_from_other_file_error(
    expression: str,
    expected_value_file: str,
    expected_value_expression: str,
) -> jmespath.parser.ParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
    except jmespath.exceptions.JMESPathError as exc:
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath expression {pprint.pformat(expression)}."
            f" Expected to return from applying the expresion"
            f" {pprint.pformat(expected_value_expression)} to the file"
            f" {pprint.pformat(expected_value_file)}, raised"
            f" JMESPath {error_type}: {str(exc)}",
        )


def _evaluate_JMESPath(
    compiled_expression: jmespath.parser.ParsedResult,
    instance: t.Any,
) -> t.Any:
    try:
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )
    except jmespath.exceptions.JMESPathError as exc:
        formatted_expression = pprint.pformat(compiled_expression.expression)
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath {formatted_expression}."
            f" Raised JMESPath {error_type}: {str(exc)}",
        )


def _evaluate_JMESPath_or_expected_value_error(
    compiled_expression: jmespath.parser.ParsedResult,
    expected_value: t.Any,
    instance: t.Dict[str, t.Any],
) -> t.Any:
    try:
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )
    except jmespath.exceptions.JMESPathError as exc:
        formatted_expression = pprint.pformat(compiled_expression.expression)
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath {formatted_expression}."
            f" Expected to return {pprint.pformat(expected_value)}, raised"
            f" JMESPath {error_type}: {str(exc)}",
        )


class JMESPathPlugin:
    @staticmethod
    def JMESPathsMatch(
        value: t.List[t.List[t.Any]],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": ("The JMES path match tuples must be of type array"),
                "definition": ".JMESPathsMatch",
            }
            return
        if not value:
            yield InterruptingError, {
                "message": "The JMES path match tuples must not be empty",
                "definition": ".JMESPathsMatch",
            }
            return
        for i, jmespath_match_tuple in enumerate(value):
            if not isinstance(jmespath_match_tuple, list):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of type array"
                    ),
                    "definition": f".JMESPathsMatch[{i}]",
                }
                return
            if len(jmespath_match_tuple) != 2:
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of length 2"
                    ),
                    "definition": f".JMESPathsMatch[{i}]",
                }
                return
            if not isinstance(jmespath_match_tuple[0], str):
                yield InterruptingError, {
                    "message": (
                        "The JMES path expression must be of type string"
                    ),
                    "definition": f".JMESPathsMatch[{i}][0]",
                }
                return

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": (
                        "A JMES path can not be applied to a directory"
                    ),
                    "definition": f".files[{f}]",
                    "file": fpath,
                }
                continue

            instance = tree.serialize_file(fpath)

            for e, (expression, expected_value) in enumerate(value):
                try:
                    compiled_expression = (
                        _compile_JMESPath_or_expected_value_error(
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
                    continue

                try:
                    expression_result = (
                        _evaluate_JMESPath_or_expected_value_error(
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
                    yield Error, {
                        "message": (
                            f"JMESPath '{expression}' does not match."
                            f" Expected {pprint.pformat(expected_value)},"
                            f" returned {pprint.pformat(expression_result)}"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }

    @staticmethod
    def ifJMESPathsMatch(
        value: t.Dict[str, t.List[t.List[str]]],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, dict):
            yield InterruptingError, {
                "message": (
                    "The files - JMES path match tuples must be"
                    " of type object"
                ),
                "definition": ".ifJMESPathsMatch",
            }
            return
        elif not value:
            yield InterruptingError, {
                "message": (
                    "The files - JMES path match tuples must not be empty"
                ),
                "definition": ".ifJMESPathsMatch",
            }
            return
        for fpath, jmespath_match_tuples in value.items():
            if not isinstance(jmespath_match_tuples, list):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuples must be of type array"
                    ),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                }
                return
            if not jmespath_match_tuples:
                yield InterruptingError, {
                    "message": ("The JMES path match tuples must not be empty"),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                }
                return
            for i, jmespath_match_tuple in enumerate(jmespath_match_tuples):
                if not isinstance(jmespath_match_tuple, list):
                    yield InterruptingError, {
                        "message": (
                            "The JMES path match tuple must be of type array"
                        ),
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}]",
                    }
                    return
                if len(jmespath_match_tuple) != 2:
                    yield InterruptingError, {
                        "message": (
                            "The JMES path match tuple must be of length 2"
                        ),
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}]",
                    }
                    return
                if not isinstance(jmespath_match_tuple[0], str):
                    yield InterruptingError, {
                        "message": "The JMES path must be of type string",
                        "definition": f".ifJMESPathsMatch[{fpath}][{i}][0]",
                    }
                    return

        for fpath, jmespath_match_tuples in value.items():
            fcontent = tree.get_file_content(fpath)
            if fcontent is None:
                yield InterruptingError, {
                    "message": (
                        "The file to check if matches against JMES paths does"
                        " not exist"
                    ),
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": "A JMES path can not be applied to a directory",
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }
                continue

            try:
                instance = tree.serialize_file(fpath)
            except SerializerError as exc:
                yield InterruptingError, {
                    "message": exc.message,
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }
                continue

            for e, (expression, expected_value) in enumerate(
                jmespath_match_tuples,
            ):
                try:
                    compiled_expression = (
                        _compile_JMESPath_or_expected_value_error(
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
                    continue

                try:
                    expression_result = (
                        _evaluate_JMESPath_or_expected_value_error(
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
        value: t.List[t.List[t.Any]],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The pipes must be of type array",
                "definition": ".crossJMESPathsMatch",
            }
            return
        if not value:
            yield InterruptingError, {
                "message": "The pipes must not be empty",
                "definition": ".crossJMESPathsMatch",
            }
            return

        # each pipe is evaluated for each file
        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": (
                        "A JMES path can not be applied to a directory"
                    ),
                    "definition": f".files[{f}]",
                    "file": fpath,
                }
                continue

            for i, pipe in enumerate(value):
                if not isinstance(pipe, list):
                    yield InterruptingError, {
                        "message": "The pipe must be of type array",
                        "definition": f".crossJMESPathsMatch[{i}]",
                    }
                    return
                elif len(pipe) < 3:
                    yield InterruptingError, {
                        "message": "The pipe must be, at least, of length 3",
                        "definition": f".crossJMESPathsMatch[{i}]",
                    }
                    return

                files_expression = pipe[0]

                # the first value in the array is the expression for `files`
                if not isinstance(files_expression, str):
                    yield InterruptingError, {
                        "message": "The file expression must be of type string",
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                    }
                    return
                elif not files_expression:
                    yield InterruptingError, {
                        "message": "The file expression must not be empty",
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                    }
                    return

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
                    return
                elif not final_expression:
                    yield InterruptingError, {
                        "message": "The final expression must not be empty",
                        "definition": (
                            f".crossJMESPathsMatch[{i}][{len(pipe) - 2}]"
                        ),
                    }
                    return

                expected_value = pipe[-1]

                try:
                    final_compiled_expression = (
                        _compile_JMESPath_or_expected_value_error(  # noqa: E501
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
                    continue

                files_instance = tree.serialize_file(fpath)

                try:
                    files_compiled_expression = (
                        _compile_JMESPath_expression_or_error(  # noqa: E501
                            files_expression,
                        )
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                    }
                    continue

                try:
                    files_result = _evaluate_JMESPath(
                        files_compiled_expression,
                        files_instance,
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".crossJMESPathsMatch[{i}][0]",
                        "file": fpath,
                    }
                    continue

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
                        return
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
                        return

                    other_fpath, other_expression = other_data

                    if not isinstance(other_fpath, str):
                        yield InterruptingError, {
                            "message": "The file path must be of type string",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                        }
                        return
                    elif not other_fpath:
                        yield InterruptingError, {
                            "message": "The file path must not be empty",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                        }
                        return

                    if not isinstance(other_expression, str):
                        yield InterruptingError, {
                            "message": "The expression must be of type string",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][1]"
                            ),
                        }
                        return
                    elif not other_expression:
                        yield InterruptingError, {
                            "message": "The expression must not be empty",
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][1]"
                            ),
                        }
                        return

                    try:
                        other_compiled_expression = _compile_JMESPath_or_expected_value_from_other_file_error(  # noqa: E501
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
                        return

                    try:
                        other_instance = tree.fetch_file(other_fpath)
                    except FetchError as exc:
                        yield InterruptingError, {
                            "message": exc.message,
                            "definition": (
                                f".crossJMESPathsMatch[{i}][{pipe_index}][0]"
                            ),
                            "file": other_fpath,
                        }
                        return

                    try:
                        other_result = _evaluate_JMESPath(
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
                        return
                    else:
                        other_results.append(other_result)

                try:
                    final_result = _evaluate_JMESPath(
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
                    return

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
