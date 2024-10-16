import os

from jmespath.functions import Functions as project_config_functions

from project_config.plugins import Plugins
from project_config.utils.jmespath import jmespath_options
from testing_helpers import rootdir


PLUGINS_REFERENCE_FILEPATH = os.path.join(
    rootdir,
    "docs",
    "reference",
    "plugins.rst",
)
JMESPATH_UTILS_MODULE_PATH = os.path.join(
    rootdir,
    "src",
    "project_config",
    "utils",
    "jmespath.py",
)


def get_file_lines(filepath):
    with open(filepath, encoding="utf-8") as f:
        return f.read().splitlines()


def get_project_config_jmespath_functions_from_impl():
    original_jmespath_functions = dir(project_config_functions)

    custom_function_names = []
    for method_name in dir(jmespath_options.custom_functions):
        if method_name.startswith("_func_") and (
            method_name not in original_jmespath_functions
        ):
            custom_function_names.append(method_name[6:])

    module_lines = get_file_lines(JMESPATH_UTILS_MODULE_PATH)
    for line in module_lines:
        if "_func_" in line:
            try:
                function_name = line.lstrip().split(" _func_")[1].split("(")[0]
            except IndexError:
                continue
            if function_name not in custom_function_names:
                custom_function_names.append(function_name)
    return custom_function_names


def test_plugin_actions_documented():
    reference_lines = get_file_lines(PLUGINS_REFERENCE_FILEPATH)

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
        if line.startswith("=") and line.count("=") > 3 and line.endswith("="):
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


def test_jmespath_custom_functions_documented():
    """Assert that all JMESPath custom functions are documented."""
    custom_function_names = get_project_config_jmespath_functions_from_impl()

    _inside_jmespath = False
    documented_function_names = []

    line_index = 0
    reference_lines = get_file_lines(PLUGINS_REFERENCE_FILEPATH)
    while True:
        try:
            line = reference_lines[line_index]
        except IndexError:
            break
        if not _inside_jmespath and line == "jmespath":
            _inside_jmespath = True
            line_index += 2
            continue
        if _inside_jmespath:
            if line.startswith("****"):
                break
            if line.startswith(".. function::"):
                function_name = line.split(" ")[2].split("(")[0]
                documented_function_names.append(function_name)
        line_index += 1

    assert sorted(custom_function_names) == sorted(documented_function_names)
