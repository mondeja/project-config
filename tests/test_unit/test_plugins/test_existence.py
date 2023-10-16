import pytest

from project_config import InterruptingError, ResultValue
from project_config.plugins.existence import ExistencePlugin


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
                        "message": (
                            "The files to check for existence"
                            " must be of type array"
                        ),
                        "definition": ".ifFilesExist",
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
                        "message": (
                            "The files to check for existence must not be empty"
                        ),
                        "definition": ".ifFilesExist",
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            [5],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The file to check for existence"
                            " must be of type string"
                        ),
                        "definition": ".ifFilesExist[0]",
                    },
                ),
            ],
            id="invalid-value-item-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foo.ext"],
            None,
            [],  # return a true boolean is optional to pass the conditional
            id="file-exists",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["bar.ext"],
            None,
            [(ResultValue, False)],
            id="file-not-exists",
        ),
        pytest.param(
            {"foo": None},
            ["foo"],
            None,
            [(ResultValue, False)],
            id="file-not-exists-is-directory",
        ),
        pytest.param(
            {"foo": None},
            ["foo/"],
            None,
            [],
            id="directory-exists",
        ),
        pytest.param(
            {"foo": None},
            ["bar/"],
            None,
            [(ResultValue, False)],
            id="directory-not-exists",
        ),
        pytest.param(
            {"bar.ext": "content"},
            ["bar.ext/"],
            None,
            [(ResultValue, False)],
            id="directory-not-exists-is-file",
        ),
    ),
)
def test_ifFilesExist(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        ExistencePlugin,
        "ifFilesExist",
        files,
        value,
        rule,
        expected_results,
    )
