import typing as t

from project_config.config.exceptions import ProjectConfigInvalidConfigSchema
from project_config.config.style.fetchers import fetch_style


def validate_style_plugins(style_path: str, style: t.Any) -> t.List[str]:
    # TODO: validate plugins
    error_messages: t.List[str] = []

    return error_messages


def validate_style_rules(style_path: str, style: t.Any) -> t.List[str]:
    error_messages = []
    if "rules" not in style:
        error_messages.append(f"{style_path}.rules -> is required")
    elif not isinstance(style["rules"], list):
        error_messages.append(f"{style_path}.rules -> must be of type array")
    elif not style["rules"]:
        error_messages.append(f"{style_path}.rules -> at least one rule is required")
    else:
        for r, rule in enumerate(style["rules"]):
            if "files" not in rule:
                error_messages.append(f"{style_path}.rules[{r}].files -> is required")
            elif not isinstance(rule["files"], list):
                error_messages.append(
                    f"{style_path}.rules[{r}].files -> must be of type array"
                )
            elif not rule["files"]:
                error_messages.append(
                    f"{style_path}.rules[{r}].files -> at least one file is required"
                )
            else:
                for f, file in enumerate(rule["files"]):
                    if not isinstance(file, str):
                        error_messages.append(
                            f"{style_path}.rules[{r}].files[{f}] -> must be of type string"
                        )
                    elif not file:
                        error_messages.append(
                            f"{style_path}.rules[{r}].files[{f}] -> must not be empty"
                        )
            # TODO: validate rules properties consistency against plugins.
            #   This needs the passing of the plugins object and the reading
            #   of plugin verbs at style validation time.
    return error_messages


def validate_style(style_path: str, style: t.Any) -> t.List[str]:
    error_messages = [
        *validate_style_rules(style_path, style),
        *validate_style_plugins(style_path, style),
    ]

    return error_messages


def get_style(config_path: str, config_style: t.Union[str, t.List[str]]) -> t.Any:
    error_messages = []
    if isinstance(config_style, str):
        style, error_message = fetch_style(config_style)
        if error_message:
            error_messages.append(f"style -> {error_message}")
        error_messages.extend(validate_style(config_style, style))
    else:
        style = {"rules": [], "plugins": []}
        # TODO: extend styles with nested styles ("extend" property)
        for s, partial_style_uri in enumerate(config_style):
            partial_style, error_message = fetch_style(partial_style_uri)
            if error_message:
                error_messages.append(f"style[{s}] -> {error_message}")
                continue

            error_messages.extend(
                validate_style(partial_style_uri, partial_style),
            )

            # extend style
            style["rules"].extend(partial_style["rules"])
            for plugin in partial_style.get("plugins", []):
                if plugin not in style["plugins"]:
                    style["plugins"].append(plugin)
    if error_messages:
        raise ProjectConfigInvalidConfigSchema(
            config_path,
            error_messages,
        )
    return style
