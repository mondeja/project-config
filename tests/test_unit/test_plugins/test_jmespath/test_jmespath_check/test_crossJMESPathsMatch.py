import pytest

from project_config import Error, InterruptingError
from project_config.plugins.jmespath import JMESPathPlugin
from testing_helpers import mark_end2end


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
        pytest.param(
            # When a file query is a JMESPath literal, the file is
            # not serialized.
            #
            # Serialization of Python files require their execution
            {"foo.py": 'raise Exception("The file has been executed!")'},
            [
                [
                    "`null`",  # literal as JMESPath expression
                    ["foo.py?text", "[0]"],
                    "[1]",
                    'raise Exception("The file has been executed!")',
                ],
            ],
            None,
            [],
            {},
            id="skip-files-serialization-when-files-query-is-jp-literal",
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
                            "'https://google.com/mondeja/"
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
