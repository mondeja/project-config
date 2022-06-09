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
    def __init__(self):
        # map from plugin names to loaded classes
        self.loaded_plugins: t.Dict[str, type] = {}

        # map from plugin names to plugin class loaders functions
        self.plugin_names_loaders: t.Dict[str, t.Callable[[], type]] = {}

        # map from verbs to plugins names
        self.verbs_plugin_names: t.Dict[str, str] = {}
        # TODO: how to handle conditionals?

        # prepare default plugins cache, third party ones will be loaded
        # on demand at style validation time
        self._prepare_default_plugins_cache()
    
    @property
    def plugin_names_verbs(self) -> t.Dict[str, t.List[str]]:
        """Map from plugin names to their allowed verbs."""
        result = {}
        for verb, plugin_name in self.verbs_plugin_names.items():
            if plugin_name not in result:
                result[plugin_name] = []
            result[plugin_name].append(verb)
        return result
    
    @property
    def plugin_names(self) -> t.List[str]:
        return list(self.plugin_names_loaders)
    
    @property
    def loaded_plugin_names(self) -> t.List[str]:
        return list(self.loaded_plugin_names)

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

    def _prepare_default_plugins_cache(self) -> None:
        for plugin in importlib_metadata.entry_points(group="project-config.plugins"):
            if not plugin.value.startswith("project_config.plugins."):
                continue
            
            self._add_plugin_to_cache(plugin)
    
    def prepare_third_party_plugin(self, plugin_name: str) -> None:
        for plugin in importlib_metadata.entry_points(group="project-config.plugins", name=plugin_name):
            # Allow third party plugins to avorride default plugins
            if plugin.value.startswith("project_config.plugins."):
                continue
        
            self._add_plugin_to_cache(plugin)
    
    def _add_plugin_to_cache(self, plugin: importlib_metadata.EntryPoint) -> None:
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

    def is_valid_verb(self, verb: str) -> bool:
        """Return if a verb is prepared."""
        return verb in self.verbs_plugin_names
    
    