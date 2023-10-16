import pytest

from project_config.serializers.editorconfig import dumps, loads


BASIC_EDITORCONFIG_OBJECT = {
    "": {"root": True},
    "*.foo": {"indent_style": "space"},
}
BASIC_EDITORCONFIG_STRING = "root = true\n\n[*.foo]\nindent_style = space\n"
FULL_EDITORCONFIG_OBJECT = {
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
}


@pytest.mark.parametrize(
    ("string", "expected_result"),
    (
        pytest.param(
            BASIC_EDITORCONFIG_STRING,
            BASIC_EDITORCONFIG_OBJECT,
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
            FULL_EDITORCONFIG_OBJECT,
            id="full",
        ),
    ),
)
def test_editorconfig_loads(string, expected_result):
    assert loads(string) == expected_result


@pytest.mark.parametrize(
    ("obj", "expected_result"),
    (
        pytest.param(
            BASIC_EDITORCONFIG_OBJECT,
            BASIC_EDITORCONFIG_STRING,
            id="basic",
        ),
        pytest.param(
            FULL_EDITORCONFIG_OBJECT,
            """root = false

[*.foo]
indent_style = space
indent_size = 2
tab_width = 60
end_of_line = crlf
charset = latin1
trim_trailing_whitespace = false
insert_final_newline = true

[*.{bar,baz}]
indent_style = tab
indent_size = 4
tab_width = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = false

[*.qux]
empty_value = ""
""",
            id="full",
        ),
    ),
)
def test_editorconfig_dumps(obj, expected_result):
    assert dumps(obj) == expected_result
