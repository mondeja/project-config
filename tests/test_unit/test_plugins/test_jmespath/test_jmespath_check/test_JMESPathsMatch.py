import pytest

from project_config import Error, InterruptingError
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
                            "The JMES path match tuples must be of type array"
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
                            " Raised JMESPath arity error:"
                            " Expected 2 arguments"
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
                        "fixable": True,
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
                            " Raised JMESPath type error: In function"
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
