import pytest
from project_config.config import _validate_cli_config, validate_cli_config
from project_config.config.exceptions import ProjectConfigInvalidConfigSchema


@pytest.mark.parametrize(
    ("config", "expected_result"),
    (
        pytest.param(
            {"reporter": 1},
            ["cli.reporter -> must be of type string"],
            id="invalid-reporter-type",
        ),
        pytest.param(
            {"reporter": ""},
            ["cli.reporter -> must not be empty"],
            id="empty-reporter",
        ),
        pytest.param(
            {"reporter": "invalid-and-impossible-reporter"},
            ["cli.reporter -> must be one of the available reporters"],
            id="invalid-reporter",
        ),
        pytest.param(
            {"reporter": "json"},
            [],
            id="valid-reporter",
        ),
        pytest.param(
            {"color": 1},
            ["cli.color -> must be of type boolean"],
            id="invalid-color-type",
        ),
        pytest.param(
            {"color": True},
            [],
            id="valid-color",
        ),
        pytest.param(
            {"colors": True},
            ["cli.colors -> must be of type object"],
            id="invalid-colors-type",
        ),
        pytest.param(
            {"colors": {}},
            ["cli.colors -> must not be empty"],
            id="empty-colors",
        ),
        pytest.param(
            {"colors": {"file": "blue"}},
            [],
            id="valid-colors",
        ),
        pytest.param(
            {"rootdir": 0},
            ["cli.rootdir -> must be of type string"],
            id="invalid-rootdir-type",
        ),
        pytest.param(
            {"rootdir": ""},
            ["cli.rootdir -> must not be empty"],
            id="empty-rootdir",
        ),
        pytest.param(
            {"rootdir": "src"},
            [],
            id="valid-rootdir",
        ),
    ),
)
def test_validate_cli_config_errors(config, expected_result):
    assert _validate_cli_config(config) == expected_result


def test_validate_cli_config_exception(tmp_path):
    expected_error_message = (
        f"The configuration at {str(tmp_path)} is invalid:\n"
        "  - cli.rootdir -> must not be empty"
    )
    with pytest.raises(ProjectConfigInvalidConfigSchema) as exc:
        validate_cli_config(str(tmp_path), {"rootdir": ""})
    assert exc.value.message == expected_error_message
