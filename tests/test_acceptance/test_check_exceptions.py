import json

import pytest

from project_config.commands.check import check
from project_config.compat import importlib_metadata
from project_config.exceptions import ProjectConfigCheckFailed
from project_config.plugins import PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP


@pytest.mark.parametrize("method_name", ("invalidFoo", "ifInvalidFoo"))
def test_check_invalid_plugin_functions(
    tmp_path,
    chdir,
    mocker,
    method_name,
    fake_cli_namespace,
):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "style.json"')

    invalid_plugin = importlib_metadata.EntryPoint(
        "invalid-no-staticmethod",
        (
            "testing_helpers.invalid_no_staticmethods_plugin"
            ":InvalidNoStaticMethodsPlugin"
        ),
        PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    default_plugin_entrypoints = importlib_metadata.entry_points(
        group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            invalid_plugin,
            *default_plugin_entrypoints,
        ],
    )

    style = {
        "plugins": ["invalid-no-staticmethod"],
        "rules": [{"files": [".project-config.toml"], method_name: "foo"}],
    }
    style_file = tmp_path / "style.json"
    style_file.write_text(json.dumps(style))

    with chdir(tmp_path):
        namespace = fake_cli_namespace(
            config=str(project_config_file),
            rootdir=str(tmp_path),
            color=False,
        )
        with pytest.raises(ProjectConfigCheckFailed) as exc:
            check(namespace)
        assert str(exc.value) == (
            f"[CONFIGURATION]\n  - The method '{method_name}' of the"
            " plugin 'invalid-no-staticmethod' (class"
            " 'InvalidNoStaticMethodsPlugin') must be a static method"
            f" rules[0].{method_name}"
        )


@pytest.mark.parametrize("method_name", ("invalidFoo", "ifInvalidFoo"))
def test_check_invalid_breakage_types(
    tmp_path,
    chdir,
    mocker,
    method_name,
    fake_cli_namespace,
):
    project_config_file = tmp_path / ".project-config.toml"
    project_config_file.write_text('style = "style.json"')

    invalid_plugin = importlib_metadata.EntryPoint(
        "invalid-breakage-type-yielder",
        (
            "testing_helpers.invalid_breakage_type_yielder_plugin"
            ":InvalidBreakageTypeYielderPlugin"
        ),
        PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    default_plugin_entrypoints = importlib_metadata.entry_points(
        group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            invalid_plugin,
            *default_plugin_entrypoints,
        ],
    )

    style = {
        "plugins": ["invalid-no-staticmethod"],
        "rules": [{"files": [".project-config.toml"], method_name: "foo"}],
    }
    style_file = tmp_path / "style.json"
    style_file.write_text(json.dumps(style))

    with chdir(tmp_path):
        namespace = fake_cli_namespace(
            config=str(project_config_file),
            rootdir=str(tmp_path),
            color=False,
        )
        with pytest.raises(NotImplementedError) as exc:
            check(namespace)
        expected_exc_message = (
            ("Breakage type 'foo' is not implemented for conditionals checking")
            if method_name.startswith("if")
            else ("Breakage type 'foo' is not implemented for verbal checking")
        )
        assert str(exc.value) == expected_exc_message
