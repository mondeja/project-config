import re

import pytest
from project_config.serializers import (
    SerializerError,
    guess_preferred_serializer,
    serialize_for_url,
)


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
            {"__file__": "file.py", "foo": "bar", "baz": 1},
            id=".py",
        ),
        pytest.param(
            "https://example.com/file.py?text",
            "foo = 'bar'\nbaz = 1",
            ["foo = 'bar'", "baz = 1"],
            id=".py?text",
        ),
    ),
)
def test_serialize_for_url(url, string, expected_result):
    url, serializer_name = guess_preferred_serializer(url)
    assert (
        serialize_for_url(url, string, prefer_serializer=serializer_name)
        == expected_result
    )


@pytest.mark.parametrize(
    (
        "url",
        "string",
        "expected_exception_class",
        "expected_exception_message",
    ),
    (
        pytest.param(
            "https://example.com/file.json",
            "{",
            SerializerError,
            (
                "'https://example.com/file.json' can't be serialized as a"
                " valid object: Expecting property name enclosed in double"
                " quotes: line 1 column 2 (char 1)"
            ),
            id=".json-parsing-error",
        ),
        pytest.param(
            "https://example.com/file.json?impossible-other-serializer",
            "{}",
            SerializerError,
            (
                "'https://example.com/file.json' can't be serialized as a"
                " valid object:\nPreferred serializer"
                " 'impossible-other-serializer' not supported"
            ),
            id=".json?invalid-preferred-serializer",
        ),
    ),
)
def test_serialize_for_url_errors(
    url,
    string,
    expected_exception_class,
    expected_exception_message,
):
    url, serializer_name = guess_preferred_serializer(url)
    with pytest.raises(
        expected_exception_class,
        match=re.escape(expected_exception_message),
    ):
        serialize_for_url(url, string, prefer_serializer=serializer_name)
