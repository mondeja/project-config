from project_config.__main__ import run


def test_conditionals_run_before_files_existence_check(tmp_path, capsys, chdir):
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
