import urllib.parse

import pytest

from project_config.fetchers.github import (
    _get_default_branch_from_repo_branches_html,
    fetch,
)


@pytest.mark.parametrize(
    ("repo_name", "repo_owner", "expected_branch"),
    (
        ("simple-icons", "simple-icons", "develop"),
        ("mondeja", "project-config", "master"),
    ),
)
def test__get_default_branch_from_repo_branches_html(
    repo_name,
    repo_owner,
    expected_branch,
):
    assert (
        _get_default_branch_from_repo_branches_html(
            repo_name,
            repo_owner,
        )
        == expected_branch
    )


@pytest.mark.parametrize(
    ("url", "expected_content"),
    (
        (
            "gh://mondeja/project-config-styles/python/base.json5",
            "pyproject/main.json5",
        ),
        (
            "gh://mondeja/project-config@v0.1.0/docs/install.rst",
            "poetry add project-config",
        ),
    ),
)
def test_fetch(url, expected_content):
    assert expected_content in fetch(urllib.parse.urlsplit(url))
