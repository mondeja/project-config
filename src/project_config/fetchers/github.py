"""Github files resources URIs fetcher."""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.parse
from enum import Enum
from typing import Any

from project_config import __version__
from project_config.utils.http import GET


SEMVER_REGEX = r"\d+\.\d+\.\d+"


class AcceptHeader(Enum):
    """Accept header values for Github API."""

    JSON = "application/vnd.github+json"


def _github_headers(accept: AcceptHeader | None = None) -> dict[str, str]:
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"project-config v{__version__}",
    }
    if accept == AcceptHeader.JSON:
        headers["Accept"] = "application/vnd.github+json"

    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _build_github_api_url(
    repo_owner: str,
    repo_name: str,
    git_reference: str | None,
    fpath: str,
) -> str:
    query_parameters = "" if not git_reference else f"?ref={git_reference}"
    return (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        f"/contents/{fpath}{query_parameters}"
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
        project, git_reference = (project_maybe_with_gitref, None)

    return _build_github_api_url(
        url_parts.netloc,
        project,
        git_reference,
        fpath,
    )


def fetch(url_parts: urllib.parse.SplitResult, **kwargs: Any) -> Any:
    """Fetch a resource through HTTPs protocol for a Github URI.

    Args:
        url_parts (urllib.parse.SplitResult): The URL parts of the URI.
        **kwargs (Any): The keyword arguments to pass to the ``GET`` function.

    Returns:
        str: The fetched resource content.
    """
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    kwargs["headers"].update(_github_headers(accept=AcceptHeader.JSON))
    response = json.loads(GET(resolve_url(url_parts), **kwargs))
    if "content" in response:
        return base64.b64decode(response["content"]).decode("utf-8")
    return response


def get_latest_release_tags(
    repo_owner: str,
    repo_name: str,
    only_semver: bool = False,  # noqa: FBT001, FBT002
) -> list[str]:
    """Get the latest release tag of a Github repository.

    Args:
        repo_owner (str): The Github repository owner.
        repo_name (str): The Github repository name.
        only_semver (bool): If True, only return a tag if it is a semver tag.

    Returns:
        str: The latest release tag.
    """
    result = GET(
        f"https://github.com/{repo_owner}/{repo_name}/tags",
        headers=_github_headers(),
    )
    regex = (
        rf'/{re.escape(repo_owner)}/{re.escape(repo_name)}/releases/tag/([^"]+)'
    )

    response = []
    tags = re.findall(regex, result)
    for tag in tags:
        if tag in response:
            continue

        cleaned_tag = re.sub("^[a-zA-Z-]+", "", tag)

        if not cleaned_tag:
            continue

        if only_semver and not re.match(SEMVER_REGEX, cleaned_tag):
            continue

        response.append(tag)
    return response
