import pytest

from project_config.config.style.fetchers import fetch_style


@pytest.mark.parametrize(
    (
        "path",
        "url",
        "content",
        "expected_result",  # use True to expect the same as "content"
        "expected_error_message",
    ),
    (
        pytest.param(
            "foo.txt",
            "foo.txt",
            "foo\nbar\n",
            None,
            "'foo.txt' can't be decoded as a valid JSON file: Expecting value: line 1 column 1 (char 0)",
            id=".txt",
        ),
        pytest.param(
            "foo.txt",
            "foo.txt",
            "{}",
            {},
            None,
            id=".txt (valid JSON)",
        ),
        pytest.param(
            "foo.json",
            "foo.json",
            "",
            None,
            (
                "'foo.json' can't be decoded as a valid JSON file:"
                " Expecting value: line 1 column 1 (char 0)"
            ),
            id=".txt (invalid JSON as empty)",
        ),
        pytest.param(
            "foo.json",
            "foo.json",
            "{}",
            {},
            None,
            id=".json",
        ),
        pytest.param(
            "foo.json",
            "foo.json",
            "",
            None,
            (
                "'foo.json' can't be decoded as a valid JSON file:"
                " Expecting value: line 1 column 1 (char 0)"
            ),
            id=".json (empty)",
        ),
        pytest.param(
            "foo.json",
            "foo.json",
            "{foo}",
            None,
            (
                "'foo.json' can't be decoded as a valid JSON file:"
                " Expecting property name enclosed in double quotes:"
                " line 1 column 2 (char 1)"
            ),
            id=".json (invalid JSON)",
        ),
        pytest.param(
            "foo.json5",
            "foo.json5",
            "{//comment\n}",
            {},
            None,
            id=".json5",
        ),
        pytest.param(
            "foo.json5",
            "foo.json5",
            "",
            None,
            (
                "'foo.json5' can't be decoded as a valid JSON file:"
                " No JSON data found near 0"
            ),
            id=".json5 (empty)",
        ),
        pytest.param(
            "foo.json5",
            "foo.json5",
            "{foo}",
            None,
            (
                "'foo.json5' can't be decoded as a valid JSON file:"
                " Expected b'colon' near 5, found U+007d"
            ),
            id=".json5 (invalid JSON)",
        ),
        pytest.param(
            "foo.yaml",
            "foo.yaml",
            "foo: 1",
            {"foo": 1},
            None,
            id=".yaml",
        ),
        pytest.param(
            "foo.yaml",
            "foo.yaml",
            "",
            None,  # yaml.Loader results in None if empty file
            None,
            id=".yaml (empty)",
        ),
        pytest.param(
            "foo.yaml",
            "foo.yaml",
            "true: 1\n2\n3'foo",
            None,
            (
                "'foo.yaml' can't be decoded as a valid JSON file:\n"
                "while scanning a simple key\n"
                '  in "<unicode string>", line 2, column 1\n'
                "could not find expected ':'\n"
                '  in "<unicode string>", line 3, column 1'
            ),
            id=".yaml (invalid JSON)",
        ),
        pytest.param(
            "foo.toml",
            "foo.toml",
            "[foo]\nbar = 1",
            {"foo": {"bar": 1}},
            None,
            id=".toml",
        ),
        pytest.param(
            "foo.toml",
            "foo.toml",
            "",
            {},
            None,
            id=".toml (empty)",
        ),
        pytest.param(
            "foo.toml",
            "foo.toml",
            "foo = 'bar",
            None,
            (
                "'foo.toml' can't be decoded as a valid JSON file:"
                " Unexpected end of file at line 1 col 10"
            ),
            id=".toml (invalid JSON)",
        ),
        pytest.param(
            "foo.json",
            "{tmp_path}/foo.json",
            "{}",
            {},
            None,
            id="absolute path",
        ),
    ),
)
def test_fetch_style_file(
    tmp_path, chdir, path, url, content, expected_result, expected_error_message
):
    (tmp_path / path).write_text(content)

    if expected_result is True:
        expected_result = content
    url = url.replace("{tmp_path}", str(tmp_path))
    with chdir(tmp_path):
        result, error_message = fetch_style(url)
    assert result == expected_result
    assert error_message == expected_error_message
