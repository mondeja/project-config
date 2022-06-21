"""Project-config built-in plugins.

These plugins are not required to be specified in ``plugins``
properties of styles.
"""

import importlib.util
import inspect
import re
import typing as t

from project_config.compat import TypeAlias, importlib_metadata
from project_config.exceptions import ProjectConfigException
from project_config.tree import Tree
from project_config.types import Results, Rule


PluginMethod: TypeAlias = t.Callable[[t.Any, Tree, Rule], Results]


class InvalidPluginFunction(ProjectConfigException):
    """Exception raised when a method of a plugin class is not valid."""


class Plugins:
    """Plugins wrapper.

    Performs all the logic concerning to plugins.

    Plugins modules are loaded on demand, only when an action
    specified by a rule requires it, and cached for later
    demanding from rules.
    """

    def __init__(self) -> None:
        # map from plugin names to loaded classes
        self.loaded_plugins: t.Dict[str, type] = {}

        # map from plugin names to plugin class loaders functions
        self.plugin_names_loaders: t.Dict[str, t.Callable[[], type]] = {}

        # map from actions to plugins names
        self.actions_plugin_names: t.Dict[str, str] = {}

        # map from actions to static methods
        self.actions_static_methods: t.Dict[str, PluginMethod] = {}

        # prepare default plugins cache, third party ones will be loaded
        # on demand at style validation time
        self._prepare_default_plugins_cache()

    @property
    def plugin_names_actions(self) -> t.Dict[str, t.List[str]]:
        """Map from plugin names to their allowed actions."""
        result: t.Dict[str, t.List[str]] = {}
        for action, plugin_name in self.actions_plugin_names.items():
            if plugin_name not in result:
                result[plugin_name] = []
            result[plugin_name].append(action)
        return result

    @property
    def plugin_names(self) -> t.List[str]:
        """List of available plugin names."""
        return list(self.plugin_names_loaders)

    @property
    def loaded_plugin_names(self) -> t.List[str]:
        """List of loaded plugin names."""
        return list(self.loaded_plugin_names)

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
            group="project_config.plugins",
        ):
            if not plugin.value.startswith("project_config.plugins."):
                continue

            self._add_plugin_to_cache(plugin)

    def prepare_third_party_plugin(self, plugin_name: str) -> None:
        """Prepare cache for third party plugins.

        After that a plugin has been prepared can be load on demand.

        Args:
            plugin_name (str): Name of the entry point of the plugin.
        """
        for plugin in importlib_metadata.entry_points(
            group="project_config.plugins",
            name=plugin_name,
        ):
            # Allow third party plugins to avorride default plugins
            if plugin.value.startswith("project_config.plugins."):
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
    ) -> t.Iterator[str]:
        # TODO: raise error is the specification is not found
        #   this could happen if an user as defined an entrypoint
        #   pointing to a non existent module
        module_spec = importlib.util.find_spec(module_dotpath)
        if module_spec is not None:
            module_path = module_spec.origin
            if module_path is not None:
                with open(module_path) as f:
                    for match in re.finditer(r"def ([^_]\w+)\(", f.read()):
                        yield match.group(1)
            # else:  # TODO: this could even happen? raise error
