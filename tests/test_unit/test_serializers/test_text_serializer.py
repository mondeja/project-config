import pytest

from project_config.serializers.text import dumps, loads


@pytest.mark.parametrize(
    ("string", "expected_result"),
    (
        pytest.param(
            "foo\n\tbar\r\nbaz\n",
            ["foo", "\tbar", "baz"],
            id="basic",
        ),
    ),
)
def test_text_loads(string, expected_result):
    assert loads(string) == expected_result


@pytest.mark.parametrize(
    ("obj", "expected_result"),
    (
        pytest.param(
            ["foo", "\tbar", "baz"],
            "foo\n\tbar\nbaz\n",
            id="basic",
        ),
        pytest.param(
            ["", "\tbar", ""],
            "\n\tbar\n\n",
            id="empty-lines",
        ),
    ),
)
def test_text_dumps(obj, expected_result):
    assert dumps(obj) == expected_result
