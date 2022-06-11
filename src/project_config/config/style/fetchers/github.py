import json
import re
import urllib.parse

from project_config.config.style.fetchers.https import GET


# TODO: cache this result
def get_default_branch_from_git_repo(repo_owner: str, repo_name: str) -> str:
    # try from repository HTML
    result = GET(f"https://github.com/{repo_owner}/{repo_name}/branches")
    match = re.search(r'branch=["|\'](\w+)["|\']', result)
    if match:
        return match.group(1)

    # try from API
    return json.loads(  # type: ignore
        GET(f"https://api.github.com/repos/{repo_owner}/{repo_name}")
    )["default_branch"]


def build_raw_githubusercontent_url(
    repo_owner: str,
    repo_name: str,
    git_reference: str,
    fpath: str,
) -> str:
    return (
        f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/"
        f"{git_reference}/{fpath}"
    )


# TODO: cache this result
def fetch(url_parts: urllib.parse.SplitResult) -> str:
    # extract project, filepath and git reference
    project_maybe_with_gitref, fpath = url_parts.path.lstrip("/").split("/", maxsplit=1)
    if "@" in project_maybe_with_gitref:
        project, git_reference = project_maybe_with_gitref.split("@")
    else:
        project = project_maybe_with_gitref
        git_reference = get_default_branch_from_git_repo(
            url_parts.netloc,  # netloc is the repo owner here
            project,
        )

    url = build_raw_githubusercontent_url(
        url_parts.netloc,
        project,
        git_reference,
        fpath,
    )
    return GET(url)
