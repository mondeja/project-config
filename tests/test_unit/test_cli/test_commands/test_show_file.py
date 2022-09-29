from project_config.__main__ import run


def test_show_file(capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')

    with chdir(tmp_path):
        assert run(["show", "file", str(project_config_file)]) == 0
    out, err = capsys.readouterr()
    assert out == '{"style": "foo.json5", "cache": "never"}\n'
    assert err == ""
