import json

from project_config.__main__ import run
from project_config.plugins import Plugins


def test_show_plugins(tmp_path, chdir, capsys):

    with chdir(tmp_path):
        project_config_file = tmp_path / ".project-config.toml"
        project_config_file.write_text('style = "style.json"')

        style_file = tmp_path / "style.json"
        style_file.write_text(json.dumps({"rules": [{"files": "style.json"}]}))

        assert run(["show", "plugins", "--nocolor"]) == 0
        out, err = capsys.readouterr()
        assert err == ""

        stdout_lines = out.splitlines()

        expected_plugins_names = Plugins().plugin_names

        outputted_plugin_names = []
        for i, line in enumerate(stdout_lines):
            if not line.startswith("  "):
                plugin_name = line.rstrip(":")
                assert plugin_name in expected_plugins_names
                assert stdout_lines[i + 1].startswith("  - ")
                outputted_plugin_names.append(plugin_name)

        for expected_plugin_name in expected_plugins_names:
            assert expected_plugin_name in outputted_plugin_names
