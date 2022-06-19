import re

import pytest

from project_config.config import CONFIG_CACHE_REGEX, _cache_string_to_seconds


@pytest.mark.parametrize(
    ("value", "expected_result"),
    (
        ("5 minutes", 60 * 5),
        ("1 minutes", 60),
        ("1 minute", 60),
        ("1 hour", 60**2),
        ("3 hour", 60**2 * 3),
        ("6 days", 60**2 * 24 * 6),
        ("5 day", 60**2 * 24 * 5),
        ("36 second", 36),
        ("102 seconds", 102),
        ("300 tropecientos de trillones de decenios", ValueError),
        ("750 foobarbazes", ValueError),
        ("45 secondhours", 45 * 60**2),  # the comparation is lazy
        ("never", 0),
        ("4 weeks", 60**2 * 24 * 7 * 4),
        ("2 week", 60**2 * 24 * 7 * 2),
    ),
)
def test_cache_string_to_seconds(value, expected_result, maybe_raises):
    with maybe_raises(expected_result):
        assert _cache_string_to_seconds(value) == expected_result

    if hasattr(expected_result, "__traceback__"):
        assert not re.match(CONFIG_CACHE_REGEX, value)
    else:
        assert re.match(CONFIG_CACHE_REGEX, value)
