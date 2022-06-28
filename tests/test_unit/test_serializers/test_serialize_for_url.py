import pytest

from project_config.serializers import serialize_for_url


@pytest.mark.parametrize(
    ("url", "string", "expected_result"),
    (
        pytest.param(
            "https://example.com/file.json",
            '{"foo": "bar", "baz": 1}',
            {"foo": "bar", "baz": 1},
            id=".json",
        ),
        pytest.param(
            "https://example.com/file.json5",
            '{foo: "bar", baz: 1}',
            {"foo": "bar", "baz": 1},
            id=".json5",
        ),
        pytest.param(
            "https://example.com/file.yaml",
            "foo: bar\nbaz: 1",
            {"foo": "bar", "baz": 1},
            id=".yaml",
        ),
        pytest.param(
            "https://example.com/file.yml",
            "foo: bar\nbaz: 1",
            {"foo": "bar", "baz": 1},
            id=".yml",
        ),
        pytest.param(
            "https://example.com/file.toml",
            'foo = "bar"\nbaz = 1',
            {"foo": "bar", "baz": 1},
            id=".toml",
        ),
        pytest.param(
            "https://example.com/file.ini",
            "[section]\nfoo = bar\nbaz = 1",
            {"section": {"foo": "bar", "baz": "1"}},
            id=".ini",
        ),
        pytest.param(
            "https://example.com/.editorconfig",
            "root = true\n\n[*.ext]\nindent_size = 1",
            {"": {"root": True}, "*.ext": {"indent_size": 1}},
            id=".editorconfig",
        ),
        pytest.param(
            "https://example.com/file.py",
            "foo = 'bar'\nbaz = 1",
            {"__file__": "https://example.com/file.py", "foo": "bar", "baz": 1},
            id=".py",
        ),
    ),
)
def test_serialize_for_url(url, string, expected_result):
    assert serialize_for_url(url, string) == expected_result
