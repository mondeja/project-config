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
    def _func_op(self, a: float, operator: str, b: float) -> bool:
        try:
            func = OPERATORS_FUNCTIONS[operator]
        except KeyError:
            raise jmespath.exceptions.JMESPathError(
                f"Invalid operator '{operator}' passed to op() function,"
                f" expected one of: {', '.join(list(OPERATORS_FUNCTIONS))}",
            )
        return func(a, b)  # type: ignore

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
            f" JMESPath {error_type}: {exc.__str__()}",
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
            f" JMESPath {error_type}: {exc.__str__()}",
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
            f" Raised JMESPath {error_type}: {exc.__str__()}",
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
            f" JMESPath {error_type}: {exc.__str__()}",
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
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": "A JMES path can not be applied to a directory",
                    "definition": f".ifJMESPathsMatch[{fpath}]",
                    "file": fpath,
                }
                continue

            instance = tree.serialize_file(fpath)

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
                "message": "The JMES path match tuples must be of type array",
                "definition": ".crossJMESPathsMatch",
            }
            return
        if not value:
            yield InterruptingError, {
                "message": "The JMES path match tuples must not be empty",
                "definition": ".crossJMESPathsMatch",
            }
            return
        for i, jmespath_match_tuple in enumerate(value):
            if not isinstance(jmespath_match_tuple, list):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of type array"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}]",
                }
                return
            if len(jmespath_match_tuple) != 2:
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of length 2"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}]",
                }
                return
            if not isinstance(jmespath_match_tuple[0], str):
                yield InterruptingError, {
                    "message": (
                        "The JMES path expression must be of type string"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}][0]",
                }
                return
            if not isinstance(jmespath_match_tuple[1], list):
                yield InterruptingError, {
                    "message": (
                        "The file and JMES path expression array from"
                        " which the expected value will be taken must"
                        " be of type array"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}][1]",
                }
                return
            if len(jmespath_match_tuple[1]) != 2:
                yield InterruptingError, {
                    "message": (
                        "The file and JMES path expression from which"
                        " the expected value will be taken must be of"
                        " length 2"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}][1]",
                }
                return
            if not isinstance(jmespath_match_tuple[1][0], str):
                yield InterruptingError, {
                    "message": (
                        "The file from which the expected value will be"
                        " taken must be of type string"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}][1][0]",
                }
                return
            if not isinstance(jmespath_match_tuple[1][1], str):
                yield InterruptingError, {
                    "message": (
                        "The JMES path expression to query the file"
                        " from which the expected value will be"
                        " taken must be of type string"
                    ),
                    "definition": f".crossJMESPathsMatch[{i}][1][1]",
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

            for e, (expression, expected_value_getter_tuple) in enumerate(
                value,
            ):
                ev_file, ev_expression = expected_value_getter_tuple

                # parse both expressions
                try:
                    ev_compiled_expression = _compile_JMESPath_or_expected_value_from_other_file_error(  # noqa: E501
                        ev_expression,
                        ev_file,
                        ev_expression,
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".crossJMESPathsMatch[{e}][1][1]",
                        "file": ev_file,
                    }
                    continue

                # obtain expected value
                try:
                    ev_instance = tree.serialize_file(ev_file)
                except FileNotFoundError as exc:
                    yield InterruptingError, {
                        "message": str(exc),
                        "definition": f".crossJMESPathsMatch[{f}][1][0]",
                        "file": ev_file,
                    }
                    continue

                try:
                    expected_value = _evaluate_JMESPath(
                        ev_compiled_expression,
                        ev_instance,
                    )
                except JMESPathError as exc:
                    yield Error, {
                        "message": exc.message,
                        "definition": f".crossJMESPathsMatch[{e}][1]",
                        "file": ev_file,
                    }
                    continue

                try:
                    compiled_expression = _compile_JMESPath_or_expected_value_from_other_file_error(  # noqa: E501
                        expression,
                        ev_file,
                        ev_expression,
                    )
                except JMESPathError as exc:
                    yield InterruptingError, {
                        "message": exc.message,
                        "definition": f".crossJMESPathsMatch[{e}][0]",
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
                        "definition": f".crossJMESPathsMatch[{e}]",
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
                        "definition": f".crossJMESPathsMatch[{e}]",
                        "file": fpath,
                    }
