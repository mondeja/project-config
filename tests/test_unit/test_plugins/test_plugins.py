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
CONTRIB_PLUGINS_PACKAGE_DIR = os.path.join(
    PLUGINS_PACKAGE_DIR,
    "contrib",
)
NUMBER_OF_DEFAULT_PLUGINS = len(
    [
        fname
        for fname in os.listdir(PLUGINS_PACKAGE_DIR)
        if not fname.startswith("_")
        and not os.path.isdir(os.path.join(PLUGINS_PACKAGE_DIR, fname))
    ],
) + len(
    [
        fname
        for fname in os.listdir(CONTRIB_PLUGINS_PACKAGE_DIR)
        if not fname.startswith("_")
        and not os.path.isdir(os.path.join(CONTRIB_PLUGINS_PACKAGE_DIR, fname))
    ],
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
    )


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
