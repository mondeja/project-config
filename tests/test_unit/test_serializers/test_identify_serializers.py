import pytest

from project_config.serializers import _identify_serializer, serializers


@pytest.mark.parametrize(
    ("filename", "expected_serializer"),
    (
        pytest.param(
            ".editorconfig",
            serializers[".editorconfig"],
            id="editorconfig",
        ),
        pytest.param(
            "impossibleeverfilenaming.extension",
            serializers[".json"],
            id="fallback",
        ),
    ),
)
def test__identify_serializer(filename, expected_serializer):
    return _identify_serializer(filename) == expected_serializer
