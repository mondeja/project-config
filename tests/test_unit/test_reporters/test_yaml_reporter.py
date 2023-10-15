import pytest
from project_config.reporters import yaml


@pytest.mark.parametrize(
    ("errors", "expected_result"),
    (
        pytest.param(
            [],
            "",
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
            """foo.py:
  - message: message
    definition: definition""",
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
            """foo.py:
  - message: message 1
    definition: definition 1
  - message: message 2
    definition: definition 2
    hint: a hint to solve it
bar.py:
  - message: message 3
    definition: definition 3""",
            id="complex",
        ),
    ),
)
def test_errors_report(
    errors,
    expected_result,
    assert_errors_report,
):
    assert_errors_report(
        yaml,
        errors,
        expected_result,
        color=False,
    )


@pytest.mark.parametrize(
    ("data_key", "data", "expected_result"),
    (
        pytest.param(
            "config",
            {
                "cache": "5 minutes",
                "style": "foo.json5",
            },
            "cache: 5 minutes\nstyle: foo.json5",
            id="config-style-string",
        ),
        pytest.param(
            "config",
            {
                "cache": "5 minutes",
                "style": ["foo.json5", "bar.json5"],
            },
            """cache: 5 minutes
style:
  - foo.json5
  - bar.json5""",
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
            """rules:
  - files:
      - foo.ext
      - bar.ext""",
            id="style-basic",
        ),
        pytest.param(
            "style",
            {
                "plugins": [],
                "rules": [
                    {
                        "files": ["foo.ext", "bar.ext"],
                    },
                ],
            },
            """rules:
  - files:
      - foo.ext
      - bar.ext""",
            id="style-empty-plugins",
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
            """plugins:
  - plugin_foo
rules:
  - files:
      - foo.ext
      - bar.ext
  - files:
      - foo.ext
      - bar.ext
    includeLines:
      - line1
      - line2""",
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
            """plugins:
  - plugin_foo
  - plugin_bar
rules:
  - files:
      - foo.ext
      - bar.ext
  - files:
      not:
        foo.ext: foo reason
        bar.ext: bar reason
    includeLines:
      - line1
      - line2
    ifIncludeLines:
      if-inc-1.ext:
        - if-inc-line-1
        - if-inc-line-2
  - files:
      not:
        - foo.ext
        - foo.bar""",
            id="style-complex",
        ),
        pytest.param(
            "plugins",
            {"foo": ["bar", "baz"], "rain": ["dirt", "sand"]},
            """foo:
  - bar
  - baz
rain:
  - dirt
  - sand""",
            id="plugins",
        ),
    ),
)
def test_data_report(
    data_key,
    data,
    expected_result,
    assert_data_report,
):
    assert_data_report(
        yaml,
        data_key,
        data,
        expected_result,
    )
