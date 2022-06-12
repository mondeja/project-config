import pprint
import typing as t

import jmespath

from project_config import (
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)
from project_config.fetchers import decode_with_decoder, get_decoder
from project_config.utils import GET


class JMESPathPlugin:
    @classmethod
    def JMESPathsMatch(
        cls,
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
            for e, (exp, expected_value) in enumerate(jmespath_expressions):
                expression_result = exp.search(instance)
                if expression_result != expected_value:
                    yield Error, {
                        "message": (
                            f"The JMESPath expression '{exp.expression}' does not match."
                            f" Expected {pprint.pformat(expected_value)}, returned"
                            f" '{expression_result}'"
                        ),
                        "definition": f".JMESPathsMatch[{e}]",
                        "file": fpath,
                    }
