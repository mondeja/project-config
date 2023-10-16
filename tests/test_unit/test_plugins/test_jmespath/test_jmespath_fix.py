import json

import pytest

from project_config import Error
from project_config.constants import InterruptingError
from project_config.plugins.jmespath import JMESPathPlugin


def JSON_2_INDENTED(string):
    return (  # noqa: E731
        json.dumps(
            json.loads(string),
            indent=2,
        )
        + "\n"
    )


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
        pytest.param(
            {
                "package.json": '{"foo": "baz"}',
            },
            [
                ["bar", "qux", True],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][2]",
                        "message": (
                            "The JMES path fixer query must be of type string"
                        ),
                    },
                ),
            ],
            {
                "package.json": '{"foo": "baz"}',
            },
            id="invalid-fixer-query-type",
        ),
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
                            "JMESPath 'foo' does not match. Expected"
                            " 'bar', returned 'baz'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED('{"foo": "bar"}'),
            },
            id="constant-expression-smart",
        ),
        pytest.param(
            {
                "package.json": "[]",
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
                            "JMESPath '[0]' does not match. Expected"
                            " 'foo', returned None"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED('["foo"]'),
            },
            id="constant-expression-index-smart",
        ),
        pytest.param(
            {
                "package.json": "{}",
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
                            "JMESPath 'type(foo)' does not match. Expected"
                            " 'string', returned 'null'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED('{"foo": ""}'),
            },
            id="typeof-expression-smart",
        ),
        pytest.param(
            {
                "pyproject.toml": '[project]\nname = "foo"\n',
            },
            [
                [
                    'type(tool."project-config")',
                    "object",
                    'deepmerge(@, `{"tool": {"project-config": {}}}`)',
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
                            "JMESPath 'type(tool.\"project-config\")'"
                            " does not match. Expected"
                            " 'object', returned 'null'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "pyproject.toml": (
                    '[project]\nname = "foo"\n\n[tool.project-config]\n'
                ),
            },
            id="typeof-deepmerge-subexpressions-default",
        ),
        pytest.param(
            {
                "package.json": "{}\n",
            },
            [
                [
                    'type(foo."project-config")',
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
                            "JMESPath 'type(foo.\"project-config\")'"
                            " does not match. Expected"
                            " 'array', returned 'null'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED(
                    '{"foo": {"project-config": []}}',
                ),
            },
            id="typeof-array-subexpressions-smart",
        ),
        pytest.param(
            {
                "package.json": "{}\n",
            },
            [
                [
                    'type(foo."project-config")',
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
                            "JMESPath 'type(foo.\"project-config\")'"
                            " does not match. Expected"
                            " 'string', returned 'null'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED(
                    '{"foo": {"project-config": ""}}',
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
                            "JMESPath 'type(foo[0].bar)' does not match."
                            " Expected 'string', returned 'boolean'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED(
                    '{"foo": [{"bar": ""}, {"bar": true}]}',
                ),
            },
            id="typeof-string-subexpressions-indexes-smart",
        ),
        pytest.param(
            {
                "package.json": "[]",
            },
            [
                ["type(@)", "object", "`{}`"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            "JMESPath 'type(@)' does not match."
                            " Expected 'object', returned 'array'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": "{}\n",
            },
            id="typeof-root-variable-manual",
        ),
        pytest.param(
            {"package.json": "[]"},
            [["type(@)", "object"]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            "JMESPath 'type(@)' does not match."
                            " Expected 'object', returned 'array'"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {"package.json": "{}\n"},
            id="typeof-root-variable-smart",
        ),
        pytest.param(
            {"package.json": "{}"},
            [
                [
                    "null",
                    True,
                    "deepmerge(@, `{}`, 'invalid-deepmerge-strategy')",
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][2]",
                        "message": (
                            'Invalid JMESPath "deepmerge(@, `{}`, '
                            "'invalid-deepmerge-strategy')\". Raised"
                            " JMESPath error: Invalid strategy"
                            " 'invalid-deepmerge-strategy' passed"
                            " to deepmerge() function, expected one of:"
                            " always_merger, conservative_merger, "
                            "merge_or_raise"
                        ),
                    },
                ),
            ],
            {"package.json": "{}"},
            id="deepmerge-invalid-strategy",
        ),
        pytest.param(
            {"package.json": "{}"},
            [
                [
                    "null",
                    True,
                    (
                        "deepmerge(@, `{}`,"
                        " [[['invalid-type', 'override']],"
                        " ['override'], ['override']]"
                        ")"
                    ),
                ],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][2]",
                        "message": (
                            "Invalid JMESPath"
                            " (\"deepmerge(@, `{}`, [[['invalid-type',"
                            " 'override']], ['override'], \"\n"
                            " \"['override']])\"). Raised JMESPath"
                            " error: Invalid type passed "
                            "to deepmerge() function in strategies array,"
                            " expected one of: str, bool, int, float,"
                            " list, dict, set"
                        ),
                    },
                ),
            ],
            {"package.json": "{}"},
            id="deepmerge-invalid-builtin-type",
        ),
        pytest.param(
            {"package.json": "{}"},
            [
                ["null", True, "`['"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][2]",
                        "message": (
                            'Invalid JMESPath expression "`[\'". Raised'
                            " JMESPath lexing error: Bad jmespath"
                            " expression: Unclosed ` delimiter:\n`['\n^"
                        ),
                    },
                ),
            ],
            {"package.json": "{}"},
            id="fixer-query-compilation-error",
        ),
        pytest.param(
            {"package.json": "{}"},
            [
                ["null", True, "contains(`1`, `1`)"],
            ],
            None,
            [
                (
                    InterruptingError,
                    {
                        "definition": ".JMESPathsMatch[0][2]",
                        "message": (
                            "Invalid JMESPath 'contains(`1`, `1`)'. Raised"
                            " JMESPath type error: In function contains(),"
                            " invalid type for value: 1, expected one of:"
                            " ['array', 'string'], received: \"number\""
                        ),
                    },
                ),
            ],
            {"package.json": "{}"},
            id="fixer-query-evaluation-error",
        ),
        pytest.param(
            {".editor.json": "{}"},
            [
                ['"".boolean_value', True],
                ['"*".string_value', "lf"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": ".editor.json",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "JMESPath '\"\".boolean_value' does not match."
                            " Expected True, returned None"
                        ),
                    },
                ),
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[1]",
                        "file": ".editor.json",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "JMESPath '\"*\".string_value' does not match."
                            " Expected 'lf', returned None"
                        ),
                    },
                ),
            ],
            {
                ".editor.json": JSON_2_INDENTED(
                    (
                        '{"": {"boolean_value": true},'
                        ' "*": {"string_value": "lf"}}'
                    ),
                ),
            },
            id="fixer-query-subexpression-smart",
        ),
        pytest.param(
            {"foo.json": '{"foo": 1, "bar": 2}'},
            [["contains(keys(@), 'foo')", False]],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "foo.json",
                        "fixable": True,
                        "fixed": True,
                        "message": (
                            "JMESPath 'contains(keys(@), 'foo')' does"
                            " not match. Expected False, returned True"
                        ),
                    },
                ),
            ],
            {
                "foo.json": JSON_2_INDENTED('{"bar": 2}'),
            },
            id="@-forbidden-key-smart",
        ),
    ),
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


@pytest.mark.parametrize(
    ("files", "value", "rule", "expected_results", "expected_files"),
    (
        pytest.param(
            {
                "package.json": '{"foo": "baz"}',
            },
            [
                ["null", True, "update(@, {bar: 'qux'})"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            "JMESPath 'null' does not match. Expected"
                            " True, returned None"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED(
                    '{"foo": "baz", "bar": "qux"}',
                ),
            },
            id="update()",
        ),
        pytest.param(
            {
                "package.json": '{"foo": "baz", "bar": 1}',
            },
            [
                ["null", True, "unset(@, 'foo')"],
            ],
            None,
            [
                (
                    Error,
                    {
                        "definition": ".JMESPathsMatch[0]",
                        "file": "package.json",
                        "message": (
                            "JMESPath 'null' does not match. Expected"
                            " True, returned None"
                        ),
                        "fixed": True,
                        "fixable": True,
                    },
                ),
            ],
            {
                "package.json": JSON_2_INDENTED('{"bar": 1}'),
            },
            id="unset()",
        ),
    ),
)
def test_JMESPathsMatch_updater_functions(
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
