import pytest

from project_config.serializers.editorconfig import loads


@pytest.mark.parametrize(
    ("string", "expected_result"),
    (
        pytest.param(
            "root = true\n\n[*.foo]\nindent_style = space\n",
            {"": {"root": True}, "*.foo": {"indent_style": "space"}},
            id="basic",
        ),
        pytest.param(
            """
root = false

# this is a comment

[*.foo]
indent_style = space
indent_size = 2
tab_width = 60
end_of_line = crlf
charset = latin1
trim_trailing_whitespace = false
insert_final_newline = true

;this is another comment

[*.{bar,baz}]
indent_style = tab
indent_size = 4
tab_width = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = false

[*.qux]
empty_value = ""  ; the parser is really lazy
""",
            {
                "": {"root": False},
                "*.foo": {
                    "indent_style": "space",
                    "indent_size": 2,
                    "tab_width": 60,
                    "end_of_line": "crlf",
                    "charset": "latin1",
                    "trim_trailing_whitespace": False,
                    "insert_final_newline": True,
                },
                "*.{bar,baz}": {
                    "indent_style": "tab",
                    "indent_size": 4,
                    "tab_width": 4,
                    "end_of_line": "lf",
                    "charset": "utf-8",
                    "trim_trailing_whitespace": True,
                    "insert_final_newline": False,
                },
                "*.qux": {"empty_value": ""},
            },
            id="full",
        ),
    ),
)
def test_editorconfig_serializer(string, expected_result):
    assert loads(string) == expected_result
