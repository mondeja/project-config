import urllib.parse

import pytest

from project_config.fetchers.github import fetch
from testing_helpers import mark_end2end


@mark_end2end
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
