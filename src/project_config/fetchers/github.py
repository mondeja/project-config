"""Github files resources URIs fetcher."""

from __future__ import annotations

import json
import re
import typing as t
import urllib.parse

from project_config.utils.http import GET


def _get_default_branch_from_repo_branches_html(
    repo_owner: str,
    repo_name: str,
) -> t.Optional[str]:
    # try from repository HTML
    result = GET(f"https://github.com/{repo_owner}/{repo_name}/branches")
    match = re.search(r'branch=["|\'](\w+)["|\']', result)
    return match.group(1) if match else None


def _get_default_branch_from_repo_github_api(
    repo_owner: str,
    repo_name: str,
) -> str:  # pragma: no cover
    # try from API
    #
    # note that this function is not covered by the tests because
    # the previous function that retrieves the default branch from the
    # HTML of the repo must be the one that works, this only acts as
    # a fallback, though could reach the limit of usage of the API
    #
    # if the previous becomes problematic we should improve the management
    # of the API rate limit with a Github token
    result = GET(f"https://api.github.com/repos/{repo_owner}/{repo_name}")
    return json.loads(result)["default_branch"]  # type: ignore


def _get_default_branch_from_git_repo(
    repo_owner: str,
    repo_name: str,
) -> str:  # pragma: no cover
    return _get_default_branch_from_repo_branches_html(
        repo_owner,
        repo_name,
    ) or _get_default_branch_from_repo_github_api(
        repo_owner,
        repo_name,
    )


def _build_raw_githubusercontent_url(
    repo_owner: str,
    repo_name: str,
    git_reference: str,
    fpath: str,
) -> str:
    return (
        f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/"
        f"{git_reference}/{fpath}"
    )


def resolve_url(url_parts: urllib.parse.SplitResult) -> str:
    """Resolve a ``gh:`` scheme URI to their real counterpart.

    Args:
        url_parts (urllib.parse.SplitResult): The URL parts of the URI.

    Returns:
        str: The real ``https:`` scheme URL.
    """
    # extract project, filepath and git reference
    project_maybe_with_gitref, fpath = url_parts.path.lstrip("/").split(
        "/",
        maxsplit=1,
    )
    if "@" in project_maybe_with_gitref:
        project, git_reference = project_maybe_with_gitref.split("@")
    else:
        project = project_maybe_with_gitref
        git_reference = _get_default_branch_from_git_repo(
            url_parts.netloc,  # netloc is the repo owner here
            project,
        )

    return _build_raw_githubusercontent_url(
        url_parts.netloc,
        project,
        git_reference,
        fpath,
    )


def fetch(url_parts: urllib.parse.SplitResult, **kwargs: t.Any) -> str:
    """Fetch a resource through HTTPs protocol for a Github URI.

    Args:
        url_parts (urllib.parse.SplitResult): The URL parts of the URI.

    Returns:
        str: The fetched resource content.
    """
    return GET(resolve_url(url_parts), **kwargs)
