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
  - definition: definition
    message: message""",
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
                },
                {
                    "file": "bar.py",
                    "message": "message 3",
                    "definition": "definition 3",
                },
            ],
            """bar.py:
  - definition: definition 3
    message: message 3
foo.py:
  - definition: definition 1
    message: message 1
  - definition: definition 2
    message: message 2""",
            id="complex",
        ),
    ),
)
def test_yaml_errors_report(
    errors,
    expected_result,
    assert_errors_report,
):
    assert_errors_report(
        yaml,
        errors,
        expected_result,
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
        bar.ext: bar reason
        foo.ext: foo reason
    ifIncludeLines:
      if-inc-1.ext:
        - if-inc-line-1
        - if-inc-line-2
    includeLines:
      - line1
      - line2
  - files:
      not:
        - foo.ext
        - foo.bar""",
            id="style-complex",
        ),
    ),
)
def test_yaml_data_report(
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
