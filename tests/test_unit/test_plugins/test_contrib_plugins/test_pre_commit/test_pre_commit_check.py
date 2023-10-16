import pytest

from project_config import Error, InterruptingError
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
            {
                ".pre-commit-config.yaml": (
                    "repos:"
                    " [{"
                    " 'repo': 'https://github.com/mondeja/project-config',"
                    " 'rev': 'master',"
                    " 'hooks': [{'id': 'project-config-fix'}]"
                    "}]"
                ),
            },
            ["https://github.com/mondeja/project-config", "project-config"],
            None,
            [
                (
                    Error,
                    {
                        "message": (
                            "The hook 'project-config' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
            ],
            id="set-simple",
        ),
        pytest.param(
            {
                ".pre-commit-config.yaml": (
                    "repos:"
                    " [{"
                    " 'repo': 'https://github.com/mondeja/project-config',"
                    " 'rev': 'master',"
                    " 'hooks': []"
                    "}]"
                ),
            },
            ["https://github.com/mondeja/project-config", "project-config"],
            None,
            [
                (
                    Error,
                    {
                        "message": (
                            "The key 'hooks' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must not be empty"
                        ),
                        "definition": ".preCommitHookExists[1]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
                (
                    Error,
                    {
                        "message": (
                            "The hook 'project-config' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
            ],
            id="set-simple-empty-hooks",
        ),
        pytest.param(
            {".pre-commit-config.yaml": "{}"},
            ["https://github.com/mondeja/project-config", "project-config"],
            None,
            [
                (
                    Error,
                    {
                        "message": "The key 'repos' must be set",
                        "definition": ".preCommitHookExists",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
                (
                    Error,
                    {
                        "message": (
                            "The repo 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
                (
                    Error,
                    {
                        "message": (
                            "The key 'rev' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
                (
                    Error,
                    {
                        "message": (
                            "The key 'hooks' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[1]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
                (
                    Error,
                    {
                        "message": (
                            "The hook 'project-config' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                        "definition": ".preCommitHookExists[1][0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                    },
                ),
            ],
            id="set-full",
        ),
        pytest.param(
            {
                ".pre-commit-config.yaml": (
                    "repos:\n"
                    "  - repo: https://github.com/mondeja/project-config\n"
                    "    hooks:\n"
                    "      - id: project-config\n"
                    "        alias: project-config-check\n"
                    "      - id: project-config-fix\n"
                    "        alias: project-config-fix\n"
                ),
            },
            [
                "https://github.com/mondeja/project-config",
                [
                    {"id": "project-config", "alias": "pc"},
                    {"id": "project-config-fix", "alias": "pcf"},
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".preCommitHookExists[0]",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                        "message": (
                            "The key 'rev' of the repo "
                            "'https://github.com/mondeja/project-config'"
                            " must be set"
                        ),
                    },
                ),
                (
                    Error,
                    {
                        "definition": ".preCommitHookExists[1][0].alias",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                        "message": (
                            "The configuration 'alias' defined by the hook"
                            " 'project-config' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be 'pc' but is 'project-config-check'"
                        ),
                    },
                ),
                (
                    Error,
                    {
                        "definition": ".preCommitHookExists[1][1].alias",
                        "file": ".pre-commit-config.yaml",
                        "fixable": True,
                        "fixed": False,
                        "message": (
                            "The configuration 'alias' defined by the hook"
                            " 'project-config-fix' of the repo"
                            " 'https://github.com/mondeja/project-config'"
                            " must be 'pcf' but is 'project-config-fix'"
                        ),
                    },
                ),
            ],
            id="edit-hooks",
        ),
        pytest.param(
            {
                ".pre-commit-config.yaml": (
                    "repos:"
                    " [{"
                    " 'repo': 'meta',"
                    " 'hooks': [{'id': 'check-hooks-apply'}]"
                    "}]"
                ),
            },
            ["meta", "check-hooks-apply"],
            None,
            [],
            id="meta-repo-not-set-rev",
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
