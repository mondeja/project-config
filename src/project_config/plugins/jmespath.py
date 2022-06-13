import pprint
import re
import typing as t

import jmespath

from project_config import Error, InterruptingError, Results, Rule, Tree


class JMESPathProjectConfigFunctions(jmespath.functions.Functions):
    """Custom functionso object to support some custom functions.

    Custom functions added:

    - ``regex_match('<regex>', @) -> boolean``: Match a Python regular
      expression against a JMESPath result.
    - ``regex_search('<regex>', @) -> array[string]``: Search with
      Python regular expression against a JMESPath result. It returns
      an array with all groups, if groups are defined inside the regular
      expression or an array with the full match otherwise.
    """

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["string"]})
    def _func_regex_match(self, regex: str, value: str) -> bool:
        return bool(re.match(regex, value))

    @jmespath.functions.signature({"types": ["string"]}, {"types": ["string"]})
    def _func_regex_search(self, regex: str, value: str) -> bool:
        match = re.search(regex, value)
        return [match.group(0)] if not match.groups() else list(match.groups())


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

        jmespath_expressions = []
        for e, (expression_string, expected_value) in enumerate(value):
            try:
                exp = jmespath.compile(expression_string)
            except jmespath.exceptions.ParseError as exc:
                yield InterruptingError, {
                    "message": str(exc),
                    "definition": f".JMESPathsMatch[{e}][0]",
                    "file": None,
                }
                return
        jmespath_expressions = [
            (jmespath.compile(exp), expected_value) for exp, expected_value in value
        ]

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, {
                    "message": "You can't apply a JMESPath to a directory",
                    "definition": f".files[{f}]",
                    "file": f"{fpath}/",
                }

            instance = tree.decode_file(fpath, fcontent)
            import json

            if "pyproject.toml" in fpath:
                print(json.dumps(instance))
                print(type(instance["tool"]))
                print("HERE", jmespath.search("keys(@)", instance))
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
