import pytest

from project_config.__main__ import run
from project_config.config.exceptions import CustomConfigFileNotFound


def test_config_file_not_found(tmp_path, capsys, chdir):
    with chdir(tmp_path):
        run(["check", "-c", "unexistent-file.toml"])
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Custom configuration file 'unexistent-file.toml' not found\n"


def test_config_file_not_found_with_traceback(tmp_path, chdir):
    with chdir(tmp_path), pytest.raises(
        CustomConfigFileNotFound,
        match=r"^unexistent-file\.toml$",
    ):
        run(["check", "-c", "unexistent-file.toml", "-T"])


def test_style_file_not_found(tmp_path, capsys, chdir):
    config_file = tmp_path / ".project-config.toml"
    config_file.write_text('style = "style.json5"')
    with chdir(tmp_path):
        run(["check"])
    out, err = capsys.readouterr()
    assert out == ""
    assert err.startswith(
        "The configuration at .project-config.toml is invalid:",
    )


@pytest.mark.parametrize(
    "reporter_id",
    ("unexistent", "not-parseable;color=", "not-parseable;fmt="),
)
def test_invalid_reporter_option(
    tmp_path,
    chdir,
    capsys,
    reporter_id,
):
    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        "{rules: [{files: ['.project-config.toml']}]}",
    )

    with chdir(tmp_path):
        exitcode = run(["check", "-r", reporter_id])
    assert exitcode == 1

    out, err = capsys.readouterr()

    assert out == ""
    assert "project-config" in err


def test_remaining_args(tmp_path, chdir, capsys):
    with chdir(tmp_path), pytest.raises(SystemExit) as exc:
        run(["check", "--some-remaining-option"])
    assert exc.value.code == 1

    out, err = capsys.readouterr()
    assert "--help" in out
    assert err == ""
