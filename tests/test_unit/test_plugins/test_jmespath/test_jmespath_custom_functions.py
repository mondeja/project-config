import os
import sys

import pytest

from project_config import Error
from project_config.plugins.jmespath import JMESPathPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_match('^bar$', foo)", True]],
            None,
            [],
            id="regex_match() returns true",
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
            id="regex_match() returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["bar", "baz"]}'},
            [["regex_matchall('^ba[rz]$', foo)", True]],
            None,
            [],
            id="regex_matchall() returns true",
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
            id="regex_matchall() returns false",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^bar$', foo)", ["bar"]]],
            None,
            [],
            id="regex_search() returns full",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^(b)(a)(r)$', foo)", ["b", "a", "r"]]],
            None,
            [],
            id="regex_search() returns group",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^baz$', foo)", []]],
            None,
            [],
            id="regex_search() returns null",
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
            {"foo.json": '{"foo": "$bar"}'},
            [["regex_match(regex_escape('$'), foo)", True]],
            None,
            [],
            id="regex_escape()",
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
                            " letters than', foo)\". Raised JMESPath error:"
                            " Invalid operator"
                            " 'has the same letters than' passed to op()"
                            " function at index 0, expected one of: <, <=,"
                            " ==, !=, >=, >, is, is_not, is-not, is not,"
                            " isNot, +, &, and, //, <<, %, *, @, |, or, **,"
                            " >>, -, /, ^, count_of, count of, count-of,"
                            " countOf, index_of, index of, index-of, indexOf"
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
            {"foo.json": '{"foo": "foo", "bar": "bar", "baz": "baz"}'},
            [["op(foo, '+', bar, '+', baz)", "foobarbaz"]],
            None,
            [],
            id="op with multiple positional string arguments",
        ),
        pytest.param(
            {"foo.json": '{"foo": 5, "bar": 3, "baz": 4}'},
            [["op(foo, '+', bar, '-', baz)", 4]],
            None,
            [],
            id="op with multiple positional number arguments",
        ),
        pytest.param(
            {"foo.json": '{"foo": 5, "bar": 3, "baz": 4}'},
            [["op(foo, '+', bar, `5`, baz)", 4]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "foo.json",
                        "message": (
                            "Invalid JMESPath \"op(foo, '+', bar, `5`, baz)\"."
                            " Raised JMESPath error:"
                            " Invalid operator '5' passed to op() function at"
                            " index 2, expected one of: <, <=, ==, !=, >=, >,"
                            " is, is_not, is-not, is not, isNot, +, &, and,"
                            " //, <<, %, *, @, |, or, **, >>, -, /, ^,"
                            " count_of, count of, count-of, countOf,"
                            " index_of, index of, index-of, indexOf"
                        ),
                    },
                ),
            ],
            id="op-invalid-second-operator-type",
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
                    "op(type(getenv('PATH')), '==', type('"
                    + os.environ.get("PATH")
                    + "'))",
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
            {"foo.json": '{"foo": "bar1234"}'},
            [
                [
                    (
                        "[starts_with(foo, ['baz', 'bar']),"
                        " starts_with(foo, ['abc', '234'])]"
                    ),
                    [True, False],
                ],
            ],
            None,
            [],
            id="starts_with() accepts an array",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar1234"}'},
            [
                [
                    (
                        "[ends_with(foo, ['234', 'r12']),"
                        " ends_with(foo, ['bar', 'qux'])]"
                    ),
                    [True, False],
                ],
            ],
            None,
            [],
            id="ends_with() accepts an array",
        ),
    ),
)
def test_JMESPath_expanded_standard_functions(
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
