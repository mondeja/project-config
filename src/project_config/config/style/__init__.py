"""Style loader, blender and checker."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from project_config import tree
from project_config.cache import Cache
from project_config.config.exceptions import ProjectConfigInvalidConfigSchema
from project_config.fetchers import resolve_maybe_relative_url, resolve_url
from project_config.plugins import Plugins
from project_config.serializers import serialize_for_url


class ProjectConfigInvalidStyle(ProjectConfigInvalidConfigSchema):
    """Invalid style error."""


if TYPE_CHECKING:
    from project_config.compat import NotRequired, TypeAlias, TypedDict
    from project_config.config import ConfigType
    from project_config.types import Rule

    class StyleType(TypedDict):
        """Style type."""

        rules: NotRequired[list[Rule]]
        plugins: NotRequired[list[str]]
        extends: NotRequired[list[str]]

    PluginType: TypeAlias = type
    StyleLoaderIterator: TypeAlias = Iterator[StyleType | str]


class Style:
    """Wrapper for style loader, blender and checker.

    Args:
        config (dict): Configuration for the project.
    """

    def __init__(self, config: Any) -> None:
        self.plugins = Plugins()
        self.config = config

    @classmethod
    def from_config(cls, config: Any) -> Style:
        """Loads styles to the configuration passed as argument."""
        if (  # pragma: no cover
            isinstance(config.dict_["style"], str)
            and not os.path.isfile(config.dict_["style"])
        ) or (
            isinstance(config.dict_["style"], list)
            and not all(
                [os.path.isfile(url) for url in config.dict_["style"]],
            )
        ):
            try:
                _prefetch_urls(config)
            except Exception:
                # if an exception is raised, will be raised again
                # in the synchronous style loader
                pass

        style = cls(config)

        style_gen = style._load_styles_from_config()
        error_messages: list[str] = []
        while True:
            try:
                style_or_error = next(style_gen)
            except StopIteration:
                break
            else:
                if isinstance(style_or_error, dict):
                    # final style collected
                    style.config.dict_["style"] = style_or_error
                else:
                    error_messages.append(style_or_error)
        if error_messages:
            raise ProjectConfigInvalidStyle(style.config.path, error_messages)

        return style

    def _load_styles_from_config(self) -> StyleLoaderIterator:
        """Load styles yielding error messages if found.

        Error messages are of type string and style is of type dict.
        If the first yielded value is a dict, we have a style without errors.
        """
        self.config.dict_["_style"] = self.config.dict_["style"]
        style_urls = self.config.dict_["style"]
        if isinstance(style_urls, str):
            try:
                style = tree.fetch_remote_file(style_urls)
            except FileNotFoundError:
                yield f"style -> '{style_urls}' file not found"
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
                        yield from self._extend_partial_style(
                            style_urls,
                            style,
                        )
                    yield style
        elif isinstance(style_urls, list):
            style = {"rules": [], "plugins": []}
            for s, partial_style_url in enumerate(style_urls):
                try:
                    partial_style = tree.fetch_remote_file(partial_style_url)
                except FileNotFoundError:
                    yield f"style[{s}] -> '{partial_style_url}' file not found"
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
    ) -> StyleLoaderIterator:
        for s, extend_url in enumerate(style.pop("extends", [])):
            try:
                partial_style = tree.fetch_remote_file(extend_url)
            except FileNotFoundError:
                yield (
                    f"{parent_style_url}: .extends[{s}]"
                    f" -> '{extend_url}' file not found"
                )
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
                else:  # pragma: no cover
                    # NOTE: this is marked as not covered, but putting a
                    # `print` statement here it can be seen that the
                    # `else` branch is reached, so probably it is a bug
                    # in coverage.py
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
                    partial_style.get("rules", []),
                    partial_style.get("plugins", []),
                    prepend=True,
                )

        yield style

    def _add_new_rules_plugins_to_style(
        self,
        style: StyleType,
        new_rules: list[Rule],
        new_plugins: list[str],
        prepend: bool = False,
    ) -> None:
        style["plugins"] = style.pop("plugins", [])
        style["rules"] = style.pop("rules", [])
        if prepend:
            style["rules"] = new_rules + style["rules"]
            style["plugins"] = list(set(new_plugins + style["plugins"]))
        else:
            style["rules"].extend(new_rules)
            style["plugins"] = list(set(style["plugins"] + new_plugins))

    def _validate_style_preparing_new_plugins(
        self,
        style_url: str,
        style: Any,
    ) -> Iterator[str]:

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
                            self.config.dict_["cli"]["rootdir"],
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
                        self.plugins.prepare_3rd_party_plugin(plugin_name)

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
                        elif not isinstance(
                            rule["files"]["not"],
                            (dict, list),
                        ):
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
                                for f, fpath in enumerate(
                                    rule["files"]["not"],
                                ):
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
                        if len(rule) != 1 and not (
                            len(rule) == 2 and "hint" in rule
                        ):
                            yield (
                                f"{style_url}: .rules[{r}] -> when"
                                " requiring absence of files with"
                                " '.files.not', no other actions can"
                                " be used in the same rule"
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
                    if action in ["files", "hint"]:
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


def _prefetch_urls(config_dict: ConfigType) -> None:
    """Prefetch urls concurrently and store them in cache.

    This function is used to store urls in cache before they are used,
    so the network calls are speedup a lot.

    Args:
        config_dict: The config_dict object.
    """
    from concurrent.futures import as_completed

    from requests_futures.sessions import FuturesSession

    session = FuturesSession()

    style_urls_ = config_dict["style"]
    if isinstance(style_urls_, str):
        style_urls_ = [style_urls_]

    def prefetch_partial_style(
        parent_style_url: str,
        extend_urls: list[str],
    ) -> None:
        urls = {}
        for extend_url in extend_urls:
            resolved_extend_url = resolve_maybe_relative_url(
                extend_url,
                parent_style_url,
                config_dict["cli"]["rootdir"],
            )
            url, _ = resolve_url(resolved_extend_url)
            if Cache.get(url) is not None:
                continue
            urls[url] = resolved_extend_url
        if not urls:
            return

        futures = [session.get(url) for url in urls]

        for future in as_completed(futures):
            resp = future.result()
            Cache.set(resp.url, resp.text)
            style_obj = serialize_for_url(resp.url, resp.text)
            if isinstance(style_obj.get("extends"), list):
                prefetch_partial_style(urls[resp.url], style_obj["extends"])

    def prefetch_style(style_urls: StyleType) -> None:
        urls = {}
        for style_url in style_urls:
            url, scheme = resolve_url(style_url)
            if scheme == "file" or Cache.get(url) is not None:
                continue
            urls[url] = style_url
        if not urls:
            return

        futures = [session.get(url) for url in urls]

        for future in as_completed(futures):
            resp = future.result()
            Cache.set(resp.url, resp.text)
            style_obj = serialize_for_url(resp.url, resp.text)
            if isinstance(style_obj.get("extends"), list):
                prefetch_partial_style(urls[resp.url], style_obj["extends"])

    prefetch_style(style_urls_)
