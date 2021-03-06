import pytest

from project_config import Error, InterruptingError
from project_config.plugins.inclusion import InclusionPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
        pytest.param(
            {".gitignore": ""},
            ["This line must be in .gitgnore", ["Other line", "@", 5555]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[1]",
                        "message": (
                            "The '[expected-line, fixer_query]' array"
                            " '['Other line', '@', 5555]' must be of length 2"
                        ),
                    },
                ),
            ],
            {".gitignore": ""},
            id="invalid-value-item-length",
        ),
        pytest.param(
            {".gitignore": ""},
            ["This line must be in .gitgnore", ["Other line", 5555]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[1]",
                        "message": (
                            "The '[expected-line, fixer_query]' array items"
                            " '['Other line', 5555]' must be of type string"
                        ),
                    },
                ),
            ],
            {".gitignore": ""},
            id="invalid-value-subitem-type",
        ),
        pytest.param(
            {"file.txt": ""},
            [
                "This line must be in .gitgnore",
                ["Other line", "['foo', 'Other inclusion']"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".includeLines[0]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Expected line 'This line must be in"
                            " .gitgnore' not found"
                        ),
                    },
                ),
            ],
            {"file.txt": "foo\nOther inclusion\n"},
            id="fixer-query-override-ok",
        ),
        pytest.param(
            {"file.txt": ""},
            [
                "This line must be in .gitgnore",
                ["Other line", "`['"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[0]",
                        "message": (
                            'Invalid JMESPath expression "`[\'".'
                            " Raised JMESPath lexing error:"
                            " Bad jmespath expression: Unclosed `"
                            " delimiter:\n`['\n^"
                        ),
                    },
                ),
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[1]",
                        "message": (
                            'Invalid JMESPath expression "`[\'".'
                            " Raised JMESPath lexing error:"
                            " Bad jmespath expression: Unclosed"
                            " ` delimiter:\n`['\n^"
                        ),
                    },
                ),
            ],
            {"file.txt": ""},
            id="fixer-query-compilation-error",
        ),
        pytest.param(
            {"file.txt": ""},
            [
                "This line must be in .gitgnore",
                ["Other line", "[to_string(contains(`1`, `1`))]"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[0]",
                        "message": (
                            "Invalid JMESPath"
                            " '[to_string(contains(`1`, `1`))]'. Raised"
                            " JMESPath type error: In function contains(),"
                            " invalid type for value: 1, expected one of:"
                            " ['array', 'string'], received: \"number\""
                        ),
                    },
                ),
                (
                    InterruptingError,
                    {
                        "definition": ".includeLines[1]",
                        "message": (
                            "Invalid JMESPath"
                            " '[to_string(contains(`1`, `1`))]'. Raised"
                            " JMESPath type error: In function contains(),"
                            " invalid type for value: 1, expected one of:"
                            " ['array', 'string'], received: \"number\""
                        ),
                    },
                ),
            ],
            {"file.txt": ""},
            id="fixer-query-evaluation-error",
        ),
    ),
)
def test_includeLines_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "includeLines",
        files,
        value,
        rule,
        expected_results,
        fix=True,
        expected_files=expected_files,
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
        pytest.param(
            {"file.txt": "This line must not be in .gitgnore"},
            [
                "A line not included",
                [
                    "This line must not be in .gitgnore",
                    "[?@ != 'This line must not be in .gitgnore']",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".excludeContent[1]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Found expected content to exclude"
                            " 'This line must not be in .gitgnore'"
                        ),
                    },
                ),
            ],
            {"file.txt": ""},
            id="manual-fix-basic-ok",
        ),
        pytest.param(
            {"file.txt": ""},
            [["A line not included", bool]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[0]",
                        "message": (
                            "The '[content-to-exclude, fixer_query]'"
                            " array  items '['A line not included',"
                            " <class 'bool'>]' must be of type string"
                        ),
                    },
                ),
            ],
            {"file.txt": ""},
            id="fixer-query-invalid-type",
        ),
        pytest.param(
            {"file.txt": "Other line"},
            [
                "This line must not be in .gitgnore",
                ["Other line", "`['"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[1]",
                        "message": (
                            'Invalid JMESPath expression "`[\'".'
                            " Raised JMESPath lexing error:"
                            " Bad jmespath expression: Unclosed"
                            " ` delimiter:\n`['\n^"
                        ),
                    },
                ),
            ],
            {"file.txt": "Other line"},
            id="fixer-query-compilation-error",
        ),
        pytest.param(
            {"file.txt": "Other line"},
            [
                "This line must be in .gitgnore",
                ["Other line", "[to_string(contains(`1`, `1`))]"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[1]",
                        "message": (
                            "Invalid JMESPath"
                            " '[to_string(contains(`1`, `1`))]'."
                            " Raised JMESPath type error: In function"
                            " contains(), invalid type for value: 1,"
                            " expected one of: ['array', 'string'],"
                            ' received: "number"'
                        ),
                    },
                ),
            ],
            {"file.txt": "Other line"},
            id="fixer-query-evaluation-error",
        ),
        pytest.param(
            {"file.txt": "Other line\n"},
            [
                ["Other line", "['Other line']"],
            ],
            None,
            [],
            {"file.txt": "Other line\n"},
            id="fixer-query-not-diff-ok",
        ),
    ),
)
def test_excludeContent_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "excludeContent",
        files,
        value,
        rule,
        expected_results,
        fix=True,
        expected_files=expected_files,
    )
