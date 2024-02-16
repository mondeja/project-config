"""Serializer for pre-commit files."""

from __future__ import annotations

from typing import Any

from project_config.serializers.yaml import dumps as yaml_dumps


REPO_KEYS_ORDER = [
    "repo",
    "rev",
    "hooks",
]
HOOK_KEYS_ORDER = [
    "id",
    "name",
    "alias",
    "entry",
    "language_version",
    "files",
    "exclude",
    "types",
    "stages",
    "always_run",
    "pass_filenames",
    "additional_dependencies",
    "args",
    "exclude_types",
]


def sort_pre_commit_config(instance: dict[str, Any]) -> dict[str, Any]:
    """Sorts pre-commit-config.yaml files."""
    sorted_repos = []
    for unsorted_repo in instance.get("repos", []):
        sorted_repo = dict(
            sorted(
                unsorted_repo.items(),
                key=lambda x: (
                    REPO_KEYS_ORDER.index(x[0])
                    if x[0] in REPO_KEYS_ORDER
                    else len(REPO_KEYS_ORDER)
                ),
            ),
        )
        sorted_hooks = []
        for unsorted_hook in unsorted_repo.get("hooks", []):
            sorted_hook = dict(
                sorted(
                    unsorted_hook.items(),
                    key=lambda x: (
                        HOOK_KEYS_ORDER.index(x[0])
                        if x[0] in HOOK_KEYS_ORDER
                        else len(HOOK_KEYS_ORDER)
                    ),
                ),
            )
            sorted_hooks.append(sorted_hook)
        sorted_repo["hooks"] = sorted_hooks
        sorted_repos.append(sorted_repo)
    instance["repos"] = sorted_repos
    return instance


def dumps(obj: Any, *args: tuple[Any], **kwargs: Any) -> str:
    """Dumps pre-commit configuration to YAML."""
    return yaml_dumps(sort_pre_commit_config(obj), *args, **kwargs)
