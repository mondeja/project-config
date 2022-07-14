from project_config.__main__ import run


def test_file_not_exists_is_created(tmp_path, chdir, monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "true")
    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        '{rules: [{files: ["README.md", ".gitignore"]}]}',
    )

    with chdir(tmp_path):
        assert run(["fix"]) == 1
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "README.md").read_text() == ""

        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / ".gitignore").read_text() == ""

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == """README.md
  - (FIXED) Expected existing file does not exists rules[0].files[0]
.gitignore
  - (FIXED) Expected existing file does not exists rules[0].files[1]
"""
    )


def test_directory_not_exists_is_created(tmp_path, chdir, monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "true")
    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        '{rules: [{files: ["docs/", "src/"]}]}',
    )

    with chdir(tmp_path):
        assert run(["fix"]) == 1
        assert (tmp_path / "docs").is_dir()
        assert (tmp_path / "src").is_dir()

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == """docs/
  - (FIXED) Expected existing directory does not exists rules[0].files[0]
src/
  - (FIXED) Expected existing directory does not exists rules[0].files[1]
"""
    )


def test_file_dir_exist_is_removed(tmp_path, chdir, monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "true")
    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        """{
  rules: [
    {
      files: {not: ["README.md", "src/"]},
    },
    {
      files: {not: {
        ".gitignore": "The project must not be a GIT repository",
        "docs/": "Documentation is forbidden",
      }}
    }
  ]
}
""",
    )

    (tmp_path / "README.md").write_text("")
    (tmp_path / "src").mkdir()
    (tmp_path / ".gitignore").write_text("")
    (tmp_path / "docs").mkdir()

    with chdir(tmp_path):
        assert run(["fix"]) == 1
        assert not (tmp_path / "README.md").exists()
        assert not (tmp_path / "src").exists()
        assert not (tmp_path / ".gitignore").exists()
        assert not (tmp_path / "docs").exists()

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == """README.md
  - (FIXED) Expected absent file exists rules[0].files.not[0]
src/
  - (FIXED) Expected absent directory exists rules[0].files.not[1]
.gitignore
  - (FIXED) Expected absent file exists. The project must not be a GIT repository rules[1].files.not[.gitignore]
docs/
  - (FIXED) Expected absent directory exists. Documentation is forbidden rules[1].files.not[docs/]
"""  # noqa: E501
    )


def test_fixed_files_dirs_are_recached(tmp_path, chdir, monkeypatch, capsys):
    """Assert that fixed files and directories are updated in ``tree`` cache."""
    monkeypatch.setenv("NO_COLOR", "true")

    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        """{
  rules: [
    {
      files: {not: ["README.md", "src/"]},
    },
    {
      files: {not: {
        ".gitignore": "The project must not be a GIT repository",
        "docs/": "Documentation is forbidden",
      }}
    },
    {
      files: ["README.md", "src/", ".gitignore", "docs/"]
    }
  ]
}
""",
    )

    with chdir(tmp_path):
        assert run(["fix"]) == 1
        out, err = capsys.readouterr()
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / "README.md").read_text() == ""
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / ".gitignore").read_text() == ""
        assert (tmp_path / "docs").is_dir()
        assert (tmp_path / "src").is_dir()

    assert out == ""
    assert (
        err
        == """README.md
  - (FIXED) Expected existing file does not exists rules[2].files[0]
src/
  - (FIXED) Expected existing directory does not exists rules[2].files[1]
.gitignore
  - (FIXED) Expected existing file does not exists rules[2].files[2]
docs/
  - (FIXED) Expected existing directory does not exists rules[2].files[3]
"""
    )  # noqa: E501
