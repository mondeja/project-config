import copy

import pytest
from testing_helpers import parametrize_color

from project_config.reporters.default import (
    DefaultColorReporter,
    DefaultReporter,
)


@parametrize_color
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
def test_default_errors_report(
    color,
    errors,
    expected_result,
    tmp_path,
    monkeypatch,
):
    reporter = (DefaultColorReporter if color else DefaultReporter)(
        str(tmp_path),
    )
    for error in errors:
        if "file" in error:
            error["file"] = str(tmp_path / error["file"])
        reporter.report_error(error)

    if color:
        monkeypatch.setenv("NO_COLOR", "true")  # disable color a moment
    assert reporter.generate_errors_report() == expected_result


@parametrize_color
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
    color,
    data_key,
    data,
    expected_result,
    tmp_path,
    monkeypatch,
):
    reporter = (DefaultColorReporter if color else DefaultReporter)(
        str(tmp_path),
    )

    if color:
        monkeypatch.setenv("NO_COLOR", "true")
    assert (
        reporter.generate_data_report(
            data_key,
            copy.deepcopy(data),  # data is manipulated inplace
        )
        == expected_result
    )
