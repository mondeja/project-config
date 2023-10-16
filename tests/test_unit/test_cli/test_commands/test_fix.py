import json

import pytest

from project_config.__main__ import run


@pytest.mark.parametrize(
    (
        "rules",
        "data_file_content",
        "fixed_data_file_content",
        "expected_fix_stderr",
    ),
    (
        pytest.param(
            [
                {
                    "files": ["data.json"],
                    "JMESPathsMatch": [
                        ["foo", "baz"],
                    ],
                },
            ],
            '{"foo": "bar"}',
            '{\n  "foo": "baz"\n}\n',
            (
                "data.json\n"
                "  - (FIXED) JMESPath 'foo' does not match."
                " Expected 'baz', returned 'bar' rules[0].JMESPathsMatch[0]\n"
            ),
            id="basic",
        ),
    ),
)
def test_fixes(
    rules,
    data_file_content,
    fixed_data_file_content,
    expected_fix_stderr,
    tmp_path,
    chdir,
    capsys,
):
    with chdir(tmp_path):
        project_config_file = tmp_path / ".project-config.toml"
        project_config_file.write_text('style = "style.json"')

        style_file = tmp_path / "style.json"
        style_file.write_text(json.dumps({"rules": rules}))

        data_file = tmp_path / "data.json"
        data_file.write_text(data_file_content)

        exitcode = run(["fix", "--nocolor"])
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == expected_fix_stderr, msg
        assert out == "", msg
        assert exitcode == 1, msg

        assert data_file.read_text() == fixed_data_file_content

        exitcode = run(["fix", "--nocolor"])
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert out == "", msg
        assert err == "", msg
        assert exitcode == 0, msg
