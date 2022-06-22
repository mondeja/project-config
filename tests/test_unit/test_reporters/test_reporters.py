import pytest

from project_config.compat import importlib_metadata
from project_config.reporters import (
    PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
    InvalidThirdPartyReportersModule,
    ThirdPartyReporters,
    get_reporter,
    reporters,
)


@pytest.mark.parametrize("color", (False, True))
@pytest.mark.parametrize(
    ("reporter_id", "reporter_class_name"),
    (
        (reporter_id, reporter_class_name)
        for reporter_id, reporter_class_name in reporters.items()
    ),
)
def test_get_reporter(reporter_id, reporter_class_name, color, tmp_path):
    if color:
        reporter_class_name = reporter_class_name.replace(
            "Reporter",
            "ColorReporter",
        )
    assert (
        get_reporter(
            reporter_id,
            color,
            str(tmp_path),
        ).__class__.__name__
        == reporter_class_name
    )


@pytest.mark.parametrize(
    ("entrypoint_name", "entrypoint_value", "expected_error_message"),
    (
        pytest.param(
            "no-color-reporter",
            "testing_helpers.invalid_no_color_3rd_party_reporters_module",
            "No color reporter found in module",
            id="no-color",
        ),
        pytest.param(
            "no-bw-reporter",
            "testing_helpers.invalid_no_bw_3rd_party_reporters_module",
            "No black/white reporter found in module",
            id="no-black/white",
        ),
    ),
)
def test_get_invalid_3rd_party_reporter_modules(
    entrypoint_name,
    entrypoint_value,
    expected_error_message,
    mocker,
):
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            importlib_metadata.EntryPoint(
                entrypoint_name,
                entrypoint_value,
                PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
            ),
            *importlib_metadata.entry_points(
                group=PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
            ),
        ],
    )

    third_party_reporters = ThirdPartyReporters()
    reporter_module = third_party_reporters.load(entrypoint_name)
    with pytest.raises(
        InvalidThirdPartyReportersModule,
        match=expected_error_message,
    ):
        third_party_reporters.validate_reporter_module(reporter_module)

    ThirdPartyReporters.instance = None
