import pytest

from project_config.reporters import default


@pytest.mark.parametrize(
    ("errors", "expected_result"),
    (
        pytest.param(
            [],
            "",
            id="empty",
        ),
        pytest.param(
            [
                {
                    "file": "foo.py",
                    "message": "message",
                    "definition": "definition",
                },
            ],
            "foo.py\n  - message definition",
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
            """foo.py
  - message 1 definition 1
  - message 2 definition 2
bar.py
  - message 3 definition 3""",
            id="complex",
        ),
    ),
)
def test_default_errors_report(errors, expected_result, assert_errors_report):
    assert_errors_report(default, errors, expected_result)


@pytest.mark.parametrize(
    ("data_key", "data", "expected_result"),
    (
        pytest.param(
            "config",
            {
                "cache": "5 minutes",
                "style": "foo.json5",
            },
            """cache: 5 minutes
style: foo.json5
""",
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
  - bar.json5
""",
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
      - bar.ext
""",
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
      [
        "line1",
        "line2"
      ]
""",
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
      not
        foo.ext: foo reason
        bar.ext: bar reason
    includeLines:
      [
        "line1",
        "line2"
      ]
    ifIncludeLines:
      {
        "if-inc-1.ext": [
          "if-inc-line-1",
          "if-inc-line-2"
        ]
      }
  - files:
      not
        - foo.ext
        - foo.bar
""",
            id="style-complex",
        ),
    ),
)
def test_default_data_report(
    data_key,
    data,
    expected_result,
    assert_data_report,
):
    assert_data_report(
        default,
        data_key,
        data,
        expected_result,
    )
