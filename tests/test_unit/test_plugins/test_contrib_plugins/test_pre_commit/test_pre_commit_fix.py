import pytest
from project_config import Error
from project_config.plugins.contrib.pre_commit import PreCommitPlugin
from testing_helpers import mark_end2end


@mark_end2end
@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
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
                        "fixed": True,
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
                        "fixed": True,
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
                        "fixed": True,
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
                        "fixed": True,
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
                        "fixed": True,
                    },
                ),
            ],
            {
                ".pre-commit-config.yaml": [
                    """repos:
  - repo: https://github.com/mondeja/project-config
    rev: """,
                    """
    hooks:
      - id: project-config
""",
                ],
            },
            id="basic-fix-from-empty",
        ),
    ),
)
def test_preCommitHookExists_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        PreCommitPlugin,
        "preCommitHookExists",
        files,
        value,
        rule,
        expected_results,
        fix=True,
        expected_files=expected_files,
    )
