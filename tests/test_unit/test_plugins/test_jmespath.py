import pytest

from project_config import Error, InterruptingError, ResultValue
from project_config.plugins.jmespath import JMESPathPlugin


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
                            "The JMES path - match tuples must be of"
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
                            "The JMES path - match tuples must not be empty"
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
                            "The JMES path - match tuple must be"
                            " of type array"
                        ),
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {},
            [["foo", "bar"], ["foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[1]",
                        "message": (
                            "The JMES path - match tuple must be of length 2"
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
                            " Expected to return 'a', raised JMESPath parsing"
                            " error: Invalid jmespath expression:"
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
                            " JMESPath error: Expected 2 arguments"
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
                            "Invalid JMESPath \"contains(a, 'foobarbaz')\""
                            " in context. Expected to return True, raised"
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
            {"foo.json": '{"foo": "bar"}'},
            [["regex_match('^bar$', foo)", True]],
            None,
            [],
            id="regex_match->true",
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
                    },
                ),
            ],
            id="regex_match->false",
        ),
        pytest.param(
            {"foo.json": '{"foo": ["bar", "baz"]}'},
            [["regex_matchall('^ba[rz]$', foo)", True]],
            None,
            [],
            id="regex_matchall->true",
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
                    },
                ),
            ],
            id="regex_matchall->false",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^bar$', foo)", ["bar"]]],
            None,
            [],
            id="regex_search->full",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^(b)(a)(r)$', foo)", ["b", "a", "r"]]],
            None,
            [],
            id="regex_search->group",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["regex_search('^baz$', foo)", []]],
            None,
            [],
            id="regex_search->null",
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
            id="op->invalid-operator",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["op(foo, '==', foo)", True]],
            None,
            [],
            id="op->true",
        ),
        pytest.param(
            {"foo.json": '{"foo": "bar"}'},
            [["op(foo, '!=', foo)", False]],
            None,
            [],
            id="op->false",
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
            [],  # must be a dict
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
                            "The JMES path - match tuple must be of type array"
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
                            "The JMES path - match tuple must be of length 2"
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
            [(ResultValue, True)],
            id="unexistent-file-skips",
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
                # this result does not matter because the check will be
                # interrupted because of the previous InterruptingError
                (ResultValue, True),
            ],
            id="invalid-application-against-directory",
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
                            " Expected to return 'a', raised JMESPath parsing"
                            " error: Invalid jmespath expression:"
                            " Incomplete expression:\n"
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
                            " JMESPath error: Expected 2 arguments"
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
            {"bar.ext": '{"foo": "bar"}'},
            {"bar.ext": [["foo", "bar"]]},
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
