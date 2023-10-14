import pytest
from project_config.__main__ import run


def test_conditionals_run_before_files_existence_check(
    tmp_path,
    capsys,
    chdir,
):
    project_config_toml = tmp_path / ".project-config.toml"
    project_config_toml.write_text(
        'style = "style.json5"\n',
    )

    style_json5 = tmp_path / "style.json5"
    style_json5.write_text(
        """{
  rules: [
    {
      files: ["foo.txt"],
      ifFilesExist: ["foo.txt"],
    }
  ]
}
""",
    )

    with chdir(tmp_path):
        exitcode = run(["check", "--nocolor"])
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""
        assert exitcode == 0


@pytest.mark.parametrize(
    "filename",
    ("./foo/bar/baz/style.json5", "foo/bar/baz/style2.json5"),
)
@pytest.mark.parametrize(
    "config_filename",
    (".project-config.toml", "pyproject.toml"),
)
def test_read_config_local_styles(
    filename,
    config_filename,
    tmp_path,
    chdir,
    capsys,
):
    """Test that local styles are valid when using local paths
    starting with ``./`` or not.
    """
    project_config_config_file = tmp_path / config_filename
    group_line = (
        "[tool.project-config]" if config_filename == "pyproject.toml" else ""
    )
    project_config_config_file.write_text(
        f"""{group_line}
        style = ["{filename}"]
        """,
    )
    path = tmp_path / filename
    path.parents[0].mkdir(parents=True, exist_ok=True)
    path.write_text("{rules: [{files: ['" + filename + "']}]}")

    with chdir(tmp_path):
        exitcode = run(["check", "--nocolor"])
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""
        assert exitcode == 0
