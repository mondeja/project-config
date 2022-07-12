
import pytest

from project_config import Error
from project_config.plugins.jmespath import JMESPathPlugin


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
        pytest.param(
            {
                "package.json": '{"foo": "baz"}',
            },
            [
                ["foo", "bar"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'foo\' does not match. Expected'
                            " 'bar', returned 'baz'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": '{"foo": "bar"}',
            },
            id="constant-expression-smart",
        ),
        pytest.param(
            {
                "package.json": '[]',
            },
            [
                ["[0]", "foo"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'[0]\' does not match. Expected'
                            " 'foo', returned None"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": '["foo"]',
            },
            id="constant-expression-index-smart",
        ),
        pytest.param(
            {
                "package.json": '{}',
            },
            [
                [
                    "type(foo)",
                    "string",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'type(foo)\' does not match. Expected'
                            " 'string', returned 'null'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": '{"foo": ""}',
            },
            id="typeof-expression-smart",
        ),
        pytest.param(
            {
                "pyproject.toml": '[tool.poetry]\nname = "foo"\n',
            },
            [
                [
                    "type(tool.\"project-config\")",
                    "object",
                    'deepmerge(@, `{"tool": {"project-config": {}}}`)'
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "pyproject.toml",
                        "message": (
                            'JMESPath \'type(tool."project-config")\' does not match. Expected'
                            " 'object', returned 'null'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "pyproject.toml": (
                    '[tool.poetry]\nname = "foo"\n\n'
                    '[tool.project-config]\n'
                ),
            },
            id="typeof-deepmerge-subexpressions-default",
        ),
        pytest.param(
            {
                "pyproject.toml": '[tool.poetry]\nname = "foo"\n',
            },
            [
                [
                    "type(tool.\"project-config\")",
                    "object",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "pyproject.toml",
                        "message": (
                            'JMESPath \'type(tool."project-config")\' does not match. Expected'
                            " 'object', returned 'null'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "pyproject.toml": (
                    '[tool.poetry]\nname = "foo"\n\n'
                    '[tool.project-config]\n'
                ),
            },
            id="typeof-object-subexpressions-smart",
        ),
        pytest.param(
            {
                "package.json": '{}\n',
            },
            [
                [
                    "type(foo.\"project-config\")",
                    "array",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'type(foo."project-config")\' does not match. Expected'
                            " 'array', returned 'null'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": (
                    '{"foo": {"project-config": []}}'
                ),
            },
            id="typeof-array-subexpressions-smart",
        ),
        pytest.param(
            {
                "package.json": '{}\n',
            },
            [
                [
                    "type(foo.\"project-config\")",
                    "string",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'type(foo."project-config")\' does not match. Expected'
                            " 'string', returned 'null'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": (
                    '{"foo": {"project-config": ""}}'
                ),
            },
            id="typeof-string-subexpressions-smart",
        ),
        pytest.param(
            {
                "package.json": '{"foo": [{"bar": true}]}\n',
            },
            [
                [
                    "type(foo[0].bar)",
                    "string",
                ],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            'JMESPath \'type(foo[0].bar)\' does not match. Expected'
                            " 'string', returned 'boolean'"
                        ),
                        "fixed": True,
                    },
                ),
            ],
            {
                "package.json": (
                    '{"foo": [{"bar": ""}, {"bar": true}]}'
                ),
            },
            id="typeof-string-subexpressions-indexes-smart",
        ),

        # TODO:
        # type() with array queries: [*], [0]
        # Constants: "".root' -> true
        # contains() in arrays
        # contains(keys()) in objects
    )
)
def test_JMESPathsMatch_fix(
    files,
    value,
    rule,
    expected_results,
    expected_files,
    assert_project_config_plugin_action,
):
    assert_project_config_plugin_action(
        JMESPathPlugin,
        "JMESPathsMatch",
        files,
        value,
        rule,
        expected_results,
        fix=True,
        expected_files=expected_files,
    )
