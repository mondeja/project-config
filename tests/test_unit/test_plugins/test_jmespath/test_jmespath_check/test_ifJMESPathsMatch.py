import pytest
from project_config import Error, InterruptingError, ResultValue
from project_config.plugins.jmespath import JMESPathPlugin


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
                            "The files - JMES path match"
                            " tuples must not be empty"
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
                            "The file to check if matches against"
                            " JMES paths does not exist"
                        ),
                    },
                ),
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
                            "'foo.json' can't be serialized as a"
                            " valid object: Expecting value: line"
                            " 1 column 6 (char 5)"
                        ),
                    },
                ),
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
                            " Raised JMESPath arity error:"
                            " Expected 2 arguments"
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
