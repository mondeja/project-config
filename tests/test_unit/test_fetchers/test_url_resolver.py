import os

import pytest

from project_config.fetchers import resolve_maybe_relative_url


@pytest.mark.parametrize(
    ("url", "parent_url", "expected_url"),
    (
        pytest.param(
            "foo",
            "{tmp_path}",
            "foo",
            id="path-path",
        ),
        pytest.param(
            os.path.join("..", "qux.ext"),
            os.path.join("foo", "bar", "baz.ext"),
            "foo/qux.ext",
            id="relative-outside-rootdir",
        ),
        pytest.param(
            os.path.abspath("foo"),
            "",
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
def test_resolve_maybe_relative_url(url, parent_url, expected_url, tmp_path):
    assert (
        resolve_maybe_relative_url(
            url.replace("{tmp_path}", str(tmp_path)),
            parent_url.replace("{tmp_path}", str(tmp_path)),
            str(tmp_path),
        )
        == expected_url
    )
