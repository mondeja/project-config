"""Utilities related to JMESPaths."""

from __future__ import annotations

import builtins
import json
import operator
import os
import pprint
import re
import shlex
import sys
import typing as t
import warnings

import deepmerge
from jmespath import Options as JMESPathOptions, compile as jmespath_compile
from jmespath.exceptions import JMESPathError as OriginalJMESPathError
from jmespath.functions import (
    Functions as JMESPathFunctions,
    signature as jmespath_func_signature,
)
from jmespath.parser import ParsedResult as JMESPathParsedResult, Parser

from project_config.compat import removeprefix, removesuffix, shlex_join
from project_config.exceptions import ProjectConfigException
from project_config.tree import Tree


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


def _create_simple_transform_function_for_string(
    func_name: str,
) -> t.Callable[[type, str], str]:
    func = getattr(str, func_name)
    return jmespath_func_signature({"types": ["string"]})(
        lambda self, value: func(value),
    )


def _create_is_function_for_string(
    func_suffix: str,
) -> t.Callable[[type, str], bool]:
    func = getattr(str, f"is{func_suffix}")
    return jmespath_func_signature({"types": ["string"]})(
        lambda self, value: func(value),
    )


def _create_find_function_for_string_or_array(
    func_prefix: str,
) -> t.Callable[[type, t.Union[t.List[t.Any], str], t.Any, t.Any], int]:
    getattr(str, f"{func_prefix}find")

    def _wrapper(
        self: type, value: t.Union[t.List[t.Any], str], sub: t.Any, *args: t.Any
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
) -> t.Callable[[type, str, int, t.Any], str]:
    func = getattr(str, f"{func_prefix}just")
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["number"], "variadic": True},
    )(lambda self, value, width, *args: func(value, width, *args))


def _create_partition_function_for_string(
    func_prefix: str,
) -> t.Callable[[type, str, str], t.List[str]]:
    func = getattr(str, f"{func_prefix}partition")
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
    )(lambda self, value, sep: list(func(value, sep)))


def _create_split_function_for_string(
    func_prefix: str,
) -> t.Callable[[type, str, t.Any], t.List[str]]:
    func = getattr(str, f"{func_prefix}split")
    return jmespath_func_signature(
        {"types": ["string"], "variadic": True},
    )(lambda self, value, *args: func(value, *args))


def _create_strip_function_for_string(
    func_prefix: str,
) -> t.Callable[[type, str], str]:
    func = getattr(str, f"{func_prefix}strip")
    return jmespath_func_signature(
        {"types": ["string"], "variadic": True},
    )(lambda self, value, *args: func(value, *args))


def _create_removeaffix_function_for_string(
    func_suffix: str,
) -> t.Callable[[type, str, str], str]:
    func = removesuffix if func_suffix.startswith("s") else removeprefix
    return jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"]},
    )(lambda self, value, affix: func(value, affix))


def _to_items(value: t.Any) -> t.List[t.Any]:
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
        self, search: str, suffix: t.Union[str, t.Tuple[str]], *args: t.Any
    ) -> bool:
        if isinstance(suffix, list):
            suffix = tuple(suffix)
        return search.startswith(suffix, *args)

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string", "array-string"], "variadic": True},
    )
    def _func_ends_with(
        self, search: str, suffix: t.Union[str, t.Tuple[str]], *args: t.Any
    ) -> bool:
        if isinstance(suffix, list):
            suffix = tuple(suffix)
        return search.endswith(suffix, *args)

    # Functions that expands the standard JMESPath functions:

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_regex_match(self, regex: str, value: str, *args: t.Any) -> bool:
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
        self, regex: str, value: str, *args: t.Any
    ) -> t.List[str]:
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
        self, regex: str, repl: str, value: str, *args: t.Any
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
    def _func_op(
        self, a: float, operator: str, b: float, *args: t.Any
    ) -> t.Any:
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
    def _func_shlex_join(self, cmd_list: t.List[str]) -> str:
        return shlex_join(cmd_list)

    @jmespath_func_signature({"types": ["string"]})
    def _func_shlex_split(self, cmd_str: str) -> t.List[str]:
        return shlex.split(cmd_str)

    @jmespath_func_signature(
        {
            "types": ["number"],
            "variadic": True,
        },
    )
    def _func_round(self, *args: t.Any) -> t.Any:
        return round(*args)

    @jmespath_func_signature(
        {
            "types": ["number"],
            "variadic": True,
        },
    )
    def _func_range(self, *args: t.Any) -> t.Union[t.List[float], t.List[int]]:
        return list(range(*args))

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["number"], "variadic": True},
    )
    def _func_center(self, value: str, width: int, *args: t.Any) -> str:
        return value.center(width, *args)

    @jmespath_func_signature(
        {"types": ["string", "array"]},
        {"types": [], "variadic": True},
    )
    def _func_count(
        self,
        value: t.Union[t.List[t.Any], str],
        sub: t.Any,
        *args: t.Any,
    ) -> int:
        return value.count(sub, *args)

    @jmespath_func_signature(
        {"types": [], "variadic": True},
    )
    def _func_format(self, schema: str, *args: t.Any) -> str:
        return schema.format(*args)

    @jmespath_func_signature({"types": ["string"], "variadic": True})
    def _func_splitlines(self, value: str, *args: t.Any) -> t.List[str]:
        return value.splitlines(*args)

    @jmespath_func_signature({"types": ["string"]}, {"types": ["number"]})
    def _func_zfill(self, value: str, width: int) -> str:
        return value.zfill(width)

    @jmespath_func_signature({"types": ["string", "array", "object"]})
    def _func_enumerate(
        self,
        value: t.Union[t.List[t.Any], str, t.Dict[str, t.Any]],
    ) -> t.List[t.List[t.Any]]:
        if isinstance(value, dict):
            return [list(item) for item in enumerate(_to_items(value))]
        return [list(item) for item in enumerate(value)]

    @jmespath_func_signature({"types": ["object"]})
    def _func_to_items(
        self,
        value: t.Dict[str, t.Any],
    ) -> t.List[t.List[t.Any]]:
        return _to_items(value)

    @jmespath_func_signature({"types": ["array"]})
    def _func_from_items(self, value: t.List[t.Any]) -> t.Dict[str, t.Any]:
        return {str(key): subv for key, subv in value}

    @jmespath_func_signature()
    def _func_rootdir_name(self) -> str:
        return os.path.basename(os.environ["PROJECT_CONFIG_ROOTDIR"])

    @jmespath_func_signature(
        {"types": [], "variadic": True},
    )
    def _func_deepmerge(
        self,
        base: t.Any,
        nxt: t.Any,
        *args: t.Any,
    ) -> t.Any:
        # TODO: if base and nxt are strings use merge with other
        #   strategies such as prepend or append text.
        if len(args) > 0:
            strategies: t.Union[
                str,
                t.List[t.Union[t.Dict[str, t.List[str]], t.List[str]]],
            ] = args[0]
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
        base: t.Dict[str, t.Any],
        nxt: t.Dict[str, t.Any],
    ) -> t.Dict[str, t.Any]:
        base.update(nxt)
        return base

    @jmespath_func_signature(
        {"types": ["array"]},
        {"types": ["number"]},
        {"types": []},
    )
    def _func_insert(
        self,
        base: t.List[t.Any],
        index: int,
        item: t.Any,
    ) -> t.List[t.Any]:
        base.insert(index, item)
        return base

    @jmespath_func_signature(
        {"types": ["object"]},
        {"types": ["string"]},
        {"types": []},
    )
    def _func_set(
        self,
        base: t.Dict[str, t.Any],
        key: str,
        value: t.Any,
    ) -> t.Dict[str, t.Any]:
        base[key] = value
        return base

    @jmespath_func_signature(
        {"types": ["object"]},
        {"types": ["string"]},
    )
    def _func_unset(
        self,
        base: t.Dict[str, t.Any],
        key: str,
    ) -> t.Dict[str, t.Any]:
        if key in base:
            del base[key]
        return base

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_replace(
        self,
        base: str,
        old: str,
        new: str,
        *args: t.Any,  # count
    ) -> str:
        return base.replace(old, new, *args)

    @jmespath_func_signature()
    def _func_os(self) -> str:
        return sys.platform

    @jmespath_func_signature({"types": ["string"]})
    def _func_getenv(self, envvar: str) -> t.Optional[str]:
        return os.environ.get(envvar)

    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string", "null"]},
    )
    def _func_setenv(
        self,
        envvar: str,
        value: t.Optional[str],
    ) -> t.Dict[str, str]:
        if value is None:
            del os.environ[envvar]
        else:
            os.environ[envvar] = value
        return dict(os.environ)

    # Github functions
    @jmespath_func_signature(
        {"types": ["string"]},
        {"types": ["string"], "variadic": True},
    )
    def _func_gh_tags(
        self, repo_owner: str, repo_name: str, *args: t.Any
    ) -> t.List[str]:
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


project_config_options = JMESPathProjectConfigFunctions()

jmespath_options = JMESPathOptions(
    custom_functions=project_config_options,
)


def compile_JMESPath_expression(expression: str) -> JMESPathParsedResult:
    """Compile a JMESPath expression.

    Args:
        expression (str): JMESPath expression to compile.

    Returns:
        :py:class:`jmespath.parser.ParsedResult`: JMESPath expression compiled.
    """
    return jmespath_compile(expression)


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
    expected_value: t.Any,
) -> JMESPathParsedResult:
    """Compile a JMESPath expression or raise a ``JMESPathError``.

    You can pass a expected value that was being expected in the error message.

    Args:
        expression (str): JMESPath expression to compile.
        expected_value (t.Any): Value that was expected to match against expression.

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
    instance: t.Any,
) -> t.Any:
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
    try:
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )
    except OriginalJMESPathError as exc:
        formatted_expression = pprint.pformat(compiled_expression.expression)
        error_type = JMESPATH_READABLE_ERRORS.get(
            exc.__class__.__name__,
            "error",
        )
        raise JMESPathError(
            f"Invalid JMESPath {formatted_expression}."
            f" Raised JMESPath {error_type}: {str(exc)}",
        )


def evaluate_JMESPath_or_expected_value_error(
    compiled_expression: JMESPathParsedResult,
    expected_value: t.Any,
    instance: t.Any,
) -> t.Any:
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
        return compiled_expression.search(
            instance,
            options=jmespath_options,
        )
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
    instance: t.Any,
    fpath: str,
    tree: Tree,
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
        tree (:py:class:`project_config.Tree`): Tree used to cache the file.

    Returns:
        bool: True if the file was fixed, False otherwise.
    """
    new_content = evaluate_JMESPath(
        compiled_expression,
        instance,
    )
    return tree.edit_serialized_file(fpath, new_content)


REVERSE_JMESPATH_TYPE_PYOBJECT: t.Dict[t.Optional[str], t.Any] = {
    "string": "",
    "number": 0,
    "object": {},
    "array": [],
    "null": None,
    None: None,
}


def _build_reverse_jmes_type_object(jmespath_type: str) -> t.Any:
    return REVERSE_JMESPATH_TYPE_PYOBJECT[jmespath_type]


def smart_fixer_by_expected_value(
    compiled_expression: JMESPathParsedResult,
    expected_value: t.Any,
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
    # TODO: add types to JMESPath parser in typeshed
    ast = parser.parse(compiled_expression.expression).parsed  # type: ignore

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
        try:
            temporal_object = {}

            _obj = {}
            for i, child in enumerate(reversed(ast["children"])):
                if child["type"] == "index_expression":
                    return ""
                if i == 0:
                    _obj = {child["value"]: expected_value}
                else:
                    _obj = {child["value"]: _obj}
        except KeyError:
            return ""
        else:
            temporal_object = _obj
    elif ast["type"] == "function_expression" and ast["value"] == "type":
        if expected_value not in REVERSE_JMESPATH_TYPE_PYOBJECT:
            return ""
        temporal_object = {}
        if (
            len(ast.get("children")) == 1
            and ast["children"][0]["type"] == "field"
        ):
            temporal_object = {
                ast["children"][0]["value"]: _build_reverse_jmes_type_object(
                    expected_value,
                ),
            }
        elif (
            len(ast.get("children")) == 1
            and ast["children"][0]["type"] == "current"
        ):
            temporal_object = _build_reverse_jmes_type_object(expected_value)
            return f"`{json.dumps(temporal_object, indent=None)}`"
        else:
            deep: t.List[t.Any] = []

            def _iterate_expressions(
                expressions: t.List[t.Any],
                temporal_object: t.Any,
                merge_strategy: t.Any,
                deep: t.List[t.Any],
            ) -> t.Tuple[t.List[t.Any], t.Any, t.Any]:

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
                    _obj = {}
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
                            _obj = [_obj]  # type: ignore
                    temporal_object = _obj

                return (deep, temporal_object, merge_strategy)

            for child in ast.get("children"):
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
        and len(ast.get("children", [])) == 2
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
    ast = parser.parse(expression).parsed  # type: ignore
    return ast.get("type") == "literal"  # type: ignore
