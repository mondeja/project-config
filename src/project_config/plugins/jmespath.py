import operator
import pprint
import re
import typing as t

import jmespath

from project_config import Error, InterruptingError, Results, Rule, Tree


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


class InvalidOperator(jmespath.exceptions.JMESPathError):
    def __init__(self, operator: str):
        super().__init__(
            f"Invalid operator '{operator}' passed to op() function,"
            f" expected one of: {', '.join(list(OPERATORS_FUNCTIONS))}"
        )


class JMESPathProjectConfigFunctions(jmespath.functions.Functions):
    """Custom functionso object to support some custom functions.

    Custom functions added:

    - ``regex_match('<regex>', '<string>') -> boolean``: Match a Python regular
      expression against a string.
    - ``regex_matchall('<regex>', <container>) -> boolean``: Match a Python regular
      expression against all items in a container.
    - ``regex_search('<regex>', '<string>') -> array[string]``: Search with
      Python regular expression against a JMESPath result. It returns
      an array with all groups, if groups are defined inside the regular
      expression or an array with the full match otherwise.
    - ``gt(<source_number>, <target_number>)``: Returns if ``target``
      is equal to ``source``. Both values accepts any types.
    - ``gt(<source_number>, <target_number>)``: Returns if ``target_number``
      is greater than ``source_number``.
    - ``gte(<source_number>, <target_number>)``: Returns if ``target_number``
      is greater or equal than ``source_number``.
    - ``is_empty(<container>)``: Returns if ``container`` is empty. Works for
      strings, arrays and objects.
    """

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["string"]})
    def _func_regex_match(self, regex: str, value: str) -> bool:
        return bool(re.match(regex, value))

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["array", "object"]})
    def _func_regex_matchall(self, regex: str, container: str) -> bool:
        return all(bool(re.match(regex, value)) for value in container)

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["string"]})
    def _func_regex_search(self, regex: str, value: str) -> t.List[str]:
        match = re.search(regex, value)
        return [match.group(0)] if not match.groups() else list(match.groups())

    @jmespath.functions.signature(
        {"types": ["number", "string"]},
        {"types": ["string"]},
        {"types": ["number", "string"]},
    )
    def _func_op(self, a: float, operator: str, b: float) -> bool:
        try:
            return OPERATORS_FUNCTIONS[operator](a, b)
        except KeyError:
            raise InvalidOperator(operator)

    @jmespath.functions.signature({"types": ["string", "array", "object"]})
    def _func_is_empty(
        self,
        container: t.Union[str, t.List[t.Any], t.Dict[t.Any, t.Any]],
    ) -> bool:
        return not bool(container)


jmespath_options = jmespath.Options(custom_functions=JMESPathProjectConfigFunctions())


class JMESPathPlugin:
    @staticmethod
    def JMESPathsMatch(
        value: t.List[t.List[str]],  # list of tuples
        tree: Tree,
        rule: Rule,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": "The JMES path - match tuples must be of type array",
                "definition": ".JMESPathsMatch",
                "file": None,
            }
            return
        if not value:
            yield InterruptingError, {
                "message": "The JMES path - match tuples must not be empty",
                "definition": ".JMESPathsMatch",
                "file": None,
            }
            return
        for t, jmespath_match_tuple in enumerate(value):
            if not isinstance(jmespath_match_tuple, list):
                yield InterruptingError, {
                    "message": "The JMES path - match tuple must be of type array",
                    "definition": f".JMESPathsMatch[{t}]",
                    "file": None,
                }
                return
            if not len(jmespath_match_tuple) == 2:
                yield InterruptingError, {
                    "message": "The JMES path - match tuple must be of length 2",
                    "definition": f".JMESPathsMatch[{t}]",
                    "file": None,
                }
                return
            if not isinstance(jmespath_match_tuple[0], str):
                yield InterruptingError, {
                    "message": "The JMES path must be of type string",
                    "definition": f".JMESPathsMatch[{t}][0]",
                    "file": None,
                }
                return

        jmespath_expressions = None

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": "You can't apply a JMESPath to a directory",
                    "definition": f".files[{f}]",
                    "file": f"{fpath}/",
                }
            elif jmespath_expressions is None:
                jmespath_expressions = []
                for e, (exp, expected_value) in enumerate(value):
                    try:
                        jmespath_expressions.append(
                            (jmespath.compile(exp), expected_value)
                        )
                    except jmespath.exceptions.ParseError as exc:
                        yield InterruptingError, {
                            "message": (
                                f"Invalid JMESPath expression {pprint.pformat(exp)}."
                                f" Expected to return {pprint.pformat(expected_value)}, raised"
                                f" JMESPath parsing error: {exc.__str__()}"
                            ),
                            "definition": f".JMESPathsMatch[{e}][0]",
                            "file": fpath,
                        }

            instance = tree.decode_file(fpath, fcontent)
            if "update" in fpath:
                import json

                print(json.dumps(instance))

            for e, (exp, expected_value) in enumerate(jmespath_expressions):
                try:
                    expression_result = exp.search(
                        instance,
                        options=jmespath_options,
                    )
                except jmespath.exceptions.JMESPathTypeError as exc:
                    print(exp.expression)
                    yield Error, {
                        "message": (
                            f"Invalid JMESPath {pprint.pformat(exp.expression)} in context."
                            f" Expected to return {pprint.pformat(expected_value)}, raised"
                            f" JMESPath type error: {exc.__str__()}"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }
                    continue
                except jmespath.exceptions.JMESPathError as exc:
                    yield Error, {
                        "message": (
                            f"Invalid JMESPath {pprint.pformat(exp.expression)}."
                            f" Expected to return {pprint.pformat(expected_value)}, raised"
                            f" JMESPath error: {exc.__str__()}"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }
                    continue

                if expression_result != expected_value:
                    yield Error, {
                        "message": (
                            f"JMESPath '{exp.expression}' does not match."
                            f" Expected {pprint.pformat(expected_value)}, returned"
                            f" {pprint.pformat(expression_result)}"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }
