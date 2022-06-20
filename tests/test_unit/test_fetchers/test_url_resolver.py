import os

import pytest

from project_config.fetchers import resolve_maybe_relative_url


@pytest.mark.parametrize(
    ("url", "parent_url", "expected_url"),
    (
        pytest.param(
            "foo",
            "",
            os.path.join(os.getcwd(), "foo"),
            id="path-path",
        ),
        pytest.param(
            os.path.abspath("foo"),
            os.getcwd(),
            os.path.abspath("foo"),
            id="abspath-path",
        ),
        pytest.param(
            os.path.abspath("foo"),
            os.path.abspath("bar"),
            os.path.abspath("foo"),
            id="abspath-abspath",
        ),
        pytest.param(
            "gh://mondeja/project/file/path.ext",
            "bar",
            "gh://mondeja/project/file/path.ext",
            id="ghpath-no-gitref-path",
        ),
        pytest.param(
            "bar.ext",
            "gh://mondeja/project/file/foo.ext",
            "gh://mondeja/project/file/bar.ext",
            id="path-ghpath-no-gitref",
        ),
        pytest.param(
            "../bar.ext",
            "github://mondeja/project/file/foo.ext",
            "github://mondeja/project/bar.ext",
            id="relpath-ghpath-no-gitref",
        ),
    ),
)
def test_resolve_maybe_relative_url(url, parent_url, expected_url):
    assert resolve_maybe_relative_url(url, parent_url) == expected_url
