"""Utilities related to JMESPaths."""

from __future__ import annotations

import builtins
import glob
import json
import operator
import os
import pickle
import pprint
import re
import shlex
import shutil
import sys
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import deepmerge
from jmespath import Options as JMESPathOptions, compile as jmespath_compile
from jmespath.exceptions import (
    JMESPathError as OriginalJMESPathError,
    ParseError as JMESPathParserError,
)
from jmespath.functions import (
    Functions as JMESPathFunctions,
    signature as jmespath_func_signature,
)
from jmespath.parser import ParsedResult as JMESPathParsedResult, Parser

from project_config import tree
from project_config.cache import Cache
from project_config.compat import removeprefix, removesuffix, shlex_join
from project_config.exceptions import ProjectConfigException


if TYPE_CHECKING:
    from project_config.compat import Literal


class JMESPathError(ProjectConfigException):
    """Class to wrap all JMESPath errors of the plugin."""


BUILTIN_TYPES = ["str", "bool", "int", "float", "list", "dict", "set"]

BUILTIN_DEEPMERGE_STRATEGIES = {}
for maybe_merge_strategy_name in dir(deepmerge):
    if not maybe_merge_strategy_name.startswith("_"):
        maybe_merge_strategy_instance = getattr(
            deepmerge,
            maybe_merge_strategy_name,
        )
        if isinstance(maybe_merge_strategy_instance, deepmerge.Merger):
            BUILTIN_DEEPMERGE_STRATEGIES[
                maybe_merge_strategy_name
            ] = maybe_merge_strategy_instance

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
OPERATORS_THAT_RETURN_SET = {"and", "&", "or", "|", "-", "^"}

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

# JMESPath variables that can not be cached in evaluations
# as are not deterministic
UNCACHEABLE_JMESPATH_VARIABLES = {
    "rootdir",  # rootdir_name()
    "listdir",  # ...
    "isfile",
    "isdir",
    "exists",
    "mkdir",
    "rmdir",
    "glob",
    "getenv",
    # other useful
    "dirname",
    "basename",
    "extname",
}


def _create_simple_transform_function_for_string(
    func_name: str,
) -> Callable[[type, str], str]:
    func = getattr(str, func_name)
    return jmespath_func_signature({"types": ["string"]})(
        lambda self, value: func(value),
    )


def _create_is_function_for_string(
    func_suffix: str,
) -> Callable[[type, str], bool]:
    func = getattr(str, f"is{func_suffix}")
    return jmespath_func_signature({"types": ["string"]})(
        lambda self, value: func(value),
    )


def _create_find_function_for_string_or_array(
    func_prefix: str,
) -> Callable[[type, list[Any] | str, Any, Any], int]:
    getattr(str, f"{func_prefix}find")

    def _wrapper(
        self: type, value: list[Any] | str, sub: Any, *args: Any
    ) -> int:
        if isinstance(value, list):
            try:
                return value.index(sub, *args)
            except ValueError:
                return -1
        return value.find(sub, *args)

    return jmespath_func_signature(
        {"types": ["string", "array"], "variadic": True},
    )(_wrapper)


def _create_just_function_for_string(
    func_prefix: str,
) -> Callable[[type, str, int, Any], str]:
    func = getattr(str, f"{func_prefix}just")
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["number"], "variadic": True},
    )(lambda self, value, width, *args: func(value, width, *args))


def _create_partition_function_for_string(
    func_prefix: str,
) -> Callable[[type, str, str], list[str]]:
    func = getattr(str, f"{func_prefix}partition")
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
    )(lambda self, value, sep: list(func(value, sep)))


def _create_split_function_for_string(
    func_prefix: str,
) -> Callable[[type, str, Any], list[str]]:
    func = getattr(str, f"{func_prefix}split")
    return jmespath_func_signature(
        {"types": ["string"], "variadic": True},
    )(lambda self, value, *args: func(value, *args))


def _create_strip_function_for_string(
    func_prefix: str,
) -> Callable[[type, str], str]:
    func = getattr(str, f"{func_prefix}strip")
    return jmespath_func_signature(
        {"types": ["string"], "variadic": True},
    )(lambda self, value, *args: func(value, *args))


def _create_removeaffix_function_for_string(
    func_suffix: str,
) -> Callable[[type, str, str], str]:
    func = removesuffix if func_suffix.startswith("s") else removeprefix
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
    )(lambda self, value, affix: func(value, affix))


def _to_items(value: Any) -> list[Any]:
    return [[key, value] for key, value in value.items()]


class JMESPathProjectConfigFunctions(JMESPathFunctions):
    """JMESPath class to include custom functions."""

    # Functions that expands the functionality of the standard JMESPath
    # functions:

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string", "array-string"], "variadic": True},
    )
    def _func_starts_with(
        self, search: str, suffix: str | tuple[str], *args: Any
    ) -> bool:
        if isinstance(suffix, list):
            suffix = tuple(suffix)
        return search.startswith(suffix, *args)

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string", "array-string"], "variadic": True},
    )
    def _func_ends_with(
        self, search: str, suffix: str | tuple[str], *args: Any
    ) -> bool:
        if isinstance(suffix, list):
            suffix = tuple(suffix)
        return search.endswith(suffix, *args)

    # Functions that expands the standard JMESPath functions:

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_regex_match(self, regex: str, value: str, *args: Any) -> bool:
        return bool(re.match(regex, value, *args))

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["array-string", "object"]},
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

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_regex_search(
        self, regex: str, value: str, *args: Any
    ) -> list[str]:
        match = re.search(regex, value, *args)
        if not match:
            return []
        return [match.group(0)] if not match.groups() else list(match.groups())

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_regex_sub(
        self, regex: str, repl: str, value: str, *args: Any
    ) -> str:
        return re.sub(regex, repl, value, *args)

    @jmespath_func_signature({"types": ["string"]})
    def _func_regex_escape(self, regex: str) -> str:
        return re.escape(regex)

    @jmespath_func_signature(
        {"types": []},
        {"types": ["string"]},
        {"types": [], "variadic": True},
    )
    def _func_op(self, a: float, operator: str, b: float, *args: Any) -> Any:
        operators = []
        current_op = None
        for i, op_or_value in enumerate([operator, b] + (list(args) or [])):
            if i % 2 == 0:
                try:
                    func = OPERATORS_FUNCTIONS[op_or_value]  # type: ignore
                except KeyError:
                    raise OriginalJMESPathError(
                        f"Invalid operator '{op_or_value}' passed to op()"
                        f" function at index {i}, expected one of:"
                        f" {', '.join(list(OPERATORS_FUNCTIONS))}",
                    )
                else:
                    current_op = (func, op_or_value)
            else:
                operators.append((current_op, op_or_value))

        partial_result = a
        for (func, operator), b_ in operators:  # type: ignore
            if (
                isinstance(b_, list)
                and isinstance(partial_result, list)
                and operator in SET_OPERATORS
            ):
                # both values are lists and the operator is only valid for sets,
                # so convert both values to set applying the operator
                if operator in OPERATORS_THAT_RETURN_SET:
                    partial_result = list(func(set(partial_result), set(b_)))
                else:
                    partial_result = func(set(partial_result), set(b_))
            else:
                partial_result = func(partial_result, b_)
        return partial_result

    @jmespath_func_signature({"types": ["array-string"]})
    def _func_shlex_join(self, cmd_list: list[str]) -> str:
        return shlex_join(cmd_list)

    @jmespath_func_signature({"types": ["string"]})
    def _func_shlex_split(self, cmd_str: str) -> list[str]:
        return shlex.split(cmd_str)

    @jmespath_func_signature(
        {
            "types": ["number"],
            "variadic": True,
        },
    )
    def _func_round(self, *args: Any) -> Any:
        return round(*args)

    @jmespath_func_signature(
        {
            "types": ["number"],
            "variadic": True,
        },
    )
    def _func_range(self, *args: Any) -> list[float] | list[int]:
        return list(range(*args))

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["number"], "variadic": True},
    )
    def _func_center(self, value: str, width: int, *args: Any) -> str:
        return value.center(width, *args)

    @jmespath_func_signature(
        {"types": ["string", "array"]},
        {"types": [], "variadic": True},
    )
    def _func_count(
        self,
        value: list[Any] | str,
        sub: Any,
        *args: Any,
    ) -> int:
        return value.count(sub, *args)

    @jmespath_func_signature(
        {"types": [], "variadic": True},
    )
    def _func_format(self, schema: str, *args: Any) -> str:
        return schema.format(*args)

    @jmespath_func_signature({"types": ["string"], "variadic": True})
    def _func_splitlines(self, value: str, *args: Any) -> list[str]:
        return value.splitlines(*args)

    @jmespath_func_signature({"types": ["string"]}, {"types": ["number"]})
    def _func_zfill(self, value: str, width: int) -> str:
        return value.zfill(width)

    @jmespath_func_signature({"types": ["string", "array", "object"]})
    def _func_enumerate(
        self,
        value: list[Any] | str | dict[str, Any],
    ) -> list[list[Any]]:
        if isinstance(value, dict):
            return [list(item) for item in enumerate(_to_items(value))]
        return [list(item) for item in enumerate(value)]

    @jmespath_func_signature({"types": ["object"]})
    def _func_to_items(
        self,
        value: dict[str, Any],
    ) -> list[list[Any]]:
        return _to_items(value)

    @jmespath_func_signature({"types": ["array"]})
    def _func_from_items(self, value: list[Any]) -> dict[str, Any]:
        return {str(key): subv for key, subv in value}

    @jmespath_func_signature()
    def _func_rootdir_name(self) -> str:
        return os.path.basename(os.environ["PROJECT_CONFIG_ROOTDIR"])

    @jmespath_func_signature(
        {"types": [], "variadic": True},
    )
    def _func_deepmerge(
        self,
        base: Any,
        nxt: Any,
        *args: Any,
    ) -> Any:
        # TODO: if base and nxt are strings use merge with other
        #   strategies such as prepend or append text.
        if len(args) > 0:
            strategies: str | list[dict[str, list[str]] | list[str]] = args[0]
        else:
            strategies = "conservative_merger"
        if isinstance(strategies, str):
            try:
                merger = BUILTIN_DEEPMERGE_STRATEGIES[strategies]
            except KeyError:
                raise OriginalJMESPathError(
                    f"Invalid strategy '{strategies}' passed to deepmerge()"
                    " function, expected one of:"
                    f" {', '.join(list(BUILTIN_DEEPMERGE_STRATEGIES))}",
                )
        else:
            type_strategies = []
            for key, value in strategies[0]:  # type: ignore
                key = {"array": "list", "object": "dict"}.get(
                    key,  # type: ignore
                    key,  # type: ignore
                )
                if key not in BUILTIN_TYPES:
                    raise OriginalJMESPathError(
                        f"Invalid type passed to deepmerge() function in"
                        " strategies array, expected one of:"
                        f" {', '.join(BUILTIN_TYPES)}",
                    )
                type_strategies.append(
                    (getattr(builtins, key), value),  # type: ignore
                )

            # TODO: cache merge objects by strategies used
            merger = deepmerge.Merger(
                type_strategies,
                *strategies[1:],
            )

        merger.merge(base, nxt)
        return base

    @jmespath_func_signature({"types": ["object"]}, {"types": ["object"]})
    def _func_update(
        self,
        base: dict[str, Any],
        nxt: dict[str, Any],
    ) -> dict[str, Any]:
        base.update(nxt)
        return base

    @jmespath_func_signature(
        {"types": ["array"]},
        {"types": ["number"]},
        {"types": []},
    )
    def _func_insert(
        self,
        base: list[Any],
        index: int,
        item: Any,
    ) -> list[Any]:
        base.insert(index, item)
        return base

    @jmespath_func_signature(
        {"types": ["object"]},
        {"types": ["string"]},
        {"types": []},
    )
    def _func_set(
        self,
        base: dict[str, Any],
        key: str,
        value: Any,
    ) -> dict[str, Any]:
        base[key] = value
        return base

    @jmespath_func_signature(
        {"types": ["object"]},
        {"types": ["string"]},
    )
    def _func_unset(
        self,
        base: dict[str, Any],
        key: str,
    ) -> dict[str, Any]:
        if key in base:
            del base[key]
        return base

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_replace(
        self,
        base: str,
        old: str,
        new: str,
        *args: Any,  # count
    ) -> str:
        return base.replace(old, new, *args)

    @jmespath_func_signature()
    def _func_os(self) -> str:
        return sys.platform

    @jmespath_func_signature({"types": ["string"]})
    def _func_getenv(self, envvar: str) -> str | None:
        return os.environ.get(envvar)

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string", "null"]},
    )
    def _func_setenv(
        self,
        envvar: str,
        value: str | None,
    ) -> dict[str, str]:
        if value is None:
            del os.environ[envvar]
        else:
            os.environ[envvar] = value
        return dict(os.environ)

    # File system functions
    @jmespath_func_signature({"types": ["string"]})
    def _func_isfile(self, path: str) -> bool:
        return os.path.isfile(path)

    @jmespath_func_signature({"types": ["string"]})
    def _func_isdir(self, path: str) -> bool:
        return os.path.isdir(path)

    @jmespath_func_signature({"types": ["string"]})
    def _func_exists(self, path: str) -> bool:
        try:
            os.stat(path)
        except FileNotFoundError:
            return False
        return True

    @jmespath_func_signature({"types": ["string"]})
    def _func_mkdir(self, path: str) -> bool:
        try:
            os.stat(path)
        except FileNotFoundError:
            os.mkdir(path)
            return True
        return False

    @jmespath_func_signature({"types": ["string"]})
    def _func_rmdir(self, path: str) -> bool:
        try:
            os.stat(path)
        except FileNotFoundError:
            return False
        shutil.rmtree(path)
        return True

    @jmespath_func_signature({"types": ["string"]})
    def _func_listdir(self, path: str) -> list[str] | None:
        try:
            return os.listdir(path)
        except FileNotFoundError:
            return None

    @jmespath_func_signature(
        {"types": ["string"], "variadic": True},
    )
    def _func_glob(
        self,
        pattern: str,
        *args: Any,  # recursive
    ) -> list[str]:
        return glob.glob(pattern, recursive=args[0] if args else False)

    # Github functions
    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_gh_tags(
        self, repo_owner: str, repo_name: str, *args: Any
    ) -> list[str]:
        from project_config.fetchers.github import get_latest_release_tags

        kwargs = {}
        if len(args):
            kwargs["only_semver"] = args[0]

        return get_latest_release_tags(repo_owner, repo_name, **kwargs)

    # built-in Python's functions
    locals().update(
        dict(
            {
                f"_func_{func_name}": (
                    _create_simple_transform_function_for_string(func_name)
                )
                for func_name in {
                    "capitalize",
                    "casefold",
                    "lower",
                    "swapcase",
                    "title",
                    "upper",
                }
            },
            **{
                f"_func_{func_prefix}find": (
                    _create_find_function_for_string_or_array(
                        func_prefix,
                    )
                )
                for func_prefix in {"", "r"}
            },
            **{
                f"_func_is{func_suffix}": _create_is_function_for_string(
                    func_suffix,
                )
                for func_suffix in {
                    "alnum",
                    "alpha",
                    "ascii",
                    "decimal",
                    "digit",
                    "identifier",
                    "lower",
                    "numeric",
                    "printable",
                    "space",
                    "title",
                    "upper",
                }
            },
            **{
                f"_func_{func_prefix}just": _create_just_function_for_string(
                    func_prefix,
                )
                for func_prefix in {"l", "r"}
            },
            **{
                f"_func_{func_prefix}split": _create_split_function_for_string(
                    func_prefix,
                )
                for func_prefix in {"", "r"}
            },
            **{
                f"_func_{func_prefix}strip": _create_strip_function_for_string(
                    func_prefix,
                )
                for func_prefix in {"", "l", "r"}
            },
            **{
                f"_func_{func_prefix}partition": (
                    _create_partition_function_for_string(func_prefix)
                )
                for func_prefix in {"", "r"}
            },
            **{
                f"_func_remove{func_suffix}": (
                    _create_removeaffix_function_for_string(func_suffix)
                )
                for func_suffix in {"suffix", "prefix"}
            },
        ),
    )


jmespath_project_config_options = JMESPathProjectConfigFunctions()

jmespath_options = JMESPathOptions(
    custom_functions=jmespath_project_config_options,
)


def compile_JMESPath_expression(expression: str) -> JMESPathParsedResult:
    """Compile a JMESPath expression.

    Args:
        expression (str): JMESPath expression to compile.

    Returns:
        :py:class:`jmespath.parser.ParsedResult`: JMESPath expression compiled.
    """
    compiled_expression: JMESPathParsedResult = Cache.get(f"jm://{expression}")
    if compiled_expression is None:
        compiled_expression = jmespath_compile(expression)
        Cache.set(f"jm://{expression}", compiled_expression)
    return compiled_expression


def compile_JMESPath_expression_or_error(
    expression: str,
) -> JMESPathParsedResult:
    """Compile a JMESPath expression or raise a ``JMESPathError``.

    Args:
        expression (str): JMESPath expression to compile.

    Returns:
        :py:class:`jmespath.parser.ParsedResult`: JMESPath
            expression compiled.

    Raises:
        ``JMESPathError``: If the expression cannot be compiled.
    """
    try:
        return compile_JMESPath_expression(expression)
    except OriginalJMESPathError as exc:
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath expression {pprint.pformat(expression)}."
            f" Raised JMESPath {error_type}: {str(exc)}",
        )


def compile_JMESPath_or_expected_value_error(
    expression: str,
    expected_value: Any,
) -> JMESPathParsedResult:
    """Compile a JMESPath expression or raise a ``JMESPathError``.

    You can pass a expected value that was being expected in the error message.

    Args:
        expression (str): JMESPath expression to compile.
        expected_value (Any): Value that was expected to match against expression.

    Returns:
        :py:class:`jmespath.parser.ParsedResult`: JMESPath expression compiled.

    Raises:
        ``JMESPathError``: If the expression cannot be compiled.
    """  # noqa: E501
    try:
        return compile_JMESPath_expression(expression)
    except OriginalJMESPathError as exc:
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath expression {pprint.pformat(expression)}."
            f" Expected to return {pprint.pformat(expected_value)}, raised"
            f" JMESPath {error_type}: {str(exc)}",
        )


def compile_JMESPath_or_expected_value_from_other_file_error(
    expression: str,
    expected_value_file: str,
    expected_value_expression: str,
) -> JMESPathParsedResult:
    """Compile a JMESPath expression or raise a ``JMESPathError``.

    Show that the expression was being expected to match the value
    applying the expression to another file than the actual.

    Args:
        expression (str): JMESPath expression to compile.
        expected_value_file (str): File to the query is applied to.
        expected_value_expression (str): Expected result value not
            satisfied by the expression.

    Returns:
        :py:class:`jmespath.parser.ParsedResult`: JMESPath
             expression compiled.

    Raises:
        ``JMESPathError``: If the expression cannot be compiled.
    """
    try:
        return compile_JMESPath_expression(expression)
    except OriginalJMESPathError as exc:
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


def evaluate_JMESPath(
    compiled_expression: JMESPathParsedResult,
    instance: Any,
) -> Any:
    """Evaluate a JMESPath expression against a instance.

    Args:
        compiled_expression (:py:class:`jmespath.parser.ParsedResult`): JMESPath
            expression to evaluate.
        instance (any): Instance to evaluate the expression against.

    Returns:
        any: Result of the evaluation.

    Raises:
        ``JMESPathError``: If the expression cannot be evaluated.
    """
    # This caching is a bit tricky, because some things as if a
    # directory exists can not be cached, can change.
    #
    # Also, Python modules can't be pickled, so we can't cache them.
    #
    # TODO: This needs to be properly tested, currently a cache
    #       inconsistency is affecting the example 008.
    is_cacheable_expression = True
    for uncacheable_variable in UNCACHEABLE_JMESPATH_VARIABLES:
        if uncacheable_variable in compiled_expression.expression:
            is_cacheable_expression = False
            break
    if is_cacheable_expression is False:
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )

    try:
        pickled_instance = pickle.dumps(instance)
    except TypeError:
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )

    result = Cache.get(
        f"jm://E?{compiled_expression.expression}:{hash(pickled_instance)}",
    )
    if result is None:
        try:
            result = compiled_expression.search(
                instance,
                options=jmespath_options,
            )
        except OriginalJMESPathError as exc:
            formatted_expression = pprint.pformat(
                compiled_expression.expression,
            )
            error_type = JMESPATH_READABLE_ERRORS.get(
                exc.__class__.__name__,
                "error",
            )
            raise JMESPathError(
                f"Invalid JMESPath {formatted_expression}."
                f" Raised JMESPath {error_type}: {str(exc)}",
            )
        Cache.set(
            f"jm://E?{compiled_expression.expression}:{str(instance)}",
            result,
        )
    return result


def evaluate_JMESPath_or_expected_value_error(
    compiled_expression: JMESPathParsedResult,
    expected_value: Any,
    instance: Any,
) -> Any:
    """Evaluate a JMESPath expression against a instance or raise a ``JMESPathError``.

    You can pass a expected value that was being expected in the
    error message.

    Args:
        compiled_expression (:py:class:`jmespath.parser.ParsedResult`): JMESPath
            expression to evaluate.
        expected_value (any): Value that was expected to match against expression.
        instance (any): Instance to evaluate the expression against.

    Returns:
        any: Result of the evaluation.

    Raises:
        ``JMESPathError``: If the
            expression cannot be evaluated.
    """  # noqa: E501
    try:
        return evaluate_JMESPath(compiled_expression, instance)
    except OriginalJMESPathError as exc:
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


def fix_tree_serialized_file_by_jmespath(
    compiled_expression: JMESPathParsedResult,
    instance: Any,
    fpath: str,
) -> bool:
    """Fix a file by aplying a JMESPath expression to an instance.

    This function is used to fix a file by applying a JMESPath expression.
    The result of the expression will be the serialized version of the
    updated instance.

    Args:
        compiled_expression (:py:class:`jmespath.parser.ParsedResult`): JMESPath
            expression to evaluate.
        instance (any): Instance to evaluate the expression against.
        fpath (str): Path to the file to fix.

    Returns:
        bool: True if the file was fixed, False otherwise.
    """
    new_content = evaluate_JMESPath(
        compiled_expression,
        instance,
    )
    return tree.edit_local_file(fpath, new_content)


REVERSE_JMESPATH_TYPE_PYOBJECT: dict[
    str | None,
    dict[Any, Any] | list[Any] | Literal[0, "", None],
] = {
    "string": "",
    "number": 0,
    "object": {},
    "array": [],
    "null": None,
    None: None,
}


def _build_reverse_jmes_type_object(jmespath_type: str) -> Any:
    return REVERSE_JMESPATH_TYPE_PYOBJECT[jmespath_type]


def smart_fixer_by_expected_value(
    compiled_expression: JMESPathParsedResult,
    expected_value: Any,
) -> str:
    """Smart JMESPath fixer queries creator.

    Build a smart JMESPath query fixer by altering a expression to
    match a expected value given the syntax of an expression.

    Args:
        compiled_expression (:py:class:`jmespath.parser.ParsedResult`): JMESPath
            expression to evaluate.
        expected_value (any): Value that was expected to match against
            expression.

    Returns:
        str: JMESPath query fixer.
    """
    fixer_expression = ""

    parser = Parser()
    ast = parser.parse(compiled_expression.expression).parsed

    merge_strategy = "conservative_merger"

    if (
        ast["type"] == "index_expression"
        and ast["children"][0]["type"] == "identity"
        and ast["children"][1]["type"] == "index"
    ):
        return (
            f'insert(@, `{ast["children"][1]["value"]}`,'
            f" `{json.dumps(expected_value)}`)"
        )
    if ast["type"] == "field":
        key = ast["value"]
        return f"set(@, '{key}' `{json.dumps(expected_value)}`)"
    elif ast["type"] == "subexpression":
        temporal_object = {}
        _obj = {}
        for i, child in enumerate(reversed(ast["children"])):
            # TODO: manage indexes in subexpressions
            if child["type"] == "index_expression":
                return ""
            if i == 0:
                _obj = {child["value"]: expected_value}
            else:
                _obj = {child["value"]: _obj}
        temporal_object = _obj

    elif ast["type"] == "function_expression" and ast["value"] == "type":
        if expected_value not in REVERSE_JMESPATH_TYPE_PYOBJECT:
            return ""
        temporal_object = {}
        if len(ast["children"]) == 1 and ast["children"][0]["type"] == "field":
            temporal_object = {
                ast["children"][0]["value"]: _build_reverse_jmes_type_object(
                    expected_value,
                ),
            }
        elif (
            len(ast["children"]) == 1
            and ast["children"][0]["type"] == "current"
        ):
            temporal_object = _build_reverse_jmes_type_object(expected_value)
            return f"`{json.dumps(temporal_object, indent=None)}`"
        else:
            deep: list[Any] = []

            def _iterate_expressions(
                expressions: list[Any],
                temporal_object: Any,
                merge_strategy: Any,
                deep: list[Any],
            ) -> tuple[list[Any], Any, Any]:

                for iexp, fexp in enumerate(reversed(expressions)):
                    _last_field_type_iexp = (
                        len([e["type"] == "field" for e in expressions[iexp:]])
                        > 0
                    )
                    if fexp["type"] == "field":
                        fexp_value = fexp["value"]
                    elif fexp["type"] == "index_expression":
                        (
                            tmp_deep,
                            temporal_object,
                            merge_strategy,
                        ) = _iterate_expressions(
                            fexp["children"],
                            temporal_object,
                            merge_strategy,
                            deep,
                        )
                        deep.extend(tmp_deep)
                        continue
                    elif fexp["type"] == "index":
                        fexp_value = fexp["value"]

                    deep.append(fexp_value)
                    _obj: Any = {}
                    for di, d in enumerate(deep):
                        if di == 0 and _last_field_type_iexp:
                            _obj = _build_reverse_jmes_type_object(
                                expected_value,
                            )
                        if isinstance(d, str):
                            _obj = {d: _obj}
                        else:
                            # index
                            merge_strategy = [
                                [
                                    (
                                        "list",
                                        "prepend" if d == 0 else "append",
                                    ),
                                    ("dict", "merge"),
                                    ("set", "union"),
                                ],
                                ["override"],
                                ["override"],
                            ]
                            _obj = [_obj]
                    temporal_object = _obj

                return (deep, temporal_object, merge_strategy)

            for child in ast["children"]:
                if child["type"] == "subexpression":
                    expressions = list(child.get("children", []))
                    (
                        _,
                        temporal_object,
                        merge_strategy,
                    ) = _iterate_expressions(
                        expressions,
                        temporal_object,
                        merge_strategy,
                        deep,
                    )
    elif (
        ast["type"] == "function_expression"
        and ast["value"] == "contains"
        and len(ast["children"]) == 2
        and ast["children"][0]["type"] == "function_expression"
        and ast["children"][0]["value"] == "keys"
        and ast["children"][0].get("children")
        and ast["children"][0]["children"][0]["type"] == "current"
        and ast["children"][1]["type"] == "literal"
    ):
        if expected_value is False:
            # contains(keys(@), 'key') -> false
            key = ast["children"][1]["value"]
            fixer_expression = f"unset(@, '{key}')"
        return fixer_expression
    else:  # pragma: no cover
        return fixer_expression

    # default deepmerge fixing
    if isinstance(merge_strategy, str):
        merge_strategy_formatted = f"'{merge_strategy}'"
    else:
        merge_strategy_formatted = (
            f"`{json.dumps(merge_strategy, indent=None)}`"
        )
    fixer_expression += (
        f"deepmerge(@,"
        f" `{json.dumps(temporal_object, indent=None)}`,"
        f" {merge_strategy_formatted})"
    )

    return fixer_expression


def is_literal_jmespath_expression(expression: str) -> bool:
    """Check if a JMESPath expression is a literal expression."""
    parser = Parser()
    try:
        ast = parser.parse(expression).parsed
    except JMESPathParserError:
        return False
    return ast["type"] == "literal"
