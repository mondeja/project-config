import pytest
from project_config.reporters import yaml


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
