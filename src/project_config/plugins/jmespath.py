"""JMESPath expressions plugin."""

from __future__ import annotations

import builtins
import copy
import json
import operator
import os
import pprint
import re
import shlex
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

from project_config import (
    ActionsContext,
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)
from project_config.compat import (
    cached_function,
    removeprefix,
    removesuffix,
    shlex_join,
)
from project_config.exceptions import ProjectConfigException
from project_config.fetchers import FetchError
from project_config.serializers import SerializerError


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

    @jmespath_func_signature(
        {"types": []},
        {"types": ["string"]},
        {"types": []},
    )
    def _func_op(self, a: float, operator: str, b: float) -> t.Any:
        try:
            func = OPERATORS_FUNCTIONS[operator]
        except KeyError:
            raise OriginalJMESPathError(
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
                if key not in BUILTIN_TYPES:  # type: ignore
                    raise OriginalJMESPathError(
                        f"Invalid type passed to deepmerge() function in"
                        " strategies array, expected one of:"
                        f" {', '.join(BUILTIN_TYPES)}",
                    )
                type_strategies.append(  # type: ignore
                    (getattr(builtins, key), value),
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


jmespath_options = JMESPathOptions(
    custom_functions=JMESPathProjectConfigFunctions(),
)


class JMESPathError(ProjectConfigException):
    """Class to wrap all JMESPath errors of the plugin."""


@cached_function
def _compile_JMESPath_expression(
    expression: str,
) -> JMESPathParsedResult:
    return jmespath_compile(expression)


def _compile_JMESPath_expression_or_error(
    expression: str,
) -> JMESPathParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
    except OriginalJMESPathError as exc:
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
) -> JMESPathParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
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


def _compile_JMESPath_or_expected_value_from_other_file_error(
    expression: str,
    expected_value_file: str,
    expected_value_expression: str,
) -> JMESPathParsedResult:
    try:
        return _compile_JMESPath_expression(expression)
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


def _evaluate_JMESPath(
    compiled_expression: JMESPathParsedResult,
    instance: t.Any,
) -> t.Any:
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


def _evaluate_JMESPath_or_expected_value_error(
    compiled_expression: JMESPathParsedResult,
    expected_value: t.Any,
    instance: t.Dict[str, t.Any],
) -> t.Any:
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


def _build_fixer_function(
    compiled_expression: JMESPathParsedResult,
    instance: t.Any,
    fpath: str,
    tree: Tree,
) -> t.Callable[[], bool]:
    def _wrapper() -> bool:
        # TODO: raise errors
        new_content = _evaluate_JMESPath(
            compiled_expression,
            instance,
        )
        return tree.edit_serialized_file(fpath, new_content)

    return _wrapper


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


def _smart_fixer_query(
    compiled_expression: JMESPathParsedResult,
    expected_value: t.Any,
) -> str:
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

    else:
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


class JMESPathPlugin:
    @staticmethod
    def JMESPathsMatch(
        value: t.List[t.List[t.Any]],
        tree: Tree,
        rule: Rule,
        context: ActionsContext,
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
            if len(jmespath_match_tuple) not in (2, 3):
                yield InterruptingError, {
                    "message": (
                        "The JMES path match tuple must be of length 2 or 3"
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
                    return

        files = copy.copy(tree.files)
        for f, (fpath, fcontent) in enumerate(files):
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

            _, instance = tree.serialize_file(fpath)

            for e, (expression, expected_value, fixer_query) in enumerate(
                value,
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
                    if context.fix:
                        if not fixer_query:
                            fixer_query = _smart_fixer_query(
                                compiled_expression,
                                expected_value,
                            )
                        if fixer_query:
                            # TODO: raise errors
                            diff = _build_fixer_function(
                                _compile_JMESPath_expression(fixer_query),
                                instance,
                                fpath,
                                tree,
                            )()
                            fixed = True
                            if not diff:
                                continue
                        else:
                            fixed = False
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
                    }

    @staticmethod
    def ifJMESPathsMatch(
        value: t.Dict[str, t.List[t.List[str]]],
        tree: Tree,
        rule: Rule,
        context: ActionsContext,
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
                _, instance = tree.serialize_file(fpath)
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
        context: ActionsContext,
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

                _, files_instance = tree.serialize_file(fpath)

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
