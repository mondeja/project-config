"""Project-config built-in plugins.

These plugins are not required to be specified in ``plugins``
properties of styles.
"""

from __future__ import annotations

import importlib.util
import inspect
import re
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

from project_config.compat import importlib_metadata
from project_config.exceptions import ProjectConfigException
from project_config.types import ActionsContext


PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP = "project_config.plugins"

if TYPE_CHECKING:
    from project_config.compat import TypeAlias
    from project_config.types import Results, Rule

    PluginMethod: TypeAlias = Callable[
        [Any, Rule, ActionsContext | None],
        Results,
    ]


class InvalidPluginFunction(ProjectConfigException):
    """Exception raised when a method of a plugin class is not valid."""


class Plugins:
    """Plugins wrapper.

    Performs all the logic concerning to plugins.

    Plugins modules are loaded on demand, only when an action
    specified by a rule requires it, and cached for later
    demanding from rules.
    """

    def __init__(self, prepare_all: bool = False) -> None:
        # map from plugin names to loaded classes
        self.loaded_plugins: dict[str, type] = {}

        # map from plugin names to plugin class loaders functions
        self.plugin_names_loaders: dict[str, Callable[[], type]] = {}

        # map from actions to plugins names
        self.actions_plugin_names: dict[str, str] = {}

        # map from actions to static methods
        self.actions_static_methods: dict[str, PluginMethod] = {}

        if prepare_all:
            # prepare all plugins cache, default and third party,
            # useful in tasks like plugins listing
            self._prepare_all_plugins_cache()
        else:
            # prepare default plugins cache, third party ones will be loaded
            # on demand at style validation time
            self._prepare_default_plugins_cache()

    @property
    def plugin_names(self) -> list[str]:
        """Available plugin names."""
        return list(self.plugin_names_loaders)

    @property
    def plugin_action_names(self) -> dict[str, list[str]]:
        """Mapping of plugin names to their actions."""
        plugins_actions: dict[str, list[str]] = {}
        for action_name, plugin_name in self.actions_plugin_names.items():
            if plugin_name not in plugins_actions:
                plugins_actions[plugin_name] = []
            if action_name.startswith("if"):
                plugins_actions[plugin_name].append(action_name)
            else:
                plugins_actions[plugin_name].insert(0, action_name)
        return plugins_actions

    def get_function_for_action(
        self,
        action: str,
    ) -> PluginMethod:
        """Get the function that performs an action given her name.

        Args:
            action (str): Action name whose function will be returned.

        Returns:
            type: Function that process the action.
        """
        if action not in self.actions_static_methods:
            plugin_name = self.actions_plugin_names[action]
            if plugin_name not in self.loaded_plugins:
                load_plugin = self.plugin_names_loaders[plugin_name]
                plugin_class = load_plugin()
                self.loaded_plugins[plugin_name] = plugin_class
            else:
                plugin_class = self.loaded_plugins[plugin_name]
            method = getattr(plugin_class, action)

            # the actions in plugins must be defined as static methods
            # to not compromise performance
            #
            # this check is realized just one time for each action
            # thanks to the cache
            if not isinstance(
                inspect.getattr_static(plugin_class, action),
                staticmethod,
            ):
                raise InvalidPluginFunction(
                    f"The method '{action}' of the plugin '{plugin_name}'"
                    f" (class '{plugin_class.__name__}') must be a static"
                    " method",
                )
            self.actions_static_methods[action] = method
        else:
            method = self.actions_static_methods[action]

        return method  # type: ignore

    def is_valid_action(self, action: str) -> bool:
        """Return if an action exists in available plugins.

        Args:
            action (str): Action to check for their existence.

        Returns:
            bool: ``True`` if the action exists, ``False`` otherwise.
        """
        return action in self.actions_plugin_names

    def _prepare_default_plugins_cache(self) -> None:
        for plugin in importlib_metadata.entry_points(
            group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
        ):
            if not plugin.value.startswith(
                f"{PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP}.",
            ):
                continue

            self._add_plugin_to_cache(plugin)

    def _prepare_all_plugins_cache(self) -> None:
        for plugin in importlib_metadata.entry_points(
            group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
        ):
            self._add_plugin_to_cache(plugin)

    def prepare_3rd_party_plugin(self, plugin_name: str) -> None:
        """Prepare cache for third party plugins.

        After that a plugin has been prepared can be load on demand.

        Args:
            plugin_name (str): Name of the entry point of the plugin.
        """
        for plugin in importlib_metadata.entry_points(
            group=PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP,
            name=plugin_name,
        ):
            # Allow third party plugins to override default plugins
            if plugin.value.startswith(
                f"{PROJECT_CONFIG_PLUGINS_ENTRYPOINTS_GROUP}.",
            ):
                continue

            self._add_plugin_to_cache(plugin)

    def _add_plugin_to_cache(
        self,
        plugin: importlib_metadata.EntryPoint,
    ) -> None:
        # do not load plugin until any action is called
        # instead just save in cache and will be loaded on demand
        self.plugin_names_loaders[plugin.name] = plugin.load

        for action in self._extract_actions_from_plugin_module(plugin.module):
            if action not in self.actions_plugin_names:
                self.actions_plugin_names[action] = plugin.name

    def _extract_actions_from_plugin_module(
        self,
        module_dotpath: str,
    ) -> Iterator[str]:
        # TODO: raise error is the specification is not found
        #   this could happen if an user as defined an entrypoint
        #   pointing to a non existent module
        module_spec = importlib.util.find_spec(module_dotpath)
        if module_spec is not None:
            module_path = module_spec.origin
            if module_path is not None:
                with open(module_path, encoding="utf-8") as f:
                    for match in re.finditer(r"def ([^_]\w+)\(", f.read()):
                        yield match.group(1)
            # else:  # TODO: this could even happen? raise error
