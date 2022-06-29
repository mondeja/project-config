from project_config.__main__ import run


def test_show_style(capsys, tmp_path, chdir):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "foo.json5"\ncache = "never"\n')
    style_file = tmp_path / "foo.json5"
    style_file.write_text(
        """{
  rules: [
    {
      files: ["foo.json5"],
      JMESPathsMatch: [
        ["rules[0].JMESPathsMatch[0][0]", "rules[0].JMESPathsMatch[0][0]"]
      ]
    }
  ]
}""",
    )

    with chdir(tmp_path):
        assert run(["show", "style", "--nocolor"]) == 0
    out, err = capsys.readouterr()
    assert (
        out
        == """rules:
  - files:
      - foo.json5
    JMESPathsMatch:
      [
        [
          "rules[0].JMESPathsMatch[0][0]",
          "rules[0].JMESPathsMatch[0][0]"
        ]
      ]
"""
    )
    assert err == ""
