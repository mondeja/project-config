import json

import pytest
from project_config.reporters import json_


parametrize_formats = pytest.mark.parametrize(
    "fmt",
    (None, "pretty", "pretty4"),
    ids=("format=default", "format=pretty", "format=pretty4"),
)

ERROR_REPORTS_PARAMETERS = (
    pytest.param(
        [],
        "{}",
        id="ok",
    ),
    pytest.param(
        [
            {
                "file": "foo.py",
                "message": "message",
                "definition": "definition",
            },
        ],
        '{"foo.py": [{"message": "message", "definition": "definition"}]}',
        id="basic",
    ),
    pytest.param(
        [
            {
                "file": "foo.py",
                "message": "message 1",
                "definition": "definition 1",
            },
            {
                "file": "foo.py",
                "message": "message 2",
                "definition": "definition 2",
                "hint": "a hint to solve it",
            },
            {
                "file": "bar.py",
                "message": "message 3",
                "definition": "definition 3",
            },
        ],
        (
            '{"foo.py": [{"message": "message 1", "definition":'
            ' "definition 1"}, {"message": "message 2", "definition":'
            ' "definition 2", "hint": "a hint to solve it"}], "bar.py":'
            ' [{"message": "message 3", "definition": "definition 3"}]}'
        ),
        id="complex",
    ),
)

DATA_REPORTS_PARAMETERS = (
    pytest.param(
        "config",
        {
            "cache": "5 minutes",
            "style": "foo.json5",
        },
        '{"cache": "5 minutes", "style": "foo.json5"}',
        id="config-style-string",
    ),
    pytest.param(
        "config",
        {
            "cache": "5 minutes",
            "style": ["foo.json5", "bar.json5"],
        },
        '{"cache": "5 minutes", "style": ["foo.json5", "bar.json5"]}',
        id="config-style-array",
    ),
    pytest.param(
        "style",
        {
            "rules": [
                {
                    "files": ["foo.ext", "bar.ext"],
                },
            ],
        },
        '{"rules": [{"files": ["foo.ext", "bar.ext"]}]}',
        id="style-basic",
    ),
    pytest.param(
        "style",
        {
            "plugins": ["plugin_foo"],
            "rules": [
                {
                    "files": ["foo.ext", "bar.ext"],
                },
                {
                    "files": ["foo.ext", "bar.ext"],
                    "includeLines": ["line1", "line2"],
                },
            ],
        },
        (
            '{"plugins": ["plugin_foo"], "rules": [{"files":'
            ' ["foo.ext", "bar.ext"]}, {"files": ["foo.ext",'
            ' "bar.ext"], "includeLines": ["line1", "line2"]}]}'
        ),
        id="style-multiple-rules",
    ),
    pytest.param(
        "style",
        {
            "plugins": ["plugin_foo", "plugin_bar"],
            "rules": [
                {
                    "files": ["foo.ext", "bar.ext"],
                },
                {
                    "files": {
                        "not": {
                            "foo.ext": "foo reason",
                            "bar.ext": "bar reason",
                        },
                    },
                    "includeLines": ["line1", "line2"],
                    "ifIncludeLines": {
                        "if-inc-1.ext": ["if-inc-line-1", "if-inc-line-2"],
                    },
                },
                {
                    "files": {"not": ["foo.ext", "foo.bar"]},
                },
            ],
        },
        (
            '{"plugins": ["plugin_foo", "plugin_bar"], "rules":'
            ' [{"files": ["foo.ext", "bar.ext"]}, {"files": {"not":'
            ' {"foo.ext": "foo reason", "bar.ext": "bar reason"}},'
            ' "includeLines": ["line1", "line2"], "ifIncludeLines":'
            ' {"if-inc-1.ext": ["if-inc-line-1", "if-inc-line-2"]}},'
            ' {"files": {"not": ["foo.ext", "foo.bar"]}}]}'
        ),
        id="style-complex",
    ),
    pytest.param(
        "plugins",
        {"foo": ["bar", "baz"], "rain": ["dirt", "sand"]},
        '{"foo": ["bar", "baz"], "rain": ["dirt", "sand"]}',
        id="plugins",
    ),
)


def _expected_result_by_format(expected_result, fmt):
    if fmt == "pretty":
        expected_result = json.dumps(json.loads(expected_result), indent=2)
    elif fmt == "pretty4":
        expected_result = json.dumps(
            json.loads(expected_result),
            indent=4,
        )
    return expected_result


@parametrize_formats
@pytest.mark.parametrize(
    ("errors", "expected_result"),
    ERROR_REPORTS_PARAMETERS,
)
def test_errors_report(
    errors,
    expected_result,
    fmt,
    assert_errors_report,
):
    assert_errors_report(
        json_,
        errors,
        _expected_result_by_format(expected_result, fmt),
        fmt=fmt,
    )


@parametrize_formats
@pytest.mark.parametrize(
    ("data_key", "data", "expected_result"),
    DATA_REPORTS_PARAMETERS,
)
def test_data_report(
    data_key,
    data,
    expected_result,
    fmt,
    assert_data_report,
):
    assert_data_report(
        json_,
        data_key,
        data,
        _expected_result_by_format(expected_result, fmt),
        fmt=fmt,
    )
