import pytest

from project_config import Error, InterruptingError, ResultValue
from project_config.plugins.inclusion import InclusionPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.ext": "foo"},
            5,
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": "The value must be of type array",
                        "definition": ".includeLines",
                    },
                ),
            ],
            id="invalid-value-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            [],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": "The value must not be empty",
                        "definition": ".includeLines",
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foo", 5],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The expected line '5' must be of type string or array"
                        ),
                        "definition": ".includeLines[1]",
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foo", ""],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": "Expected line must not be empty",
                        "definition": ".includeLines[1]",
                    },
                ),
            ],
            id="invalid-empty-value-item",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foo", "bar", "foo", "baz"],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": "Duplicated expected line 'foo'",
                        "definition": ".includeLines[2]",
                    },
                ),
            ],
            id="invalid-duplicated-value-item",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foo"],
            None,
            [],
            id="file-one-line-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["bar"],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".includeLines[0]",
                        "file": "foo.ext",
                        "fixed": False,
                        "fixable": True,
                        "message": "Expected line 'bar' not found",
                    },
                ),
            ],
            id="file-one-line-no-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo\r\nbar\r\nbaz\r\n"},
            ["foo", "baz"],
            None,
            [],
            id="file-two-lines-match-two-lines",
        ),
        pytest.param(
            {"foo": None},
            ["foo", "baz"],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".files[0]",
                        "file": "foo/",
                        "message": (
                            "Directory found but the verb 'includeLines'"
                            " does not accepts directories as inputs"
                        ),
                    },
                ),
            ],
            id="directory",
        ),
        pytest.param(
            {"foo": False},
            ["foo", "baz"],
            None,
            [],
            id="file-not-exists",
        ),
    ),
)
def test_includeLines(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "includeLines",
        files,
        value,
        rule,
        expected_results,
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.ext": "foo"},
            5,
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines",
                        "message": "The value must be of type object",
                    },
                ),
            ],
            id="invalid-value-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines",
                        "message": "The value must not be empty",
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"": ["foo"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines",
                        "message": "File paths must not be empty",
                    },
                ),
            ],
            id="invalid-empty-fpath",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": 5},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo.ext]",
                        "message": (
                            "The expected lines '5' must be of type array"
                        ),
                    },
                ),
            ],
            id="invalid-expected-lines-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": []},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo.ext]",
                        "message": "Expected lines must not be empty",
                    },
                ),
            ],
            id="invalid-empty-expected-lines",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": ["foo", 5]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo.ext][1]",
                        "file": "foo.ext",
                        "message": (
                            "The expected line '5' must be of type string"
                        ),
                    },
                ),
            ],
            id="invalid-expected-line-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": ["foo", "\r\n"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo.ext][1]",
                        "file": "foo.ext",
                        "message": "Expected line must not be empty",
                    },
                ),
            ],
            id="invalid-empty-expected-line",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": ["foo", "\nfoo\r\n"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo.ext][1]",
                        "file": "foo.ext",
                        "message": "Duplicated expected line 'foo'",
                    },
                ),
            ],
            id="invalid-duplicated-expected-line",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": ["foo"]},
            None,
            [],
            id="file-one-line-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"foo.ext": ["bar"]},
            None,
            [(ResultValue, False)],
            id="file-one-line-no-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            {"bar.ext": ["bar"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[bar.ext]",
                        "file": "bar.ext",
                        "message": (
                            "File specified in conditional"
                            " 'ifIncludeLines' not found"
                        ),
                    },
                ),
            ],
            id="file-not-exists",
        ),
        pytest.param(
            {"foo.ext": "foo\nbar"},
            {"foo.ext": ["foo"]},
            None,
            [],
            id="file-two-lines-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo\nbar"},
            {"foo.ext": ["foo", "bar"]},
            None,
            [],
            id="file-two-lines-match-two-lines",
        ),
        pytest.param(
            {"foo.ext": "foo\r\nbar\r\nbaz"},
            {"foo.ext": ["bar", "baz"]},
            None,
            [],
            id="windows-newlines",
        ),
        pytest.param(
            {"foo": None},
            {"foo": ["foo", "bar"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo]",
                        "file": "foo/",
                        "message": (
                            "Directory found but the conditional"
                            " 'ifIncludeLines' does not accepts"
                            " directories as inputs"
                        ),
                    },
                ),
            ],
            id="directory",
        ),
        pytest.param(
            {"foo": None, "bar": None},
            {"foo": ["foo"], "bar": ["bar"]},
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".ifIncludeLines[foo]",
                        "file": "foo/",
                        "message": (
                            "Directory found but the conditional"
                            " 'ifIncludeLines' does not accepts"
                            " directories as inputs"
                        ),
                    },
                ),
            ],
            id="two-directories",
        ),
        pytest.param(  # all lines must be in file to match
            {"foo.ext": "foo\nbar"},
            {"foo.ext": ["bar", "baz"]},
            None,
            [(ResultValue, False)],
            id="file-two-lines-match-one-line-no-match-one-line",
        ),
    ),
)
def test_ifIncludeLines(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "ifIncludeLines",
        files,
        value,
        rule,
        expected_results,
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
        pytest.param(
            {"foo.ext": False},
            5,
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent",
                        "message": (
                            "The contents to exclude must be of type array"
                        ),
                    },
                ),
            ],
            id="invalid-value-type",
        ),
        pytest.param(
            {"foo.ext": False},
            [],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent",
                        "message": (
                            "The contents to exclude must not be empty"
                        ),
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "bar"},
            ["foo", 5],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[1]",
                        "message": (
                            "The content to exclude '5' must be of type string or array"
                        ),
                        "file": "foo.ext",
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {"foo.ext": "bar"},
            ["foo", ""],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[1]",
                        "message": "The content to exclude must not be empty",
                        "file": "foo.ext",
                    },
                ),
            ],
            id="invalid-empty-value-item",
        ),
        pytest.param(
            {"foo.ext": "bar"},
            ["foo", "baz", "foo"],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".excludeContent[2]",
                        "message": "Duplicated content to exclude 'foo'",
                        "file": "foo.ext",
                    },
                ),
            ],
            id="invalid-duplicated-value-item",
        ),
        pytest.param(
            {"foo.ext": False},
            ["foo"],
            None,
            [],
            id="unexistent-file",
        ),
        pytest.param(
            {"foo": None},
            ["foo"],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".files[0]",
                        "file": "foo/",
                        "message": (
                            "Directory found but the verb 'excludeContent'"
                            " does not accepts directories as inputs"
                        ),
                    },
                ),
            ],
            id="apply-to-directory",
        ),
        pytest.param(
            {"foo.ext": "foo bar\nbaz"},
            ["foo"],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".excludeContent[0]",
                        "file": "foo.ext",
                        "message": "Found expected content to exclude 'foo'",
                        "fixable": False,
                        "fixed": False,
                    },
                ),
            ],
            id="content-included",
        ),
        pytest.param(
            {"foo.ext": "foo bar\nbaz"},
            ["qux"],
            None,
            [],
            id="content-excluded",
        ),
    ),
)
def test_excludeContent(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        InclusionPlugin,
        "excludeContent",
        files,
        value,
        rule,
        expected_results,
    )
