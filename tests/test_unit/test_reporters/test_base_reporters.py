import os

import pytest

from project_config.reporters.base import (
    BaseColorReporter,
    InvalidColors,
    colored_color_exists,
)


@pytest.mark.parametrize(
    ("color", "expected_result"),
    (
        pytest.param("red", True, id="valid-color"),
        pytest.param("impossible-color", False, id="invalid-color"),
    ),
)
def test_colored_color_exists(color, expected_result):
    if expected_result is False and "CI" in os.environ:
        pytest.skip("colored not supported on CI")
    assert colored_color_exists(color) == expected_result


class ColorReporter(BaseColorReporter):
    def generate_errors_report(self):
        return ""


def test_BaseColorReporter_init_fails():
    with pytest.raises(InvalidColors) as exc:
        ColorReporter(
            colors={
                "file": "red",
                "definition": "impossible-color",
                "invalid-formatter subject": "blue",
            },
        )

    additional_message = (
        "- Color 'impossible-color' not supported\n  "
        if "CI" not in os.environ
        else ""
    )

    assert (
        exc.value.message
        == f"""Invalid colors or subjects in 'colors' configuration for reporters:
  {additional_message}- Invalid subject 'invalid_formatter_subject' to colorize
"""  # noqa: E501
    )

    with pytest.raises(TypeError) as exc:
        BaseColorReporter()

    assert ("Can't instantiate abstract class BaseColorReporter with") in str(
        exc.value,
    )


def test_BaseColorReporter_init_ok(tmp_path):
    reporter = ColorReporter(
        str(tmp_path),
        colors={
            "config value": "red",
            "config key": "white",
        },
    )
    assert reporter.colors == {"config_value": "red", "config_key": "white"}
