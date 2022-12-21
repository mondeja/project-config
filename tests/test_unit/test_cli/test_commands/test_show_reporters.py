"""Tests for 'project-config show reporters' command."""

from project_config.__main__ import run
from project_config.compat import importlib_metadata
from project_config.reporters import (
    PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
    reporters,
)


def test_show_reporters(capsys, mocker):
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            importlib_metadata.EntryPoint(
                "valid-reporters",
                "testing_helpers.valid_3rd_party_reporters_module",
                PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
            ),
            *importlib_metadata.entry_points(
                group=PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
            ),
        ],
    )

    possible_expected_reporters = ["valid-reporters", *list(reporters)]

    assert run(["show", "reporters"]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    for quoted_reporter in out.rstrip("\r\n").split(" "):
        reporter_id = quoted_reporter.strip(",'")
        assert reporter_id in possible_expected_reporters
