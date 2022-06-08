"""Project-config built-in plugins.

These plugins are not required to be specified in ``plugins``
properties of styles.
"""

import functools
import importlib.util
import re
import typing as t


try:
    import importlib.metadata as importlib_metadata
except ImportError:  # Python 3.7
    import importlib_metadata


class Plugins:
    def __init__(self, possible_plugin_names: t.List[str]):
        # map from plugin names to loaded classes
        self.loaded_plugins: t.Dict[str, type] = {}

        # map from plugin names to plugin class loaders functions
        self.plugin_names_loaders: t.Dict[str, t.Callable[[], type]] = {}

        # map from verbs to plugins names
        self.verbs_plugin_names: t.Dict[str, str] = {}
        # TODO: how to handle conditionals?

        # prepare plugins cache
        self._prepare_plugins_cache(possible_plugin_names)

    @functools.lru_cache(maxsize=None)
    def get_method_for_verb(self, verb: str) -> t.Any:  # TODO: improve this type
        plugin_name = self.verbs_plugin_names[verb]
        if plugin_name not in self.loaded_plugins:
            load_plugin = self.plugin_names_loaders[plugin_name]
            plugin_class = load_plugin()
            self.loaded_plugins[plugin_name] = plugin_class
        else:
            plugin_class = self.loaded_plugins[plugin_name]
        return getattr(plugin_class, f"verb_{verb}")

    def _prepare_plugins_cache(self, possible_plugin_names: t.List[str]) -> None:
        # NOTE: possible_plugin_names must be a list qith unique items

        plugins = importlib_metadata.entry_points(group="project-config.plugins")

        processed_plugins: t.List[str] = []
        for plugin in plugins:
            # Filter plugins always loading built-in ones
            if (
                not plugin.value.startswith("project_config.plugins.")
                and plugin.name not in possible_plugin_names
            ):
                processed_plugins.append(plugin.name)
                continue

            # Allow third-party plugins to override core plugins
            if plugin.name in processed_plugins and plugin.value.startswith(
                "project_config.plugins."
            ):
                continue

            # do not load plugin until any verb is called
            # instead just save in cache and will be loaded on demand
            self.plugin_names_loaders[plugin.name] = plugin.load

            for verb in self._extract_verbs_from_plugin_module(plugin.module):
                if verb not in self.verbs_plugin_names:
                    self.verbs_plugin_names[verb] = plugin.name

    def _extract_verbs_from_plugin_module(self, module_dotpath: str) -> t.Iterator[str]:
        # TODO: raise error is the specification is not found
        #   this could happen if an user as defined an entrypoint
        #   pointing to a non existent module
        module_spec = importlib.util.find_spec(module_dotpath)
        if module_spec is not None:
            module_path = module_spec.origin
            if module_path is not None:
                with open(module_path) as f:
                    for match in re.finditer(r"def verb_(\w+)\(", f.read()):
                        yield match.group(1)
            # else:  # TODO: this could even happen? raise error


'''

def get_plugins(plugin_names: t.List[str] = []) -> t.Iterator[type]:
    """Return a dict of all installed Plugins as {name: EntryPoint}."""

    plugins = importlib_metadata.entry_points(group="project-config.plugins")

    processed_plugins: t.List[str] = []
    for plugin in plugins:
        # Filter plugins always loading built-in ones
        if (
            not plugin.value.startswith("project_config.plugins.")
            and plugin.name not in plugin_names
        ):
            processed_plugins.append(plugin.name)
            continue

        # Allow third-party plugins to override core plugins
        if plugin.name in processed_plugins and plugin.value.startswith(
            "project_config.plugins."
        ):
            continue

        yield plugin.load()


def get_plugin_verbs(plugin: type) -> t.Iterator[t.Tuple[str, str]]:
    for method_name in plugin.__dict__.keys():
        if method_name.startswith("_"):
            continue
        if method_name.startswith("verb_"):
            yield method_name.split("_")[1], method_name
'''
