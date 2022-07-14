import pytest

from project_config.serializers.ini import dumps, loads


SPACE = " "


@pytest.mark.parametrize(
    ("string", "expected_result"),
    (
        pytest.param(
            "[section]\nfoo = bar\nbaz = 1",
            {"section": {"foo": "bar", "baz": "1"}},
            id="basic",
        ),
        pytest.param(
            """[section]
foo = bar
baz = 1
qux =
    a
    b
    c

[other_section]
a_boolean = true
a_zero = 0
""",
            {
                "section": {
                    "foo": "bar",
                    "baz": "1",
                    "qux": "\na\nb\nc",
                },
                "other_section": {
                    "a_boolean": "true",
                    "a_zero": "0",
                },
            },
            id="full",
        ),
    ),
)
def test_ini_serializer(string, expected_result):
    assert loads(string) == expected_result


@pytest.mark.parametrize(
    ("obj", "expected_result"),
    (
        pytest.param(
            {"section": {"foo": "bar", "baz": "1"}},
            "[section]\nfoo = bar\nbaz = 1\n\n",
            id="basic",
        ),
        pytest.param(
            {
                "section": {
                    "foo": "bar",
                    "baz": "1",
                    "qux": "\na\nb\nc",
                },
                "other_section": {
                    "a_boolean": "true",
                    "a_zero": "0",
                },
            },
            """[section]
foo = bar
baz = 1
qux ="""
            + SPACE
            + """
\ta
\tb
\tc

[other_section]
a_boolean = true
a_zero = 0

""",
            id="full",
        ),
    ),
)
def test_ini_deserializer(obj, expected_result):
    assert dumps(obj) == expected_result
