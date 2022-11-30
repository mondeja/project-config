import pytest

from project_config.utils.jmespath import is_literal_jmespath_expression


@pytest.mark.parametrize(
    ("expression", "expected_result"),
    (
        ("foo", False),
        ("foo.bar", False),
        ("foo[0]", False),
        ("foo[0].bar", False),
        ("foo[0].bar[1]", False),
        ("foo[0].bar[1].baz", False),
        ("foo[0].bar[1].baz[2]", False),
        ("`null`", True),
        ("null", False),
        ("`true`", True),
        ("true", False),
        ("`false`", True),
        ("false", False),
        ('"foo"', False),
        ('`["foo", 1, 2]`', True),
        ('`"foo"`', True),
        ("`0`", True),
        ("`1`", True),
        ("`1.0`", True),
    ),
)
def test_is_literal_jmespath_expression(expression, expected_result):
    assert is_literal_jmespath_expression(expression) is expected_result
