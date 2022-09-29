import pytest

from project_config.__main__ import run


def test_show_file(capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')

    with chdir(tmp_path):
        assert run(["show", "file", str(project_config_file)]) == 0
    out, err = capsys.readouterr()
    assert out == '{"style": "foo.json5", "cache": "never"}\n'
    assert err == ""


@pytest.mark.parametrize(
    "fmt",
    ("pretty", "pretty4"),
    ids=("fmt=json:pretty", "fmt=json:pretty4"),
)
def test_show_file_pretty_output(fmt, capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')

    with chdir(tmp_path):
        exitcode = run(
            ["-r", f"json:{fmt}", "show", "file", str(project_config_file)],
        )
    assert exitcode == 0
    out, err = capsys.readouterr()

    expected_indent = "  " if fmt == "pretty" else "    "
    assert out == (
        f'{{\n{expected_indent}"style": "foo.json5",'
        f'\n{expected_indent}"cache": "never"\n}}\n'
    )
    assert err == ""
