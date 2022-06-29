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
    assert (
        exc.value.message
        == """Invalid colors or subjects in 'colors' configuration for reporters:
  - Color 'impossible-color' not supported
  - Invalid subject 'invalid_formatter_subject' to colorize
"""
    )

    with pytest.raises(TypeError) as exc:
        BaseColorReporter()
    assert str(exc.value) == (
        "Can't instantiate abstract class BaseColorReporter with abstract"
        " methods generate_errors_report"
    )


def test_BaseColorReporter_init_ok(tmp_path):
    reporter = ColorReporter(
        str(tmp_path),
        colors={
            "config value": "red",
            "config key": "#FFF",
        },
    )
    assert reporter.colors == {"config_value": "red", "config_key": "#FFF"}
