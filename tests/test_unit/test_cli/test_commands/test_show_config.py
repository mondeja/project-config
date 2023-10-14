from project_config.__main__ import run


def test_show_config(capsys, chdir, tmp_path):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.bar"\ncache = "never"\n')

    with chdir(tmp_path):
        assert run(["show", "config", "--nocolor"]) == 0
    out, err = capsys.readouterr()
    assert out == "style: foo.bar\ncache: never\n"
    assert err == ""
