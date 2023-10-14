import json
import re
import urllib.parse

import pytest
from project_config.fetchers import FetchError, fetch
from testing_helpers import TEST_SERVER_URL, mark_end2end


@mark_end2end
@pytest.mark.parametrize(
    ("path", "content", "expected_result", "expected_error_message"),
    (
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
        f"{TEST_SERVER_URL}/download/"
        f"{urllib.parse.quote(serialized_content)}/{path}"
    )

    if expected_error_message:
        with pytest.raises(
            expected_result,
            match=re.escape(expected_error_message),
        ):
            fetch(url, timeout=5, sleep=0)
    else:
        result = fetch(url, timeout=5, sleep=0)
        assert result == expected_result
