import pytest

from project_config.serializers import (
    _identify_serializer,
    guess_preferred_serializer,
)


@pytest.mark.parametrize(
    ("filename", "expected_serializer"),
    (
        pytest.param(
            ".editorconfig",
            "editorconfig",
            id=".editorconfig-editorconfig",
        ),
        pytest.param(
            "impossibleeverfilenaming.extension",
            "text",
            id="fallback-text",
        ),
        pytest.param(
            "foo.py",
            "text",
            id=".py-text",
        ),
    ),
)
def test__identify_serializer(filename, expected_serializer):
    assert _identify_serializer(filename) == expected_serializer


@pytest.mark.parametrize(
    ("filename", "expected_serializer"),
    (
        pytest.param(
            ".editorconfig",
            "editorconfig",
            id=".editorconfig-editorconfig",
        ),
        pytest.param(
            "impossibleeverfilenaming.extension",
            "text",
            id="fallback-text",
        ),
        pytest.param(
            "foo.py",
            "py",
            id=".py-py",
        ),
    ),
)
def test_guess_preferred_serializer(filename, expected_serializer):
    result_filename, result_serializer = guess_preferred_serializer(filename)
    assert result_serializer == expected_serializer
    assert result_filename == filename
