import pytest
from project_config import InterruptingError
from project_config.plugins.contrib.pre_commit import PreCommitPlugin


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
                            "The value of the pre-commit hook to check"
                            " for existence must be of type array"
                        ),
                        "definition": ".preCommitHookExists",
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
                            "The value of the pre-commit hook to check"
                            " for existence must not be empty"
                        ),
                        "definition": ".preCommitHookExists",
                    },
                ),
            ],
            id="invalid-empty-value",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            [1, 2, 3],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The value of the pre-commit hook to check"
                            " for existence must be of length 2"
                        ),
                        "definition": ".preCommitHookExists",
                    },
                ),
            ],
            id="invalid-value-length",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            [1, 2],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The URL of the pre-commit hook repo to check"
                            " for existence must be of type string"
                        ),
                        "definition": ".preCommitHookExists[0]",
                    },
                ),
            ],
            id="invalid-first-subvalue-type",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["", 2],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The URL of the pre-commit hook repo to check"
                            " for existence must not be empty"
                        ),
                        "definition": ".preCommitHookExists[0]",
                    },
                ),
            ],
            id="invalid-empty-first-subvalue",
        ),
        pytest.param(
            {"foo.ext": "foo"},
            ["foobar", 2],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The config of the pre-commit hook to check"
                            " for existence must be of type string or array"
                        ),
                        "definition": ".preCommitHookExists[1]",
                    },
                ),
            ],
            id="invalid-second-subvalue-type",
        ),
        pytest.param(
            {"foo.ext": ""},
            ["foobar", []],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The config of the pre-commit hook to check"
                            " for existence must not be empty"
                        ),
                        "definition": ".preCommitHookExists[1]",
                    },
                ),
            ],
            id="invalid-empty-second-subvalue",
        ),
        pytest.param(
            {".pre-commit-config.yaml": "foo"},
            ["foobar", "barbaz"],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The pre-commit configuration"
                            " must be of type object"
                        ),
                        "definition": ".preCommitHookExists",
                        "file": ".pre-commit-config.yaml",
                    },
                ),
            ],
            id="invalid-instance-type",
        ),
        pytest.param(
            {".pre-commit-config.yaml": ""},
            ["foobar", [2]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The config of the pre-commit hook to check"
                            " for existence must be of type string or object"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                    },
                ),
            ],
            id="invalid-second-subsubvalue-type",
        ),
        pytest.param(
            {".pre-commit-config.yaml": ""},
            ["foobar", [""]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The config of the pre-commit hook to check"
                            " for existence must not be empty"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                    },
                ),
            ],
            id="invalid-empty-second-subsubvalue",
        ),
        pytest.param(
            {".pre-commit-config.yaml": ""},
            ["foobar", [{"name": "hello"}]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The config of the pre-commit hook to check"
                            " for existence must have an id"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                    },
                ),
            ],
            id="invalid-id-not-in-hook-second-subsubvalue",
        ),
        pytest.param(
            {".pre-commit-config.yaml": ""},
            ["foobar", [{"id": 5}]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The id of the pre-commit hook to check"
                            " for existence must be of type string"
                        ),
                        "definition": ".preCommitHookExists[1][0].id",
                    },
                ),
            ],
            id="invalid-id-type-second-subsubvalue",
        ),
        pytest.param(
            {".pre-commit-config.yaml": ""},
            ["foobar", [{"id": ""}]],
            None,
            [
                (
                    InterruptingError,
                    {
                        "message": (
                            "The id of the pre-commit hook to check"
                            " for existence must not be empty"
                        ),
                        "definition": ".preCommitHookExists[1][0].id",
                    },
                ),
            ],
            id="invalid-empty-id-second-subsubvalue",
        ),
    ),
)
def test_preCommitHookExists(
    files,
    value,
    rule,
    expected_results,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        PreCommitPlugin,
        "preCommitHookExists",
        files,
        value,
        rule,
        expected_results,
    )
