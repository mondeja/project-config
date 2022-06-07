"""Project-config built-in plugins.

These plugins are not required to be specified in ``plugins``
properties of styles.
"""

import typing as t


try:
    import importlib.metadata as importlib_metadata
except ImportError:  # Python 3.7
    import importlib_metadata


def get_plugins(
    plugin_names: t.List[str] = [],
) -> t.Dict[str, importlib_metadata.EntryPoint]:
    """Return a dict of all installed Plugins as {name: EntryPoint}."""

    plugins = importlib_metadata.entry_points(group="project-config.plugins")

    pluginmap = {}
    for plugin in plugins:
        # Filter plugins always loading built-in ones
        if (
            not plugin.value.startswith("project_config.plugins.")
            and plugin.name not in plugin_names
        ):
            continue

        # Allow third-party plugins to override core plugins
        if plugin.name in pluginmap and plugin.value.startswith(
            "project_config.plugins."
        ):
            continue

        pluginmap[plugin.name] = plugin

    return pluginmap
