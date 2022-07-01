import pytest

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
            [["foo", "bar"], ["foo", "bar", "baz"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[1]",
                        "message": (
                            "The JMES path match tuple must be of length 2"
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
                        "definition": ".crossJMESPathsMatch",
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
                        "definition": ".crossJMESPathsMatch",
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
            [6],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuple must be of type array"
                        ),
                        "definition": ".crossJMESPathsMatch[0]",
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {},
            [["a", "b", "c"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path match tuple must be of length 2"
                        ),
                        "definition": ".crossJMESPathsMatch[0]",
                    },
                ),
            ],
            id="invalid-value-item-length",
        ),
        pytest.param(
            {},
            [[5, "b"]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path expression must be of type string"
                        ),
                        "definition": ".crossJMESPathsMatch[0][0]",
                    },
                ),
            ],
            id="invalid-expression-type",
        ),
        pytest.param(
            {},
            [["foo", 5]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The file and JMES path expression array from which"
                            " the expected value will be taken must be"
                            " of type array"
                        ),
                        "definition": ".crossJMESPathsMatch[0][1]",
                    },
                ),
            ],
            id="invalid-ev-type",
        ),
        pytest.param(
            {},
            [["foo", ["a", "b", "c"]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The file and JMES path expression from"
                            " which the expected value will be taken"
                            " must be of length 2"
                        ),
                        "definition": ".crossJMESPathsMatch[0][1]",
                    },
                ),
            ],
            id="invalid-ev-length",
        ),
        pytest.param(
            {},
            [["foo", [5, "b"]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The file from which the expected value"
                            " will be taken must be of type string"
                        ),
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                    },
                ),
            ],
            id="invalid-ev-file-type",
        ),
        pytest.param(
            {},
            [["foo", ["a", 5]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The JMES path expression to query the file"
                            " from which the expected value will be"
                            " taken must be of type string"
                        ),
                        "definition": ".crossJMESPathsMatch[0][1][1]",
                    },
                ),
            ],
            id="invalid-ev-expression-type",
        ),
        pytest.param(
            {"foo.ext": False},
            [["foo", ["bar", "baz"]]],
            None,
            [],
            id="unexistent-file-skips",
        ),
        pytest.param(
            {"foo/": None},
            [["foo", ["bar", "baz"]]],
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
            [["contains(keys(@", ["foo.json", "baz"]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][0]",
                        "message": (
                            "Invalid JMESPath expression 'contains(keys(@'."
                            " Expected to return from applying the"
                            " expresion 'baz' to the file 'foo.json',"
                            " raised JMESPath incomplete expression error:"
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
            [["a", ["foo.json", "contains(keys(@"]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][1]",
                        "message": (
                            "Invalid JMESPath expression 'contains(keys(@'."
                            " Expected to return from applying the"
                            " expresion 'contains(keys(@' to the file"
                            " 'foo.json', raised JMESPath incomplete"
                            " expression error: Invalid jmespath expression:"
                            " Incomplete expression:\n"
                            '"contains(keys(@"\n'
                            "                ^"
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="invalid-ev-expression-compilation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["contains(@)", ["foo.json", "a"]]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "message": (
                            "Invalid JMESPath 'contains(@)'."
                            " Expected to return 4, raised"
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
            {"foo.json": '{"a": {"b": 4}}'},
            [["b", ["foo.json", "contains(@)"]]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".crossJMESPathsMatch[0][1]",
                        "message": (
                            "Invalid JMESPath 'contains(@)'."
                            " Raised JMESPath arity error: Expected 2"
                            " arguments for function contains(), received 1"
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="invalid-ev-expression-evaluation",
        ),
        pytest.param(
            {"foo.json": '{"a": 4}'},
            [["b", ["foo.json", "a"]]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".crossJMESPathsMatch[0]",
                        "message": (
                            "JMESPath 'b' does not match."
                            " Expected 4, returned None"
                        ),
                        "file": "foo.json",
                    },
                ),
            ],
            id="expression-not-match",
        ),
        pytest.param(
            {"foo.json": '{"a": 4, "b": 4}'},
            [["b", ["foo.json", "b"]]],
            None,
            [],
            id="expression-match",
        ),
        pytest.param(
            {"foo.json": '{"a": 4, "b": 4}'},
            [["b", ["bar.json", "b"]]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".crossJMESPathsMatch[0][1][0]",
                        "file": "bar.json",
                        "message": "File 'bar.json' does not exist",
                    },
                ),
            ],
            id="ev-file-not-exists",
        ),
    ),
)
def test_crossJMESPathsMatch(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "crossJMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
    )
