import os

from testing_helpers import rootdir

from project_config.plugins import Plugins


def test_plugin_actions_documented():
    reference_filepath = os.path.join(
        rootdir,
        "docs",
        "reference",
        "plugins.rst",
    )
    with open(reference_filepath, encoding="utf-8") as f:
        reference_lines = f.read().splitlines()

    line_index = 0
    current_plugin, current_action_name = {}, None
    plugins_doc_data = {}

    def _maybe_add_current_plugin():
        if current_plugin:
            current_plugin_name = current_plugin.pop("name")
            plugins_doc_data[current_plugin_name] = current_plugin

    while line_index < len(reference_lines):
        line = reference_lines[line_index]
        if line.startswith("*") and line.count("*") > 3 and line.endswith("*"):
            _maybe_add_current_plugin()
            current_plugin = {
                "name": reference_lines[line_index + 1],
                "actions": {},
            }
            line_index += 3
            continue
        elif (
            line.startswith("=") and line.count("=") > 3 and line.endswith("=")
        ):
            action_name = reference_lines[line_index - 1]
            current_plugin["actions"][action_name] = {
                "has_examples": False,
                "has_versionadded": False,
            }
            current_action_name = action_name
        elif line.startswith(".. rubric:: Example"):
            current_plugin["actions"][current_action_name][
                "has_examples"
            ] = True
        elif line.startswith(".. versionadded:: "):
            current_plugin["actions"][current_action_name][
                "has_versionadded"
            ] = True
        line_index += 1
    _maybe_add_current_plugin()

    # assert all actions are properly documented
    for plugin_name, actions in Plugins().plugin_action_names.items():
        assert plugin_name in plugins_doc_data

        for action_name in actions:
            plugin_doc_actions_data = plugins_doc_data[plugin_name]["actions"]
            assert action_name in plugin_doc_actions_data
            assert plugin_doc_actions_data[action_name]["has_examples"]
            assert plugin_doc_actions_data[action_name]["has_versionadded"]
