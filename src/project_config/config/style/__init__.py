"""Style loader, blender and checker."""

import typing as t

from project_config.config.exceptions import ProjectConfigInvalidConfigSchema
from project_config.fetchers import (
    FetchError,
    fetch,
    resolve_maybe_relative_url,
)
from project_config.plugins import Plugins
from project_config.types import Rule


class ProjectConfigInvalidStyle(ProjectConfigInvalidConfigSchema):
    """Invalid style error."""


PluginType = type
# TODO: improve style type with TypedDict?
# https://docs.python.org/3/library/typing.html#typing.TypedDict
StyleType = t.Dict[str, t.List[t.Any]]
StyleLoderIterator = t.Iterator[t.Union[StyleType, str]]


class Style:
    """Wrapper for style loader, blender and checker.

    Args:
        config (dict): Configuration for the project.
    """

    def __init__(self) -> None:
        self.plugins = Plugins()

    @classmethod
    def from_config(cls, config: t.Any) -> "Style":
        """Loads styles to the configuration passed as argument."""
        style = cls()

        style_gen = style._load_styles_from_config(config)
        error_messages: t.List[str] = []
        while True:
            try:
                style_or_error = next(style_gen)
            except StopIteration:
                break
            else:
                if isinstance(style_or_error, dict):
                    # after collecting the full style, at least one rule
                    # must be defined, otherwise raise an error
                    if not style_or_error.get("rules", []):
                        if (
                            not error_messages
                        ):  # don't repeat errors, is confusing
                            error_messages.append(
                                "[styles]: .rules -> must not be empty"
                                " after extending styles",
                            )
                        break
                    else:
                        config["style"] = style_or_error
                else:
                    error_messages.append(style_or_error)
        if error_messages:
            raise ProjectConfigInvalidStyle(config.path, error_messages)

        return style

    def _load_styles_from_config(self, config: t.Any) -> StyleLoderIterator:
        """Load styles yielding error messages if found.

        Error messages are of type string and style is of type dict.
        If the first yielded value is a dict, we have a style without errors.
        """
        config["_style"] = config["style"]
        style_urls = config["style"]
        if isinstance(style_urls, str):
            try:
                style = fetch(style_urls)
            except FetchError as exc:
                yield f"style -> {exc.message}"
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

                if _partial_style_is_valid:
                    if "extends" in style:
                        # extend the style
                        yield from self._extend_partial_style(style_urls, style)
                    yield style
        elif isinstance(style_urls, list):
            style = {"rules": [], "plugins": []}
            for s, partial_style_url in enumerate(style_urls):
                try:
                    partial_style = fetch(partial_style_url)
                except FetchError as exc:
                    yield f"style[{s}] -> {exc.message}"
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
                            partial_style_url,
                            partial_style,
                        )

                    self._add_new_rules_plugins_to_style(
                        style,
                        partial_style.get("rules", []),
                        partial_style.get("plugins", []),
                    )
            yield style

    def _extend_partial_style(
        self,
        parent_style_url: str,
        style: StyleType,
    ) -> StyleLoderIterator:
        for s, extend_url in enumerate(style.pop("extends")):
            try:
                partial_style = fetch(extend_url)
            except FetchError as exc:
                yield f"{parent_style_url}: .extends[{s}] -> {exc.message}"
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
                    yield from self._extend_partial_style(
                        extend_url,
                        partial_style,
                    )

                self._add_new_rules_plugins_to_style(
                    style,
                    partial_style["rules"],
                    partial_style.get("plugins", []),
                    prepend=True,
                )

        yield style

    def _add_new_rules_plugins_to_style(
        self,
        style: StyleType,
        new_rules: t.List[Rule],
        new_plugins: t.List[PluginType],
        prepend: bool = False,
    ) -> None:
        style["plugins"] = style.pop("plugins", [])
        style["rules"] = style.pop("rules", [])
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
    ) -> t.Iterator[str]:

        # validate extends urls
        if "extends" in style:
            if not isinstance(style["extends"], list):
                yield f"{style_url}: .extends -> must be of type array"
            elif not style["extends"]:
                yield f"{style_url}: .extends -> must not be empty"
            else:
                for u, url in enumerate(style["extends"]):
                    if not isinstance(url, str):
                        yield (
                            f"{style_url}: .extends[{u}] -> must be of"
                            " type string"
                        )
                    elif not url:
                        yield f"{style_url}: .extends[{u}] -> must not be empty"
                    else:
                        # resolve "extends" url given the style url
                        style["extends"][u] = resolve_maybe_relative_url(
                            url,
                            style_url,
                        )

        # validate plugins data consistency
        if "plugins" in style:
            if not isinstance(style["plugins"], list):
                yield f"{style_url}: .plugins -> must be of type array"
            elif not style["plugins"]:
                yield f"{style_url}: .plugins -> must not be empty"
            else:
                for p, plugin_name in enumerate(style["plugins"]):
                    if not isinstance(plugin_name, str):
                        yield (
                            f"{style_url}: .plugins[{p}]"
                            " -> must be of type string"
                        )
                    elif not plugin_name:
                        yield f"{style_url}: .plugins[{p}] -> must not be empty"
                    else:
                        # cache plugins on demand
                        self.plugins.prepare_third_party_plugin(plugin_name)

        # validate rules
        if "rules" not in style:
            if "extends" not in style:
                yield (
                    f"{style_url}: .rules or .extends"
                    " -> one of both is required"
                )
        elif not isinstance(style["rules"], list):
            yield f"{style_url}: .rules -> must be of type array"
        elif not style["rules"]:
            yield f"{style_url}: .rules -> at least one rule is required"
        else:
            for r, rule in enumerate(style["rules"]):
                if not isinstance(rule, dict):
                    yield f"{style_url}: .rules[{r}] -> must be of type object"
                    continue
                elif "files" not in rule:
                    yield f"{style_url}: .rules[{r}].files -> is required"
                elif not isinstance(rule["files"], (list, dict)):
                    yield (
                        f"{style_url}: .rules[{r}].files -> must be"
                        " of type array or object"
                    )
                elif not rule["files"]:
                    yield (
                        f"{style_url}: .rules[{r}].files -> at least"
                        " one file is required"
                    )
                else:
                    if isinstance(rule["files"], dict):
                        # requiring absence of files with
                        # `files: {not: {<file>: reason}}`
                        if (
                            len(rule["files"]) != 1
                            or "not" not in rule["files"].keys()
                        ):
                            yield (
                                f"{style_url}: .rules[{r}].files"
                                " -> when files is an object, must"
                                " have one 'not' key"
                            )
                        elif not isinstance(rule["files"]["not"], (dict, list)):
                            yield (
                                f"{style_url}: .rules[{r}].files.not"
                                " -> must be of type array or object"
                            )
                        elif not rule["files"]["not"]:
                            yield (
                                f"{style_url}: .rules[{r}].files.not"
                                " -> must not be empty"
                            )
                        else:
                            if isinstance(rule["files"]["not"], dict):
                                # when 'not' is an object, is a mapping
                                # from files to absence reasons
                                for fpath, reason in rule["files"][
                                    "not"
                                ].items():
                                    if reason and not isinstance(reason, str):
                                        yield (
                                            f"{style_url}: .rules[{r}].files"
                                            f".not.{fpath} -> must be of type"
                                            " string"
                                        )
                                    if not isinstance(fpath, str):
                                        yield (
                                            f"{style_url}: .rules[{r}].files"
                                            f".not[{fpath}] -> file path must"
                                            " be of type string"
                                        )
                                    elif not fpath:
                                        yield (
                                            f"{style_url}: .rules[{r}].files"
                                            f".not[''] -> file path must"
                                            " not be empty"
                                        )
                            else:
                                for f, fpath in enumerate(rule["files"]["not"]):
                                    if not isinstance(fpath, str):
                                        yield (
                                            f"{style_url}: .rules[{r}].files"
                                            f".not[{f}] -> must be of type"
                                            " string"
                                        )
                                    elif not fpath:
                                        yield (
                                            f"{style_url}: .rules[{r}].files"
                                            f".not[{f}] -> must not be empty"
                                        )

                        # when requiring absence of files,
                        # no other action can be used
                        if len(rule) != 1:
                            yield (
                                f"{style_url}: .rules[{r}] -> when requiring"
                                " absence of files with '.files.not', any"
                                " other action can be used in the same rule"
                            )
                    else:
                        for f, file in enumerate(rule["files"]):
                            if not isinstance(file, str):
                                yield (
                                    f"{style_url}: .rules[{r}].files[{f}]"
                                    " -> must be of type string"
                                )
                            elif not file:
                                yield (
                                    f"{style_url}: .rules[{r}].files[{f}]"
                                    " -> must not be empty"
                                )

                # Validate rules properties consistency against plugins
                for action in rule:
                    if action == "files":
                        continue

                    # the action must be prepared
                    if not action:
                        yield (
                            f"{style_url}: .rules[{r}].''"
                            " -> action must not be empty"
                        )
                    elif not self.plugins.is_valid_action(action):
                        yield (
                            f"{style_url}: .rules[{r}].{action}"
                            " -> invalid action, not found in"
                            " defined plugins:"
                            f" {', '.join(self.plugins.plugin_names)}"
                        )
