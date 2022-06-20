import json
import re
import urllib.parse

import pytest
from testing_helpers import TEST_SERVER_URL

from project_config.fetchers import FetchError, fetch
from project_config.serializers import SerializerError


@pytest.mark.parametrize(
    ("path", "content", "expected_result", "expected_error_message"),
    (
        pytest.param(
            "download/foo.json",
            {"rules": []},
            True,
            None,
            id=".json",
        ),
        pytest.param(
            "download/bar.json",
            "foo",
            SerializerError,
            (
                "http://127.0.0.1:9997/download/bar.json?content=foo'"
                " can't be serialized as a valid JSON file:"
                " Expecting value: line 1 column 1 (char 0)"
            ),
            id=".json (invalid)",
        ),
        pytest.param(
            "unexistent-directory/baz.json",
            "foo",
            FetchError,
            "HTTP Error 404: NOT FOUND",
            id=".json (not existent)",
        ),
    ),
)
def test_fetch_file(
    path,
    content,
    expected_result,
    expected_error_message,
):
    if expected_result is True:
        expected_result = content
    serialized_content = (
        content if isinstance(content, str) else json.dumps(content)
    )
    url = (
        f"{TEST_SERVER_URL}/{path}?content="
        f"{urllib.parse.quote(serialized_content)}"
    )

    if expected_error_message:
        with pytest.raises(
            expected_result,
            match=re.escape(expected_error_message),
        ):
            fetch(url)
    else:
        result = fetch(url)
        assert result == expected_result
