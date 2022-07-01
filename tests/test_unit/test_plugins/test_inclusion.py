import pytest

from project_config import Error, InterruptingError, ResultValue
from project_config.plugins.inclusion import InclusionPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results"),
    (
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
            {"foo.ext": ["foo"]},
            None,
            [(ResultValue, True)],
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
            [(ResultValue, True)],
            id="file-two-lines-match-one-line",
        ),
        pytest.param(
            {"foo.ext": "foo\nbar"},
            {"foo.ext": ["foo", "bar"]},
            None,
            [(ResultValue, True)],
            id="file-two-lines-match-two-lines",
        ),
        pytest.param(
            {"foo.ext": "foo\r\nbar\r\nbaz"},
            {"foo.ext": ["bar", "baz"]},
            None,
            [(ResultValue, True)],
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