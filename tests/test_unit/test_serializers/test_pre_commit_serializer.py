import pytest
from project_config.serializers.contrib.pre_commit import dumps


@pytest.mark.parametrize(
    ("string", "expected_result"),
    (
        pytest.param(
            {
                "repos": [
                    {
                        "hooks": [{"id": "foo", "args": ["bar", "baz"]}],
                        "rev": "v1",
                        "repo": "https://foobar",
                    },
                ],
            },
            (
                "repos:\n  - repo: https://foobar\n    rev: v1\n"
                "    hooks:\n      - id: foo\n        args:\n"
                "          - bar\n          - baz\n"
            ),
            id="basic",
        ),
    ),
)
def test_pre_commit_config_dumps(string, expected_result):
    assert dumps(string) == expected_result
