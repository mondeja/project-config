import os
import sys

import pytest
from testing_helpers import mark_end2end

from project_config import Error, InterruptingError, ResultValue
from project_config.plugins.jmespath import JMESPathPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_match('^bar$', foo)", True]],
            None,
            [],
            id="regex_match returns true",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_match('^foo$', foo)", True]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "JMESPath 'regex_match('^foo$', foo)'"
                            " does not match. Expected True,"
                            " returned False"
                        ),
                        "fixed": False,
                        "fixable": False,
                    },
                ),
            ],
            id="regex_match returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["bar", "baz"]}'},
            [["regex_matchall('^ba[rz]$', foo)", True]],
            None,
            [],
            id="regex_matchall returns true",
        ),
        pytest.param(
            {"foo.json": '{"baz": ["foo", "bar"]}'},
            [["regex_matchall('^foo$', baz)", True]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "JMESPath 'regex_matchall('^foo$', baz)'"
                            " does not match. Expected True,"
                            " returned False"
                        ),
                        "fixed": False,
                        "fixable": False,
                    },
                ),
            ],
            id="regex_matchall returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^bar$', foo)", ["bar"]]],
            None,
            [],
            id="regex_search returns full",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^(b)(a)(r)$', foo)", ["b", "a", "r"]]],
            None,
            [],
            id="regex_search returns group",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^baz$', foo)", []]],
            None,
            [],
            id="regex_search returns null",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_sub('bar', 'baz', foo)", "baz"]],
            None,
            [],
            id="regex_sub(regex, repl, value)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "barbar"}'},
            [["regex_sub('bar', 'baz', foo, `1`)", "bazbar"]],
            None,
            [],
            id="regex_sub(regex, repl, value, count)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["op(foo, 'has the same letters than', foo)", True]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "Invalid JMESPath \"op(foo, 'has the same"
                            " letters than', foo)\". Expected to return"
                            " True, raised JMESPath error: Invalid operator"
                            " 'has the same letters than' passed to op()"
                            " function, expected one of: <, <=, ==, !=, >=,"
                            " >, is, is_not, is-not, is not, isNot, +, &,"
                            " and, //, <<, %, *, @, |, or, **, >>, -, /, ^,"
                            " count_of, count of, count-of, countOf, index_of,"
                            " index of, index-of, indexOf"
                        ),
                    },
                ),
            ],
            id="op returns invalid-operator",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["op(foo, '==', foo)", True]],
            None,
            [],
            id="op returns true",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["op(foo, '!=', foo)", False]],
            None,
            [],
            id="op returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": [1, 2]}'},
            [["op(foo, '<', `[3, 2, 1]`)", True]],
            None,
            [],
            id="op as strict issubset returns true",
        ),
        pytest.param(
            {"foo.json": '{"foo": [1, 2]}'},
            [["op(foo, '<', `[2, 1]`)", False]],
            None,
            [],
            id="op as strict issubset returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": [3, 1, 2]}'},
            [["op(foo, '>', `[2, 1]`)", True]],
            None,
            [],
            id="op as strict issuperset returns true",
        ),
        pytest.param(
            {"foo.json": '{"foo": [1, 2]}'},
            [["op(foo, '>', `[2, 1]`)", False]],
            None,
            [],
            id="op as strict issuperset returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": [1, 2]}'},
            [["op(foo, '|', `[3, 4]`)", [1, 2, 3, 4]]],
            None,
            [],
            id="op as set union returns array",
        ),
        pytest.param(
            {"foo.json": '{"foo": [2, 3, 4]}'},
            [["op(foo, 'and', `[3, 4, 5]`)", [3, 4]]],
            None,
            [],
            id="op as set intersection returns array",
        ),
        pytest.param(
            {"foo.json": '{"command": "echo -n \'Multiple arguments\'"}'},
            [["shlex_split(command)", ["echo", "-n", "Multiple arguments"]]],
            None,
            [],
            id="shlex_split",
        ),
        pytest.param(
            {"foo.json": '{"command": ["echo", "-n", "Multiple arguments"]}'},
            [["shlex_join(command)", "echo -n 'Multiple arguments'"]],
            None,
            [],
            id="shlex_join",
        ),
        pytest.param(
            {"foo.json": '{"n": 5.46}'},
            [["round(n)", 5]],
            None,
            [],
            id="round(n)",
        ),
        pytest.param(
            {"foo.json": '{"n": 5.46}'},
            [["round(n, `1`)", 5.5]],
            None,
            [],
            id="round(n, digits)",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [["range(`5`)", [0, 1, 2, 3, 4]]],
            None,
            [],
            id="range(stop)",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [["range(`1`, `6`)", [1, 2, 3, 4, 5]]],
            None,
            [],
            id="range(start, stop)",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [["range(`1`, `6`, `2`)", [1, 3, 5]]],
            None,
            [],
            id="range(start, stop, step)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["capitalize(foo)", "Bar"]],
            None,
            [],
            id="capitalize(string)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["center(foo, `5`)", " bar "]],
            None,
            [],
            id="center(string, width)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["center(foo, `5`, 's')", "sbars"]],
            None,
            [],
            id="center(string, width, fillchar)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bara"}'},
            [["count(foo, 'a')", 2]],
            None,
            [],
            id="count(string, sub)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "baraa"}'},
            [["count(foo, 'a', `2`)", 2]],
            None,
            [],
            id="count(string, sub, start)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "baraa"}'},
            [["count(foo, 'a', `1`, `3`)", 1]],
            None,
            [],
            id="count(string, sub, start, end)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["find(foo, 'a')", 1]],
            None,
            [],
            id="find(string, sub)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "baraa"}'},
            [["find(foo, 'a', `3`)", 3]],
            None,
            [],
            id="find(string, sub, start)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "baraa"}'},
            [["find(foo, 'a', `0`, `1`)", -1]],
            None,
            [],
            id="find(string, sub, start, end)",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["bar", "baz"]}'},
            [["find(foo, 'baz')", 1]],
            None,
            [],
            id="find(array, sub)",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["bar", "baz", "qux"]}'},
            [["find(foo, 'bar', `1`)", -1]],
            None,
            [],
            id="find(array, sub, start)",
        ),
        pytest.param(
            {"foo.json": '{"schema": "a is {0} and b is {1}"}'},
            [["format(schema, 'bar', `4`)", "a is bar and b is 4"]],
            None,
            [],
            id="format(string, *args)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["isalnum(foo)", True]],
            None,
            [],
            id="isalnum(string) returns true",
        ),
        pytest.param(
            {"foo.json": '{"foo": "."}'},
            [["isalnum(foo)", False]],
            None,
            [],
            id="isalnum(string) returns false",
        ),
        # all others is{funcsuffix} behave the same way: isalpha, isdigit, etc.
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["ljust(foo, `4`)", "bar "]],
            None,
            [],
            id="ljust(string, width)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["ljust(foo, `4`, 'a')", "bara"]],
            None,
            [],
            id="ljust(string, width, fillchar)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "  bab   "}'},
            [["strip(foo)", "bab"]],
            None,
            [],
            id="strip(string)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "  bab   "}'},
            [["lstrip(foo)", "bab   "]],
            None,
            [],
            id="lstrip(string)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "cbababcb"}'},
            [["strip(foo, 'bc')", "aba"]],
            None,
            [],
            id="strip(string, chars)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "aabbaabbcc"}'},
            [["partition(foo, 'bb')", ["aa", "bb", "aabbcc"]]],
            None,
            [],
            id="partition(string, sep)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "aabbaabbcc"}'},
            [["rpartition(foo, 'bb')", ["aabbaa", "bb", "cc"]]],
            None,
            [],
            id="rpartition(string, sep)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "aabbaabbcc"}'},
            [["removeprefix(foo, 'aab')", "baabbcc"]],
            None,
            [],
            id="removeprefix(string, prefix)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "aabbaabbcc"}'},
            [["removesuffix(foo, 'bcc')", "aabbaab"]],
            None,
            [],
            id="removesuffix(string, suffix)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "abccc"}'},
            [["split(foo, 'c', `2`)", ["ab", "", "c"]]],
            None,
            [],
            id="split(string, sep, maxsplit)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "abccc"}'},
            [["rsplit(foo, 'c', `2`)", ["abc", "", ""]]],
            None,
            [],
            id="rsplit(string, sep, maxsplit)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "a\\nb\\r\\nc"}'},
            [["splitlines(foo)", ["a", "b", "c"]]],
            None,
            [],
            id="splitlines(string)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "a\\nb\\r\\nc"}'},
            [["splitlines(foo, `true`)", ["a\n", "b\r\n", "c"]]],
            None,
            [],
            id="splitlines(string, keepends)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "aa"}'},
            [["zfill(foo, `4`)", "00aa"]],
            None,
            [],
            id="zfill(string, width)",
        ),
        pytest.param(
            {"foo.json": '{"foo": "ab"}'},
            [["enumerate(foo)", [[0, "a"], [1, "b"]]]],
            None,
            [],
            id="enumerate(string)",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["a", "b"]}'},
            [["enumerate(foo)", [[0, "a"], [1, "b"]]]],
            None,
            [],
            id="enumerate(array)",
        ),
        pytest.param(
            {"foo.json": '{"foo": {"a": 1, "b": 2}}'},
            [["enumerate(foo)", [[0, ["a", 1]], [1, ["b", 2]]]]],
            None,
            [],
            id="enumerate(object)",
        ),
        pytest.param(
            {"foo.json": '{"foo": {"a": 1, "b": 2}}'},
            [["to_items(foo)", [["a", 1], ["b", 2]]]],
            None,
            [],
            id="to_items(object)",
        ),
        pytest.param(
            {"foo.json": '{"foo": [["a", 1], ["b", 2]]}'},
            [["from_items(foo)", {"a": 1, "b": 2}]],
            None,
            [],
            id="from_items(object)",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [["op(os(), '==', '" + sys.platform + "')", True]],
            None,
            [],
            id="os()",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [
                [
                    "op(getenv('PWD'), '==', '" + os.environ.get("PWD") + "')",
                    True,
                ],
            ],
            None,
            [],
            id="getenv()",
        ),
        pytest.param(
            {"foo.json": "{}"},
            [
                [
                    (
                        "setenv('_PROJECT_CONFIG_TESTS_SETENV', 'true')"
                        "._PROJECT_CONFIG_TESTS_SETENV"
                    ),
                    "true",
                ],
                [
                    "getenv('_PROJECT_CONFIG_TESTS_SETENV')",
                    "true",
                ],
            ],
            None,
            [],
            id="setenv()",
        ),
    ),
)
def test_JMESPath_custom_functions(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "JMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
        deprecated="regex_matchall" in value[0][0],
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {},
            5,
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch",
                        "message": (
                            "The JMES path match tuples must be of"
                            " type array"
                        ),
                    },
                ),
            ],
            id="invalid-value-type",
        ),
        pytest.param(
            {},
            [],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch",
                        "message": (
                            "The JMES path match tuples must not be empty"
                        ),
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {},
            [["foo", "bar"], 6],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[1]",
                        "message": (
                            "The JMES path match tuple must be of type array"
                        ),
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {},
            [["foo", "bar"], ["foo", "bar", "baz", "qux"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[1]",
                        "message": (
                            "The JMES path match tuple must be of length 2 or 3"
                        ),
                    },
                ),
            ],
            id="invalid-value-item-length",
        ),
        pytest.param(
            {},
            [["foo", "bar"], [5, "bar"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[1][0]",
                        "message": (
                            "The JMES path expression must be of type string"
                        ),
                    },
                ),
            ],
            id="invalid-value-item-expression-type",
        ),
        pytest.param(
            {"foo.ext": False},
            [["foo", "bar"]],
            None,
            [],
            id="unexistent-file-skips",
        ),
        pytest.param(
            {"foo/": None},
            [["foo", "bar"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".files[0]",
                        "message": (
                            "A JMES path can not be applied to a directory"
                        ),
                        "file": "foo/",
                    },
                ),
            ],
            id="invalid-application-against-directory",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(keys(@", "a"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][0]",
                        "message": (
                            "Invalid JMESPath expression 'contains(keys(@'."
                            " Expected to return 'a', raised JMESPath"
                            " incomplete expression error:"
                            " Invalid jmespath expression:"
                            " Incomplete expression:\n"
                            '"contains(keys(@"\n'
                            "                ^"
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="invalid-expression-compilation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(@)", "a"]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "message": (
                            "Invalid JMESPath 'contains(@)'."
                            " Expected to return 'a', raised"
                            " JMESPath arity error: Expected 2 arguments"
                            " for function contains(),"
                            " received 1"
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="invalid-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(keys(@), 'a')", False]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "message": (
                            "JMESPath 'contains(keys(@), 'a')' does not match."
                            " Expected False, returned True"
                        ),
                        "file": "foo.json",
                        "fixed": False,
                        "fixable": False,
                    },
                ),
            ],
            id="expression-not-match",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(keys(@), 'a')", True]],
            None,
            [],
            id="expression-match",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(a, 'foobarbaz')", True]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "message": (
                            "Invalid JMESPath \"contains(a, 'foobarbaz')\"."
                            " Expected to return True, raised"
                            " JMESPath type error: In function"
                            " contains(), invalid type for value: 4, expected"
                            " one of: ['array', 'string'], received: \"number\""
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="invalid-expression-argument-type",
        ),
    ),
)
def test_JMESPathsMatch(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "JMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {},
            [],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The files - JMES path match tuples must be"
                            " of type object"
                        ),
                        "definition": ".ifJMESPathsMatch",
                    },
                ),
            ],
            id="invalid-value-type",
        ),
        pytest.param(
            {},
            {},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The files - JMES path match tuples must not"
                            " be empty"
                        ),
                        "definition": ".ifJMESPathsMatch",
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {},
            {"foo": 7},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuples must be of type array"
                        ),
                        "definition": ".ifJMESPathsMatch[foo]",
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {},
            {"foo": 5},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuples must be of type array"
                        ),
                        "definition": ".ifJMESPathsMatch[foo]",
                    },
                ),
            ],
            id="invalid-value-tuples-type",
        ),
        pytest.param(
            {},
            {"foo": []},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuples must not be empty"
                        ),
                        "definition": ".ifJMESPathsMatch[foo]",
                    },
                ),
            ],
            id="invalid-empty-value-tuples",
        ),
        pytest.param(
            {},
            {"foo": [["foo", "bar"], 8]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuple must be of type array"
                        ),
                        "definition": ".ifJMESPathsMatch[foo][1]",
                    },
                ),
            ],
            id="invalid-value-tuples-item-type",
        ),
        pytest.param(
            {},
            {"foo": [["foo", "bar"], ["foo", "bar", "baz"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuple must be of length 2"
                        ),
                        "definition": ".ifJMESPathsMatch[foo][1]",
                    },
                ),
            ],
            id="invalid-value-tuples-item-length",
        ),
        pytest.param(
            {},
            {"foo": [[True, "bar"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": "The JMES path must be of type string",
                        "definition": ".ifJMESPathsMatch[foo][0][0]",
                    },
                ),
            ],
            id="invalid-value-tuples-item-expression-type",
        ),
        pytest.param(
            {"foo.ext": False},
            {"bar.ext": [["foo", "bar"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifJMESPathsMatch[bar.ext]",
                        "file": "bar.ext",
                        "message": (
                            "The file to check if matches against JMES paths"
                            " does not exist"
                        ),
                    },
                ),
                (ResultValue, True),
            ],
            id="unexistent-file",
        ),
        pytest.param(
            {"bar/": None},
            {"bar/": [["foo", "bar"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifJMESPathsMatch[bar/]",
                        "message": (
                            "A JMES path can not be applied to a directory"
                        ),
                        "file": "bar/",
                    },
                ),
                (ResultValue, True),
            ],
            id="directory",
        ),
        pytest.param(
            {"foo.json": '{"a":'},
            {"foo.json": [["a", "b"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifJMESPathsMatch[foo.json]",
                        "file": "foo.json",
                        "message": (
                            "'foo.json' can't be serialized as a valid object:"
                            " Expecting value: line 1 column 6 (char 5)"
                        ),
                    },
                ),
                (ResultValue, True),
            ],
            id="unserializable-file",
        ),
        pytest.param(
            {"foo.json": "{}"},
            {"foo.json": [["contains(keys(@", "a"]]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifJMESPathsMatch[foo.json][0][0]",
                        "message": (
                            "Invalid JMESPath expression 'contains(keys(@'."
                            " Expected to return 'a', raised JMESPath"
                            " incomplete expression error: Invalid jmespath"
                            " expression: Incomplete expression:\n"
                            '"contains(keys(@"\n'
                            "                ^"
                        ),
                        "file": "foo.json",
                    },
                ),
                (ResultValue, True),
            ],
            id="invalid-expression-compilation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            {"foo.json": [["contains(@)", "a"]]},
            None,
            [
                (
                    Error,
                    {
                        "definition": ".ifJMESPathsMatch[foo.json][0]",
                        "message": (
                            "Invalid JMESPath 'contains(@)'."
                            " Expected to return 'a', raised"
                            " JMESPath arity error: Expected 2 arguments"
                            " for function contains(),"
                            " received 1"
                        ),
                        "file": "foo.json",
                    },
                ),
                (ResultValue, True),
            ],
            id="invalid-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            {"foo.json": [["contains(keys(@), 'a')", False]]},
            None,
            [
                (
                    ResultValue,
                    False,
                ),
            ],
            id="expression-not-match",
        ),
        pytest.param(
            {"bar.json": '{"foo": "bar"}'},
            {"bar.json": [["foo", "bar"]]},
            None,
            [(ResultValue, True)],
            id="expression-match",
        ),
    ),
)
def test_ifJMESPathsMatch(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "ifJMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "additional_files"),
    (
        pytest.param(
            {},
            5,
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch",
                        "message": "The pipes must be of type array",
                    },
                ),
            ],
            {},
            id="invalid-value-type",
        ),
        pytest.param(
            {},
            [],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch",
                        "message": "The pipes must not be empty",
                    },
                ),
            ],
            {},
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "content"},
            [5],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "message": ("The pipe must be of type array"),
                    },
                ),
            ],
            {},
            id="invalid-pipe-type",
        ),
        pytest.param(
            {"foo.ext": "content"},
            [["foo", "bar"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "message": ("The pipe must be, at least, of length 3"),
                    },
                ),
            ],
            {},
            id="invalid-pipe-length",
        ),
        pytest.param(
            {"foo.ext": "content"},
            [[5, "foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][0]",
                        "message": (
                            "The file expression must be of type string"
                        ),
                    },
                ),
            ],
            {},
            id="invalid-files-expression-type",
        ),
        pytest.param(
            {"foo.json": '["content"]'},
            [["", "foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][0]",
                        "message": ("The file expression must not be empty"),
                    },
                ),
            ],
            {},
            id="invalid-empty-files-expression",
        ),
        pytest.param(
            {"foo.json": '["content"]'},
            [["foo", "bar", 5, "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][2]",
                        "message": (
                            "The final expression must be of type string"
                        ),
                    },
                ),
            ],
            {},
            id="invalid-final-expression-type",
        ),
        pytest.param(
            {"foo.json": '["content"]'},
            [["foo", "bar", "", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][2]",
                        "message": ("The final expression must not be empty"),
                    },
                ),
            ],
            {},
            id="invalid-empty-final-expression",
        ),
        pytest.param(
            {"foo.json": '["content"]'},
            [["foo", "bar", "contains(", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][2]",
                        "message": (
                            "Invalid JMESPath expression 'contains('."
                            " Expected to return 'baz', raised JMESPath"
                            " incomplete expression error: Invalid"
                            " jmespath expression: Incomplete expression:\n"
                            '"contains("\n          ^'
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            {},
            id="invalid-final-expression-compilation",
        ),
        pytest.param(
            {"foo.json": '["content"]'},
            [["contains(", "foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][0]",
                        "message": (
                            "Invalid JMESPath expression 'contains('."
                            " Raised JMESPath incomplete expression error:"
                            " Invalid jmespath expression: Incomplete"
                            " expression:\n"
                            '"contains("\n          ^'
                        ),
                    },
                ),
            ],
            {},
            id="invalid-files-expression-compilation",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["contains([0], 'hello')", "foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][0]",
                        "file": "foo.json",
                        "message": (
                            "Invalid JMESPath \"contains([0], 'hello')\"."
                            " Raised JMESPath type error: In function"
                            " contains(), invalid type for value: 5,"
                            " expected one of: ['array', 'string'],"
                            ' received: "number"'
                        ),
                    },
                ),
            ],
            {},
            id="invalid-files-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", 5, "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1]",
                        "message": (
                            "The file path and expression tuple"
                            " must be of type array"
                        ),
                    },
                ),
            ],
            {},
            id="invalid-other-file-expression-type",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", ["foo"], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1]",
                        "message": (
                            "The file path and expression tuple"
                            " must be of length 2"
                        ),
                    },
                ),
            ],
            {},
            id="invalid-other-file-expression-length",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", [5, "foo"], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "message": "The file path must be of type string",
                    },
                ),
            ],
            {},
            id="invalid-other-file-type",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", ["", "foo"], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "message": "The file path must not be empty",
                    },
                ),
            ],
            {},
            id="invalid-empty-other-file",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", ["foo", 5], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][1]",
                        "message": "The expression must be of type string",
                    },
                ),
            ],
            {},
            id="invalid-other-expression-type",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", ["foo", ""], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][1]",
                        "message": "The expression must not be empty",
                    },
                ),
            ],
            {},
            id="invalid-empty-other-expression",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [["[0]", ["qux.ext", "type("], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1]",
                        "message": (
                            "Invalid JMESPath expression 'type('."
                            " Expected to return from applying the"
                            " expresion 'type(' to the file 'qux.ext',"
                            " raised JMESPath incomplete expression"
                            " error: Invalid jmespath expression:"
                            " Incomplete expression:\n"
                            '"type("\n      ^'
                        ),
                        "file": "qux.ext",
                    },
                ),
            ],
            {},
            id="invalid-other-expression-compilation",
        ),
        pytest.param(
            {"foo.json": "[5]", "qux.json": '{"foo": 8}'},
            [["[0]", ["qux.json", "contains(foo, 'hello')"], "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1]",
                        "message": (
                            "Invalid JMESPath \"contains(foo, 'hello')\"."
                            " Raised JMESPath type error: In function"
                            " contains(), invalid type for value: 8,"
                            " expected one of: ['array', 'string'],"
                            ' received: "number"'
                        ),
                        "file": "qux.json",
                    },
                ),
            ],
            {},
            id="invalid-other-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": "[5]", "qux.json": '{"foo": 8}'},
            [["[0]", ["qux.json", "foo"], "contains([1], 'hello')", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][2]",
                        "message": (
                            "Invalid JMESPath \"contains([1], 'hello')\"."
                            " Raised JMESPath type error: In function"
                            " contains(), invalid type for value: 8,"
                            " expected one of: ['array', 'string'],"
                            ' received: "number"'
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            {},
            id="invalid-final-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [
                [
                    "[0]",
                    ["qux.json", "foo"],
                    "[contains(@, `5`), contains(@, `8`)]",
                    [True, True],
                ],
            ],
            None,
            [],
            {"qux.json": '{"foo": 8}'},
            id="match",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [
                [
                    "[0]",
                    ["qux.ext", "foo"],
                    "[contains(@, `5`), contains(@, `7`)]",
                    [True, True],
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "JMESPath '[contains(@, `5`), contains(@, `7`)]'"
                            " does not match. Expected [True, True], returned"
                            " [True, False]"
                        ),
                    },
                ),
            ],
            {"qux.ext": '{"foo": 8}'},
            id="not-match",
        ),
        pytest.param(
            {"foo.json": "[5]"},
            [
                [
                    "[0]",
                    ["bar.json", "foo"],
                    ["baz.json", "foo"],
                    (
                        "[contains(@, `5`), contains(@, `7`),"
                        " contains(@, `8`), contains(@, `9`)]"
                    ),
                    [True, True],
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "JMESPath '[contains(@, `5`), contains(@, `7`),"
                            " contains(@, `8`), contains(@, `9`)]'"
                            " does not match. Expected [True, True], returned"
                            " [True, False, True, True]"
                        ),
                    },
                ),
            ],
            {"bar.json": '{"foo": 8}', "baz.json": '{"foo": 9}'},
            id="not-match-multiple-other-files",
        ),
        pytest.param(
            {"foo.json": False},
            [
                [
                    "@",
                    ["qux.ext", "foo"],
                    "@",
                    True,
                ],
            ],
            None,
            [],
            {},
            id="file-not-exists",
        ),
        pytest.param(
            {"foo": None},
            [
                [
                    "@",
                    ["qux.ext", "foo"],
                    "@",
                    True,
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".files[0]",
                        "file": "foo/",
                        "message": (
                            "A JMES path can not be applied to a directory"
                        ),
                    },
                ),
            ],
            {},
            id="verb-applyied-to-directory",
        ),
        pytest.param(
            {"foo.json": '{"bar": {"baz": true}}'},
            [
                [
                    "bar",
                    "[0].baz",
                    True,
                ],
            ],
            None,
            [],
            {},
            id="other-files-are-optional",
        ),
        pytest.param(
            {"foo.json": '{"bar": {"baz": true}}'},
            [
                [
                    "bar",
                    ["qux.ext", "foo"],
                    "baz",
                    True,
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "file": "qux.ext",
                        "message": "'qux.ext' file not found",
                    },
                ),
            ],
            {},
            id="unexistent-other-file-raises-error",
        ),
        pytest.param(
            {"foo.json": '{"bar": {"baz": true}}'},
            [
                [
                    "bar",
                    ["qux.json", "foo"],
                    "baz",
                    True,
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "file": "qux.json",
                        "message": (
                            "'qux.json' can't be serialized as a valid object:"
                            " Expecting property name enclosed in double"
                            " quotes: line 1 column 2 (char 1)"
                        ),
                    },
                ),
            ],
            {"qux.json": "{"},
            id="unserializable-other-file-raises-error",
        ),
    ),
)
def test_crossJMESPathsMatch(
    files,
    value,
    rule,
    expected_results,
    additional_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "crossJMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
        additional_files=additional_files,
    )


@mark_end2end
@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.json": '{"bar": {"baz": true}}'},
            [
                [
                    "bar",
                    [
                        (
                            "gh://mondeja/project-config/tests/data/styles"
                            "/bar/baz.toml"
                        ),
                        "foo",
                    ],
                    "baz",
                    True,
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "file": (
                            "gh://mondeja/project-config/tests/data/"
                            "styles/bar/baz.toml"
                        ),
                        "message": (
                            "Impossible to fetch "
                            "'https://raw.githubusercontent.com/mondeja/"
                            "project-config/master/tests/data/styles/bar/"
                            "baz.toml' after 0.5 seconds. Possibly caused by:"
                            " HTTP Error 404: Not Found"
                        ),
                    },
                ),
            ],
            id="unexistent-online-other-file-raises-error",
        ),
        pytest.param(
            {"foo.json": '{"bar": {"baz": true}}'},
            [
                [
                    "bar",
                    [
                        (
                            "gh://mondeja/project-config/tests/data/styles/"
                            "foo/style-1.json5"
                        ),
                        "extends",
                    ],
                    "[[0].baz, type([1])]",
                    [True, "array"],
                ],
            ],
            None,
            [],
            id="unexistent-online-other-file-ok",
        ),
    ),
)
def test_crossJMESPathsMatch_online_sources(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
    monkeypatch,
):
    monkeypatch.setenv("PROJECT_CONFIG_REQUESTS_TIMEOUT", "0.5")
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "crossJMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
    )
