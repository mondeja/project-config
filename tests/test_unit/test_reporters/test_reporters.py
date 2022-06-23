import pytest

from project_config.compat import importlib_metadata
from project_config.reporters import (
    PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
    InvalidNotBasedThirdPartyReporter,
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
    "color",
    (False, True),
    ids=("color=False", "color=True"),
)
@pytest.mark.parametrize(
    (
        "entrypoint_name",
        "entrypoint_value",
        "expected_exception_class",
        "expected_error_message",
    ),
    (
        pytest.param(
            "no-bw-reporter",
            "testing_helpers.invalid_no_bw_3rd_party_reporters_module",
            InvalidThirdPartyReportersModule,
            "No black/white reporter found in module",
            id="no-black/white",
        ),
        pytest.param(
            "no-color-reporter",
            "testing_helpers.invalid_no_color_3rd_party_reporters_module",
            InvalidThirdPartyReportersModule,
            "No color reporter found in module",
            id="no-color",
        ),
        pytest.param(
            "multiple-bw-reporter",
            "testing_helpers.invalid_multiple_bw_3rd_party_reporters_module",
            InvalidThirdPartyReportersModule,
            "Multiple public black/white reporters found in module",
            id="multiple-black/white",
        ),
        pytest.param(
            "multiple-color-reporter",
            "testing_helpers.invalid_multiple_color_3rd_party_reporters_module",
            InvalidThirdPartyReportersModule,
            "Multiple public color reporters found in module",
            id="multiple-color",
        ),
        pytest.param(
            "valid-reporters",
            "testing_helpers.valid_3rd_party_reporters_module",
            None,
            None,
            id="valid",
        ),
        pytest.param(
            "not-based-color-reporter",
            "testing_helpers.invalid_not_based_color_reporter_module",
            InvalidNotBasedThirdPartyReporter,
            (
                "Reporter class 'InvalidNotBasedColorReporter' is not a"
                " subclass of BaseReporter"
            ),
            id="not-based-color",
        ),
        pytest.param(
            "not-based-bw-reporter",
            "testing_helpers.invalid_not_based_bw_reporter_module",
            InvalidNotBasedThirdPartyReporter,
            (
                "Reporter class 'InvalidNotBasedReporter' is not a subclass"
                " of BaseReporter"
            ),
            id="not-based-black/white",
        ),
    ),
)
def test_get_3rd_party_reporter(
    entrypoint_name,
    entrypoint_value,
    expected_exception_class,
    expected_error_message,
    color,
    mocker,
    tmp_path,
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

    if expected_error_message is None:
        get_reporter(
            entrypoint_name,
            color,
            str(tmp_path),
        )
    else:
        with pytest.raises(
            expected_exception_class,
            match=expected_error_message,
        ):
            get_reporter(
                entrypoint_name,
                color,
                str(tmp_path),
            )

    # reset the instance to load other reporters in susequent executions
    ThirdPartyReporters.instance = None
