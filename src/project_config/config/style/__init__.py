import typing as t
from dataclasses import dataclass

from project_config.config.exceptions import ProjectConfigInvalidConfigSchema
from project_config.config.style.fetchers import (
    fetch_style,
    resolve_maybe_relative_url,
)
from project_config.plugins import Plugins


@dataclass
class Style:
    config: type

    def __post_init__(self):
        self.plugins = Plugins()

        self._load_styles_or_raise_if_invalid()

    def __getitem__(self, key: str) -> t.Any:
        return self.config["style"].__getitem__(key)

    def _load_styles_or_raise_if_invalid(self):
        style_gen = self._load_styles()
        error_messages = []
        while True:
            try:
                style_or_error = next(style_gen)
            except StopIteration:
                break
            else:
                if isinstance(style_or_error, dict):
                    self.config["style"] = style_or_error
                else:
                    error_messages.append(style_or_error)
        if error_messages:
            raise ProjectConfigInvalidConfigSchema(
                self.config.path,
                error_messages,
            )

    def _load_styles(self) -> t.Iterator[t.Union[t.Dict[str, t.Any], str]]:
        """Load styles yielding error messages if found.

        Error messages are of type string and style is of type dict.
        If the first yielded value is a dict, we have a style without errors.
        """
        style_urls = self.config["style"]
        if isinstance(style_urls, str):
            style, error_message = fetch_style(style_urls)
            if error_message:
                yield f"style -> {error_message}"
            else:
                _partial_style_is_valid = True
                validator = self._validate_style_preparing_new_plugins(
                    style_urls,
                    style,
                )
                while True:
                    try:
                        yield next(validator)
                    except StopIteration:
                        break
                    else:
                        _partial_style_is_valid = False

                if _partial_style_is_valid and "extends" in style:
                    # extend the style
                    yield from self._extend_partial_style(style_urls, style)
        elif isinstance(style_urls, list):
            style = {"rules": [], "plugins": []}
            for s, partial_style_url in enumerate(style_urls):
                partial_style, error_message = fetch_style(partial_style_url)
                if error_message:
                    yield f"style[{s}] -> {error_message}"
                    continue

                # extend style only if it is valid
                _partial_style_is_valid = True
                validator = self._validate_style_preparing_new_plugins(
                    partial_style_url,
                    partial_style,
                )
                while True:
                    try:
                        yield next(validator)
                    except StopIteration:
                        break
                    else:
                        _partial_style_is_valid = False

                if _partial_style_is_valid:
                    if "extends" in partial_style:
                        yield from self._extend_partial_style(
                            partial_style_url, partial_style
                        )

                    self._add_new_rules_plugins_to_style(
                        style,
                        partial_style["rules"],
                        partial_style.get("plugins", []),
                    )
            yield style

    def _extend_partial_style(
        self, parent_style_url: str, style: t.Dict[str, t.List[str]]
    ):
        for s, extend_url in enumerate(style["extends"]):
            partial_style, error_message = fetch_style(extend_url)
            if error_message:
                yield f"{parent_style_url}: .extends[{s}] -> {error_message}"
                continue

            _partial_style_is_valid = True
            validator = self._validate_style_preparing_new_plugins(
                extend_url,
                partial_style,
            )
            while True:
                try:
                    yield next(validator)
                except StopIteration:
                    break
                else:
                    _partial_style_is_valid = False
            if _partial_style_is_valid:
                if "extends" in partial_style:
                    # extend the style recursively
                    yield from self._extend_partial_style(extend_url, partial_style)

                self._add_new_rules_plugins_to_style(
                    style,
                    partial_style["rules"],
                    partial_style.get("plugins", []),
                    prepend=True,
                )

        yield style

    def _add_new_rules_plugins_to_style(
        self,
        style: t.Dict[str, t.List[t.Any]],
        new_rules: t.List[t.Any],
        new_plugins: t.List[str],
        prepend: bool = False,
    ):
        if prepend:
            style["rules"] = new_rules + style["rules"]
            for plugin in new_plugins:
                if plugin not in style["plugins"]:
                    style["plugins"].insert(0, plugin)
        else:
            style["rules"].extend(new_rules)
            for plugin in new_plugins:
                if plugin not in style["plugins"]:
                    style["plugins"].append(plugin)

    def _validate_style_preparing_new_plugins(
        self,
        style_url: str,
        style: t.Any,
    ):
        # validate extends urls
        if "extends" in style:
            if not isinstance(style["extends"], list):
                yield f"{style_url}: .extends -> must be of type array"
            else:
                for u, url in enumerate(style["extends"]):
                    if not isinstance(url, str):
                        yield f"{style_url}: .extends[{u}] -> must be of type string"
                    elif not url:
                        yield f"{style_url}: .extends[{u}] -> must not be empty"
                    else:
                        # resolve "extends" url given the style url
                        style["extends"][u] = resolve_maybe_relative_url(url, style_url)

        # validate plugins data consistency
        if "plugins" in style:
            if not isinstance(style["plugins"], list):
                yield f"{style_url}: .plugins -> must be of type array"
            else:
                for p, plugin_name in enumerate(style["plugins"]):
                    if not isinstance(plugin_name, str):
                        yield f"{style_url}: .plugins[{p}] -> must be of type string"
                    elif not plugin_name:
                        yield f"{style_url}: .plugins[{p}] -> must not be empty"
                    else:
                        # cache plugins on demand
                        self.plugins.prepare_third_party_plugin(plugin_name)

        # validate rules
        if "rules" not in style:
            yield f"{style_url}: .rules -> is required"
        elif not isinstance(style["rules"], list):
            yield f"{style_url}: .rules -> must be of type array"
        elif not style["rules"]:
            yield f"{style_url}: .rules -> at least one rule is required"
        else:
            for r, rule in enumerate(style["rules"]):
                if "files" not in rule:
                    yield f"{style_url}: .rules[{r}].files -> is required"
                elif not isinstance(rule["files"], list):
                    yield f"{style_url}: .rules[{r}].files -> must be of type array"
                elif not rule["files"]:
                    yield f"{style_url}: .rules[{r}].files -> at least one file is required"

                else:
                    for f, file in enumerate(rule["files"]):
                        if not isinstance(file, str):
                            yield (
                                f"{style_url}: .rules[{r}].files[{f}] -> must be of type string"
                            )
                        elif not file:
                            yield (
                                f"{style_url}: .rules[{r}].files[{f}] -> must not be empty"
                            )

                # Validate rules properties consistency against plugins
                for verb in rule:
                    if verb == "files":
                        continue

                    # the action must be prepared
                    if not verb:
                        yield (
                            f"{style_url}: .rules[{r}].{verb}" " -> must not be empty"
                        )
                    elif not self.plugins.is_valid_verb(verb):
                        yield (
                            f"{style_url}: .rules[{r}].{verb}"
                            " -> invalid action, not found in"
                            " defined plugins:"
                            f" {', '.join(self.plugins.plugin_names)}"
                        )
