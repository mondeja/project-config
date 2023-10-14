import os

import pytest
from project_config.config import (
    CONFIG_CACHE_REGEX,
    validate_config,
    validate_config_cache,
    validate_config_style,
)
from project_config.config.exceptions import ProjectConfigInvalidConfigSchema


VALIDATE_CONFIG_STYLE_CASES = (
    pytest.param({}, ["style -> at least one is required"], id="no-style"),
    pytest.param({"style": "foo"}, [], id="string"),
    pytest.param(
        {"style": ""},
        ["style -> must not be empty"],
        id="empty-string",
    ),
    pytest.param(
        {"style": 1},
        ["style -> must be of type string or array"],
        id="int",
    ),
    pytest.param(
        {"style": True},
        ["style -> must be of type string or array"],
        id="bool",
    ),
    pytest.param(
        {"style": []},
        ["style -> at least one is required"],
        id="empty-list",
    ),
    pytest.param({"style": ["foo"]}, [], id="list[string]"),
    pytest.param(
        {"style": [""]},
        ["style[0] -> must not be empty"],
        id="list[empty-string]",
    ),
    pytest.param(
        {"style": [1]},
        ["style[0] -> must be of type string"],
        id="list[int]",
    ),
    pytest.param(
        {"style": [True]},
        ["style[0] -> must be of type string"],
        id="list[bool]",
    ),
    pytest.param(
        {"style": ["foo", True]},
        ["style[1] -> must be of type string"],
        id="list[str, bool]",
    ),
)

VALIDATE_CONFIG_CACHE_CASES = (
    pytest.param({}, [], id="no-cache"),
    pytest.param({"cache": 1}, ["cache -> must be of type string"], id="int"),
    pytest.param(
        {"cache": ""},
        ["cache -> must not be empty"],
        id="empty-string",
    ),
    pytest.param(
        {"cache": "6557567 trillones de años"},
        [f"cache -> must match the regex {CONFIG_CACHE_REGEX}"],
        id="invalid-regex",
    ),
)

VALIDATE_CONFIG_CASES = []
for style_case in VALIDATE_CONFIG_STYLE_CASES:
    for cache_case in VALIDATE_CONFIG_CACHE_CASES:
        VALIDATE_CONFIG_CASES.append(
            pytest.param(
                {**style_case.values[0], **cache_case.values[0]},
                [*style_case.values[1], *cache_case.values[1]],
                id=f"style={style_case.id},cache={cache_case.id}",
            ),
        )


def cfg_with_path(config):
    config["_path"] = os.getcwd()
    return config


@pytest.mark.parametrize(
    ("config", "expected_error_messages"),
    VALIDATE_CONFIG_STYLE_CASES,
)
def test_validate_config_style(config, expected_error_messages):
    assert (
        validate_config_style(cfg_with_path(config)) == expected_error_messages
    )


@pytest.mark.parametrize(
    ("config", "expected_error_messages"),
    VALIDATE_CONFIG_CACHE_CASES,
)
def test_validate_config_cache(config, expected_error_messages):
    assert validate_config_cache(config) == expected_error_messages


@pytest.mark.parametrize(
    ("config", "expected_error_messages"),
    VALIDATE_CONFIG_CASES,
)
def test_validate_config(config, expected_error_messages):
    if not expected_error_messages:
        validate_config("foo", cfg_with_path(config))
    else:
        with pytest.raises(ProjectConfigInvalidConfigSchema) as exc_info:
            validate_config("foo", cfg_with_path(config))

        # replace because there are escape characters in regexes
        exc_messages = str(exc_info.value).replace("\\\\", "\\")
        for expected_error_message in expected_error_messages:
            assert expected_error_message in exc_messages
