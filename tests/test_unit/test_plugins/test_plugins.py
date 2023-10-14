import os
import re

import pytest
from project_config.compat import importlib_metadata
from project_config.plugins import (
    PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    InvalidPluginFunction,
    Plugins,
)
from testing_helpers import FakePlugin, rootdir


PLUGINS_PACKAGE_DIR = os.path.join(rootdir, "src", "project_config", "plugins")
NUMBER_OF_DEFAULT_PLUGINS = len(
    [
        fname
        for fname in os.listdir(PLUGINS_PACKAGE_DIR)
        if not fname.startswith("_")
    ],
)


def test__prepare_default_plugins_cache(mocker):
    # plugins cache are prepared at initialization time
    prepare_default_plugins_cache_spy = mocker.spy(
        Plugins,
        "_prepare_default_plugins_cache",
    )
    add_plugin_to_cache_spy = mocker.spy(
        Plugins,
        "_add_plugin_to_cache",
    )
    extract_actions_from_plugin_module_spy = mocker.spy(
        Plugins,
        "_extract_actions_from_plugin_module",
    )

    # initialization plugins class
    plugins = Plugins()

    # preparation of plugins cache is called one time
    prepare_default_plugins_cache_spy.assert_called_once()
    assert prepare_default_plugins_cache_spy.spy_return is None

    # _add_plugin_to_cache is called for each default plugin
    assert add_plugin_to_cache_spy.call_count == NUMBER_OF_DEFAULT_PLUGINS
    assert len(plugins.plugin_names_loaders) == NUMBER_OF_DEFAULT_PLUGINS

    # actions names are cached
    assert len(plugins.actions_plugin_names) > NUMBER_OF_DEFAULT_PLUGINS
    assert (
        extract_actions_from_plugin_module_spy.call_count
        == len(set(plugins.actions_plugin_names.values()))
        == NUMBER_OF_DEFAULT_PLUGINS
    )


def test__prepare_default_plugins_cache_ignore_3rd_party_plugin(mocker):
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            importlib_metadata.EntryPoint(
                "foo-plugin",
                "foo_plugin",
                PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
            ),
            *importlib_metadata.entry_points(
                group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
            ),
        ],
    )
    add_plugin_to_cache_spy = mocker.spy(
        Plugins,
        "_add_plugin_to_cache",
    )
    extract_actions_from_plugin_module_spy = mocker.spy(
        Plugins,
        "_extract_actions_from_plugin_module",
    )

    Plugins()

    assert (
        add_plugin_to_cache_spy.call_count
        == extract_actions_from_plugin_module_spy.call_count
        == NUMBER_OF_DEFAULT_PLUGINS
    )


def test_prepare_3rd_party_plugin(mocker):
    plugin_that_overrides_default_plugin = importlib_metadata.EntryPoint(
        "inclusion",
        "custom_inclusion",
        PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    default_plugin_entrypoints = importlib_metadata.entry_points(
        group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            plugin_that_overrides_default_plugin,
            *default_plugin_entrypoints,
        ],
    )

    inclusion_plugin_entrypoint_index = None
    for index, entrypoint in enumerate(default_plugin_entrypoints):
        if entrypoint.name == "inclusion":
            inclusion_plugin_entrypoint_index = index
            break
    assert inclusion_plugin_entrypoint_index is not None

    add_plugin_to_cache_spy = mocker.spy(Plugins, "_add_plugin_to_cache")

    plugins = Plugins()

    # to avoid the next warning:
    #
    # DeprecationWarning: Accessing entry points by index is deprecated.
    # Cast to tuple if needed.
    default_plugin_entrypoints_tuple = tuple(
        default_plugin_entrypoints,
    )

    # assert that default plugins have been prepared
    for i in range(NUMBER_OF_DEFAULT_PLUGINS):
        _, args, _ = add_plugin_to_cache_spy.mock_calls[i]
        assert args[1].name == default_plugin_entrypoints_tuple[i].name
        assert args[1].value == default_plugin_entrypoints_tuple[i].value

    # prepare third party plugin that overrides default
    plugins.prepare_3rd_party_plugin(plugin_that_overrides_default_plugin)

    # assert that the 3rd party plugin cache has been prepared
    _, args, _ = add_plugin_to_cache_spy.mock_calls[NUMBER_OF_DEFAULT_PLUGINS]
    assert args[1].name == plugin_that_overrides_default_plugin.name
    assert args[1].value == plugin_that_overrides_default_plugin.value

    # assert that the 3rd party plugin takes precedence
    with pytest.raises(
        ModuleNotFoundError,
        match=(
            f"No module named '{plugin_that_overrides_default_plugin.module}'"
        ),
    ):
        plugins.plugin_names_loaders[
            default_plugin_entrypoints_tuple[
                inclusion_plugin_entrypoint_index
            ].name
        ]()


def test_get_function_for_action():
    plugins = Plugins()

    InclusionPlugin = tuple(
        importlib_metadata.entry_points(
            group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
            name="inclusion",
        ),
    )[0].load()

    # first time is not cached
    assert (
        plugins.get_function_for_action("includeLines")
        == InclusionPlugin.includeLines
    )

    # second time, the method is cached, is returned inmediatly
    assert (
        plugins.get_function_for_action("includeLines")
        == InclusionPlugin.includeLines
    )

    # call another action of the plugin, the class is cached but
    # not the method
    assert (
        plugins.get_function_for_action("ifIncludeLines")
        == InclusionPlugin.ifIncludeLines
    )


def test_invalid_plugin_function_type(mocker):
    """Assert error raised when plugin functions are not static methods."""
    foo_plugin = importlib_metadata.EntryPoint(
        "fake-plugin",
        "testing_helpers:FakePlugin",
        PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )

    default_plugin_entrypoints = importlib_metadata.entry_points(
        group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
    )
    mocker.patch(
        f"{importlib_metadata.__name__}.entry_points",
        return_value=[
            foo_plugin,
            *default_plugin_entrypoints,
        ],
    )

    plugins = Plugins()
    plugins.prepare_3rd_party_plugin("fake-plugin")

    with pytest.raises(
        InvalidPluginFunction,
        match=re.escape(
            "The method 'ifFoo' of the plugin 'fake-plugin'"
            f" (class '{FakePlugin.__name__}') must be a static method",
        ),
    ):
        plugins.get_function_for_action("ifFoo")

    assert plugins.get_function_for_action("ifBar") == FakePlugin.ifBar
    assert plugins.get_function_for_action("foo") == FakePlugin.foo

    with pytest.raises(
        InvalidPluginFunction,
        match=re.escape(
            "The method 'bar' of the plugin 'fake-plugin'"
            f" (class '{FakePlugin.__name__}') must be a static method",
        ),
    ):
        plugins.get_function_for_action("bar")
