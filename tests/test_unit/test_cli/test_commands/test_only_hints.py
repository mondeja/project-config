from project_config.__main__ import run


def test_only_hints(chdir, tmp_path, capsys):
    (tmp_path / ".project-config.toml").write_text('style = "style.json5"')
    (tmp_path / "style.json5").write_text(
        '{rules: [{files: ["style.json5"],'
        ' JMESPathsMatch: [["type(@)", "array", "@"]],'
        ' hint: "The style root object must be an array"}]}',
    )

    with chdir(tmp_path):
        assert run(["fix", "--only-hints", "--no-color"]) == 1

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == """style.json5
  - (FIXED) The style root object must be an array rules[0].JMESPathsMatch[0]
"""
    )

    with chdir(tmp_path):
        assert run(["fix", "--only-hints", "--nocolor"]) == 1, f"{out}\n{err}"

    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err
        == """style.json5
  - (FIXED) The style root object must be an array rules[0].JMESPathsMatch[0]
"""
    )
