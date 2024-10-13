"""pre-commit plugin for project_config."""

from __future__ import annotations

import copy
import os
import stat
from typing import TYPE_CHECKING, Any

from project_config import (
    ActionsContext,
    Error,
    InterruptingError,
    tree,
)
from project_config.fetchers.github import get_latest_release_tags
from project_config.serializers.contrib.pre_commit import (
    sort_pre_commit_config,
)


if TYPE_CHECKING:
    from project_config import Results, Rule


class PreCommitPlugin:
    @staticmethod
    def preCommitHookExists(
        value: Any,
        _rule: Rule,
        context: ActionsContext,
    ) -> Results:
        if not isinstance(value, list):
            yield InterruptingError, {
                "message": (
                    "The value of the pre-commit hook to check"
                    " for existence must be of type array"
                ),
                "definition": ".preCommitHookExists",
            }
        elif not value:
            yield InterruptingError, {
                "message": (
                    "The value of the pre-commit hook to check"
                    " for existence must not be empty"
                ),
                "definition": ".preCommitHookExists",
            }
        elif len(value) != 2:  # noqa: PLR2004
            yield InterruptingError, {
                "message": (
                    "The value of the pre-commit hook to check"
                    " for existence must be of length 2"
                ),
                "definition": ".preCommitHookExists",
            }

        if not isinstance(value[0], str):
            yield InterruptingError, {
                "message": (
                    "The URL of the pre-commit hook repo to"
                    " check for existence must be of type string"
                ),
                "definition": ".preCommitHookExists[0]",
            }
        elif not value[0]:
            yield InterruptingError, {
                "message": (
                    "The URL of the pre-commit hook repo to"
                    " check for existence must not be empty"
                ),
                "definition": ".preCommitHookExists[0]",
            }

        if isinstance(value[1], str):
            value[1] = [{"id": value[1]}]
        if not isinstance(value[1], list):
            yield InterruptingError, {
                "message": (
                    "The config of the pre-commit hook to check"
                    " for existence must be of type string or array"
                ),
                "definition": ".preCommitHookExists[1]",
            }
        elif not value[1]:
            yield InterruptingError, {
                "message": (
                    "The config of the pre-commit hook to check"
                    " for existence must not be empty"
                ),
                "definition": ".preCommitHookExists[1]",
            }
        for i, hook in enumerate(value[1]):
            if not isinstance(hook, dict) and not isinstance(hook, str):
                yield InterruptingError, {
                    "message": (
                        "The config of the pre-commit hook"
                        " to check for existence must be of"
                        " type string or object"
                    ),
                    "definition": f".preCommitHookExists[1][{i}]",
                }
            elif not hook:
                yield InterruptingError, {
                    "message": (
                        "The config of the pre-commit hook to check"
                        " for existence must not be empty"
                    ),
                    "definition": f".preCommitHookExists[1][{i}]",
                }

            if isinstance(hook, str):
                value[1][i] = {"id": hook}
            elif "id" not in hook:
                yield InterruptingError, {
                    "message": (
                        "The config of the pre-commit hook to check"
                        " for existence must have an id"
                    ),
                    "definition": f".preCommitHookExists[1][{i}]",
                }
            elif not isinstance(hook["id"], str):
                yield InterruptingError, {
                    "message": (
                        "The id of the pre-commit hook to check"
                        " for existence must be of type string"
                    ),
                    "definition": f".preCommitHookExists[1][{i}].id",
                }
            elif not hook["id"]:
                yield InterruptingError, {
                    "message": (
                        "The id of the pre-commit hook to check"
                        " for existence must not be empty"
                    ),
                    "definition": f".preCommitHookExists[1][{i}].id",
                }

        repo, expected_hooks = value

        files = copy.copy(context.files)
        for f, fpath in enumerate(files):
            try:
                fstat = os.stat(fpath)
            except FileNotFoundError:  # pragma: no cover
                continue
            if stat.S_ISDIR(fstat.st_mode):  # pragma: no cover
                yield InterruptingError, {
                    "message": (
                        "The pre-commit configuration"
                        " is pointing to a directory"
                    ),
                    "definition": f".files[{f}]",
                    "file": f"{fpath}",
                }

            instance = tree.cached_local_file(fpath)
            if not isinstance(instance, dict):
                yield InterruptingError, {
                    "message": (
                        "The pre-commit configuration must be of type object"
                    ),
                    "definition": ".preCommitHookExists",
                    "file": f"{fpath}",
                }

            # check if repo in file
            if "repos" not in instance:
                instance["repos"] = []
                yield Error, {
                    "message": "The key 'repos' must be set",
                    "definition": ".preCommitHookExists",
                    "file": f"{fpath}",
                    "fixable": True,
                    "fixed": context.fix,
                }

            repo_index = -1
            for repo_i, repo_config in enumerate(instance["repos"]):
                if "repo" in repo_config and repo_config["repo"] == repo:
                    repo_index = repo_i
                    break
            if repo_index == -1:
                instance["repos"].append({"repo": repo})
                repo_index = len(instance["repos"]) - 1
                yield Error, {
                    "message": (f"The repo '{repo}' must be set"),
                    "definition": ".preCommitHookExists[0]",
                    "file": f"{fpath}",
                    "fixable": True,
                    "fixed": context.fix,
                }

            # found or added a new repo with our repo name

            # check if rev in repo
            if repo != "meta" and "rev" not in instance["repos"][repo_index]:
                # if not found, get latest rev and set it
                if context.fix:
                    parts = list(reversed(repo.split("/")))
                    repo_name, repo_owner = parts[0], parts[1]
                    latest_tag = get_latest_release_tags(
                        repo_owner,
                        repo_name,
                    )[0]
                    instance["repos"][repo_index]["rev"] = latest_tag
                else:
                    instance["repos"][repo_index]["rev"] = "master"
                yield Error, {
                    "message": (
                        f"The key 'rev' of the repo '{repo}' must be set"
                    ),
                    "definition": ".preCommitHookExists[0]",
                    "file": f"{fpath}",
                    "fixable": True,
                    "fixed": context.fix,
                }

            # check if hook in repo
            if "hooks" not in instance["repos"][repo_index]:
                instance["repos"][repo_index]["hooks"] = []
                yield Error, {
                    "message": (
                        f"The key 'hooks' of the repo '{repo}' must be set"
                    ),
                    "definition": ".preCommitHookExists[1]",
                    "file": f"{fpath}",
                    "fixable": True,
                    "fixed": context.fix,
                }
            elif not instance["repos"][repo_index]["hooks"]:
                instance["repos"][repo_index]["hooks"] = []
                yield Error, {
                    "message": (
                        f"The key 'hooks' of the repo '{repo}'"
                        f" must not be empty"
                    ),
                    "definition": ".preCommitHookExists[1]",
                    "file": f"{fpath}",
                    "fixable": True,
                    "fixed": context.fix,
                }

            # check expected hooks exists with their configuration
            for i, hook in enumerate(expected_hooks):
                hook_found = False
                for repo_hook in instance["repos"][repo_index]["hooks"]:
                    if repo_hook["id"] != hook["id"]:
                        continue

                    hook_found = True
                    for expected_hook_key, expected_hook_value in hook.items():
                        hook_value = repo_hook.get(expected_hook_key)
                        if hook_value == expected_hook_value:
                            continue

                        yield Error, {
                            "message": (
                                f"The configuration '{expected_hook_key}'"
                                f' defined by the hook \'{hook["id"]}\''
                                f" of the repo '{repo}' must be"
                                f" '{expected_hook_value}' but is"
                                f" '{hook_value}'"
                            ),
                            "definition": (
                                f".preCommitHookExists[1][{i}]"
                                f".{expected_hook_key}"
                            ),
                            "file": f"{fpath}",
                            "fixable": True,
                            "fixed": context.fix,
                        }
                        repo_hook[expected_hook_key] = expected_hook_value

                if not hook_found:
                    instance["repos"][repo_index]["hooks"].append(hook)
                    yield Error, {
                        "message": (
                            f"The hook '{hook['id']}' of the repo '{repo}'"
                            " must be set"
                        ),
                        "definition": f".preCommitHookExists[1][{i}]",
                        "file": f"{fpath}",
                        "fixable": True,
                        "fixed": context.fix,
                    }

            if context.fix:
                tree.edit_local_file(
                    fpath,
                    sort_pre_commit_config(instance),
                )
