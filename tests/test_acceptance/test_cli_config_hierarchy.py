import os

import pytest

from project_config.__main__ import parse_args
from project_config.project import Project


DEFAULT_REPORTER_VALUE = {"name": "default", "kwargs": {}}


@pytest.mark.parametrize(
    (
        "config",
        "cli_args",
        "environment_variables",
        "expected_reporter",
        "expected_color",
        "expected_rootdir",
    ),
    (
        pytest.param(
            "",
            [],
            {},
            DEFAULT_REPORTER_VALUE,
            None,  # is managed by reporters factory
            "{tmp_path}",
            id="default",
        ),
        pytest.param(
            "",
            [],
            {"NO_COLOR": "1"},
            DEFAULT_REPORTER_VALUE,
            None,  # is managed by `colored` library
            "{tmp_path}",
            id="color-env",
        ),
        pytest.param(
            "",
            ["--nocolor"],
            {},
            DEFAULT_REPORTER_VALUE,
            False,
            "{tmp_path}",
            id="color-cli",
        ),
        pytest.param(
            "[cli]\ncolor = false",
            [],
            {},
            DEFAULT_REPORTER_VALUE,
            False,
            "{tmp_path}",
            id="color-config",
        ),
        pytest.param(
            "[cli]\ncolor = true",
            ["--nocolor"],
            {},
            DEFAULT_REPORTER_VALUE,
            False,
            "{tmp_path}",
            id="color-config-cli",
        ),
        pytest.param(
            "[cli]\ncolor = true",
            [],
            {},
            DEFAULT_REPORTER_VALUE,
            True,
            "{tmp_path}",
            id="color-config",
        ),
        pytest.param(
            "",
            ["--rootdir", "root_directory"],
            {},
            DEFAULT_REPORTER_VALUE,
            None,
            os.path.join("{tmp_path}", "root_directory"),
            id="rootdir-cli",
        ),
        pytest.param(
            '[cli]\nrootdir = "root_directory"',
            [],
            {},
            DEFAULT_REPORTER_VALUE,
            None,
            os.path.join("{tmp_path}", "root_directory"),
            id="rootdir-config",
        ),
        pytest.param(
            '[cli]\nrootdir = "bar_directory"',
            ["--rootdir", "foo_directory"],
            {},
            DEFAULT_REPORTER_VALUE,
            None,
            os.path.join("{tmp_path}", "foo_directory"),
            id="rootdir-config-cli",
        ),
        pytest.param(
            "",
            ["--reporter", "toml"],
            {},
            {"name": "toml", "kwargs": {"fmt": None}},
            None,
            "{tmp_path}",
            id="reporter-cli",
        ),
        pytest.param(
            "",
            ["--reporter", "json:pretty"],
            {},
            {"name": "json", "kwargs": {"fmt": "pretty"}},
            None,
            "{tmp_path}",
            id="reporter:fmt-cli",
        ),
        pytest.param(
            '[cli]\nreporter = "toml"',
            [],
            {},
            {"kwargs": {}, "name": "toml"},
            None,
            "{tmp_path}",
            id="reporter-config",
        ),
        pytest.param(
            '[cli]\nreporter = "table:simple"',
            [],
            {},
            {"name": "table", "kwargs": {"fmt": "simple"}},
            None,
            "{tmp_path}",
            id="reporter:fmt-config",
        ),
        pytest.param(
            '[cli]\nreporter = "json:pretty"',
            ["-r", "table:simple"],
            {},
            {"name": "table", "kwargs": {"fmt": "simple"}},
            None,
            "{tmp_path}",
            id="reporter-cli-config",
        ),
        pytest.param(
            "",
            ["-r", 'json;colors={"file": "blue"}'],
            {},
            {
                "name": "json",
                "kwargs": {"fmt": None, "colors": {"file": "blue"}},
            },
            None,
            "{tmp_path}",
            id="reporter-cli-colors-cli",
        ),
        pytest.param(
            "",
            ["-r", 'json:pretty;colors={"file": "blue"}'],
            {},
            {
                "name": "json",
                "kwargs": {"fmt": "pretty", "colors": {"file": "blue"}},
            },
            None,
            "{tmp_path}",
            id="reporter:fmt-cli-colors-cli",
        ),
        pytest.param(
            '[cli]\nreporter = "json"\n\n[cli.colors]\nfile = "blue"',
            [],
            {},
            {
                "name": "json",
                "kwargs": {"colors": {"file": "blue"}},
            },
            None,
            "{tmp_path}",
            id="reporter-config-colors-config",
        ),
        pytest.param(
            '[cli]\nreporter = "json:pretty"\n\n[cli.colors]\nfile = "blue"',
            [],
            {},
            {
                "name": "json",
                "kwargs": {"fmt": "pretty", "colors": {"file": "blue"}},
            },
            None,
            "{tmp_path}",
            id="reporter:fmt-config-colors-config",
        ),
        pytest.param(
            '[cli]\nreporter = "json:pretty"\n\n[cli.colors]\nfile = "blue"',
            [],
            {},
            {
                "name": "json",
                "kwargs": {"fmt": "pretty", "colors": {"file": "blue"}},
            },
            None,
            "{tmp_path}",
            id="colors-config",
        ),
        pytest.param(
            '[cli.colors]\nfile = "blue"',
            ["-r", 'json:pretty;colors={"file": "magenta"}'],
            {},
            {
                "name": "json",
                "kwargs": {"fmt": "pretty", "colors": {"file": "magenta"}},
            },
            None,
            "{tmp_path}",
            id="colors-config-colors-cli",
        ),
    ),
)
def test_cli_config_hierarchy(
    config,
    cli_args,
    environment_variables,
    expected_reporter,
    expected_color,
    expected_rootdir,
    tmp_path,
    chdir,
    monkeypatch,
    minimal_valid_style,
):

    config_file = tmp_path / ".project-config.toml"
    config_file.write_text(f'style = "foo.json5"\n\n{config or ""}')

    style_file = tmp_path / "foo.json5"
    style_file.write_text(minimal_valid_style.string)

    cli_args.insert(0, "check")

    if environment_variables is None:
        environment_variables = {}
    for key, value in environment_variables.items():
        monkeypatch.setenv(key, value)

    expected_rootdir = expected_rootdir.replace("{tmp_path}", str(tmp_path))
    if not os.path.isdir(expected_rootdir):
        os.mkdir(expected_rootdir)

    args = parse_args(cli_args)

    project = Project(
        args.config,
        args.rootdir,
        args.reporter,
        args.color,
    )
    with chdir(tmp_path):
        project._load()

    assert project.reporter_ == expected_reporter
    assert project.color == expected_color
    assert project.rootdir == expected_rootdir
