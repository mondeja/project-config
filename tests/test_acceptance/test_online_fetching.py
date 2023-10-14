from project_config.__main__ import run
from testing_helpers import mark_end2end


@mark_end2end
def test_online_fetching_example_ok(tmp_path, capsys, chdir):
    project_config_toml = tmp_path / ".project-config.toml"
    project_config_toml.write_text(
        "style ="
        ' "gh://mondeja/project-config/tests/data/styles/foo/style-1.json5"',
    )

    with chdir(tmp_path):
        exitcode = run(["check"])
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""
        assert exitcode == 0


@mark_end2end
def test_online_fetching_example_fails(tmp_path, capsys, chdir):
    project_config_toml = tmp_path / ".project-config.toml"
    project_config_toml.write_text(
        "style ="
        ' "gh://mondeja/project-config/tests/data/styles/bar/style-2.yaml"',
    )

    with chdir(tmp_path):
        exitcode = run(["check"])
        out, err = capsys.readouterr()
        assert out == ""
        assert "JMESPath 'style' does not match. Expected" in err
        assert exitcode == 1
