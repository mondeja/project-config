import pytest
from contextlib_chdir import chdir as chdir_ctx


def _assert_minimal_valid_config(config, expected_style="foo"):
    assert isinstance(config, dict)
    assert len(config) == 1
    assert config["style"] == expected_style


def _minimal_valid_config_with_style(value):
    return f"style = '{value}'"


default_minimal_valid_config_string = _minimal_valid_config_with_style("foo")


@pytest.fixture
def minimal_valid_config():
    min_valid_config = type(
        "MinimalValidConfig",
        (),
        {
            "asserts": _assert_minimal_valid_config,
            "with_style": _minimal_valid_config_with_style,
        },
    )
    min_valid_config.string = default_minimal_valid_config_string
    return min_valid_config


@pytest.fixture
def chdir():
    return chdir_ctx
