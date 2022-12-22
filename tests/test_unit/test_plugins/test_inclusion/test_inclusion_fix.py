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
                (
                    Error,
                    {
                        "definition": ".includeLines[1]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": "Expected line 'Other line' not found",
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
            {"file.txt": "This line must be in .gitgnore"},
            [
                "This line must be",
                [
                    "foobarbaz",
                    "[?@ != 'This line must be in .gitgnore']",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".includeContent[1]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Content 'foobarbaz' expected to be"
                            " included not found"
                        ),
                    },
                ),
            ],
            {"file.txt": ""},
            id="manual-fix-basic-ok",
        ),
        pytest.param(
            {"file.txt": "Some text"},
            [["text", bool]],
            None,
            [
                (
                    InterruptingError,
                    # TODO: Show a better representation of type primitives
                    # like bool in error messages like this:
                    {
                        "definition": ".includeContent[0]",
                        "message": (
                            "The '[content-to-include, fixer_query]'"
                            " array  items '['text', <class 'bool'>]'"
                            " must be of type string"
                        ),
                    },
                ),
            ],
            {"file.txt": "Some text"},
            id="fixer-query-invalid-type",
        ),
        pytest.param(
            {"file.txt": "Existent content"},
            [
                "Existent",
                ["Other line", "`['"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeContent[1]",
                        "message": (
                            'Invalid JMESPath expression "`[\'".'
                            " Raised JMESPath lexing error:"
                            " Bad jmespath expression: Unclosed"
                            " ` delimiter:\n`['\n^"
                        ),
                    },
                ),
            ],
            {"file.txt": "Existent content"},
            id="fixer-query-compilation-error",
        ),
        pytest.param(
            {"file.txt": "Some content"},
            [
                "Some content",
                ["Other unexistent content", "[to_string(contains(`1`, `1`))]"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".includeContent[1]",
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
            {"file.txt": "Some content"},
            id="fixer-query-evaluation-error",
        ),
        pytest.param(
            {"file.txt": "Some content\n"},
            [
                ["Other content", "['Other content']"],
            ],
            (),
            [
                (
                    Error,
                    {
                        "definition": ".includeContent[0]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Content 'Other content' expected to be"
                            " included not found"
                        ),
                    },
                ),
            ],
            {"file.txt": "Other content\n"},
            id="fixer-query-not-diff-ok",
        ),
    ),
)
def test_includeContent_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "includeContent",
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
            {".gitignore": "This line must not be in .gitgnore\nfoo\nbar"},
            ["This line must not be in .gitgnore", ["Other line", "@", 5555]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeLines[1]",
                        "message": (
                            "The '[expected-line, fixer_query]' array"
                            " '['Other line', '@', 5555]' must be of length 2"
                        ),
                    },
                ),
            ],
            {".gitignore": "This line must not be in .gitgnore\nfoo\nbar"},
            id="invalid-value-item-length",
        ),
        pytest.param(
            {".gitignore": "This line must not be in .gitgnore\nfoo\nbar"},
            ["This line must not be in .gitgnore", ["Other line", 5555]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeLines[1]",
                        "message": (
                            "The '[expected-line, fixer_query]' array items"
                            " '['Other line', 5555]' must be of type string"
                        ),
                    },
                ),
            ],
            {".gitignore": "This line must not be in .gitgnore\nfoo\nbar"},
            id="invalid-value-subitem-type",
        ),
        pytest.param(
            {"file.txt": "This line must not be in .gitgnore\nfoo\nbar"},
            [
                "Other line",
                [
                    "This line must not be in .gitgnore",
                    "['foo', 'New inclusion']",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".excludeLines[1]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Found expected line to exclude"
                            " 'This line must not be in .gitgnore'"
                        ),
                    },
                ),
            ],
            {"file.txt": "foo\nNew inclusion\n"},
            id="fixer-query-override-ok",
        ),
        pytest.param(
            {"file.txt": "A line"},
            [
                "This line must not be in .gitgnore",
                ["A line", "`['"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeLines[1]",
                        "message": (
                            'Invalid JMESPath expression "`[\'".'
                            " Raised JMESPath lexing error:"
                            " Bad jmespath expression: Unclosed `"
                            " delimiter:\n`['\n^"
                        ),
                    },
                ),
            ],
            {"file.txt": "A line"},
            id="fixer-query-compilation-error",
        ),
        pytest.param(
            {"file.txt": "A line"},
            [
                "This line must not be in .gitgnore",
                ["A line", "[to_string(contains(`1`, `1`))]"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeLines[1]",
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
            {"file.txt": "A line"},
            id="fixer-query-evaluation-error",
        ),
    ),
)
def test_excludeLines_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "excludeLines",
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
            (),
            [
                (
                    Error,
                    {
                        "definition": ".excludeContent[0]",
                        "file": "file.txt",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "Found expected content to exclude 'Other line'"
                        ),
                    },
                ),
            ],
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
