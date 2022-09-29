from project_config.__main__ import run


def test_show_file(capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')

    with chdir(tmp_path):
        assert run(["show", "file", str(project_config_file)]) == 0
    out, err = capsys.readouterr()
    assert out == '{"style": "foo.json5", "cache": "never"}\n'
    assert err == ""


def test_show_file_pretty_output(capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')

    with chdir(tmp_path):
        exitcode = run(
            ["-r", "json:pretty", "show", "file", str(project_config_file)],
        )
    assert exitcode == 0
    out, err = capsys.readouterr()
    assert out == '{\n  "style": "foo.json5",\n  "cache": "never"\n}\n'
    assert err == ""
