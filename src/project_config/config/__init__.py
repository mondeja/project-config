import os
import re
import typing as t
from dataclasses import dataclass

import tomlkit

from project_config.config.exceptions import (
    ConfigurationFilesNotFound,
    CustomConfigFileNotFound,
    ProjectConfigInvalidConfigSchema,
    PyprojectTomlFoundButHasNoConfig,
)
from project_config.config.style import Style


CONFIG_CACHE_REGEX = r"^(\d+ (minutes?)|(hours?)|(days?)|(weeks?))|(never)$"


def read_toml_file(fpath: str) -> tomlkit.toml_document.TOMLDocument:
    with open(fpath, "rb") as f:
        return tomlkit.load(f)


def read_config_from_pyproject_toml() -> t.Optional[t.Any]:
    pyproject_toml = read_toml_file("pyproject.toml")
    if "tool" in pyproject_toml and "project-config" in pyproject_toml["tool"]:
        return pyproject_toml["tool"]["project-config"]
    return None


def read_config(custom_file_path: t.Optional[str] = None) -> t.Tuple[str, t.Any]:
    if custom_file_path:
        if not os.path.isfile(custom_file_path):
            raise CustomConfigFileNotFound(custom_file_path)
        return custom_file_path, read_toml_file(custom_file_path)

    pyproject_toml_exists = os.path.isfile("pyproject.toml")
    config = None
    if pyproject_toml_exists:
        config = read_config_from_pyproject_toml()
    if config is not None:
        return '"pyproject.toml".[tool.project-config]', config

    project_config_toml_exists = os.path.isfile(".project-config.toml")
    if project_config_toml_exists:
        return ".project-config.toml", read_toml_file(".project-config.toml")

    if pyproject_toml_exists:
        raise PyprojectTomlFoundButHasNoConfig()
    raise ConfigurationFilesNotFound()


def validate_config_style(config: t.Any) -> t.List[str]:
    error_messages = []
    if "style" not in config:
        error_messages.append("style -> at least one is required")
    elif not isinstance(config["style"], (str, list)):
        error_messages.append("style -> must be of type string or array")
    elif isinstance(config["style"], list):
        if not config["style"]:
            error_messages.append("style -> at least one is required")
        else:
            for i, style in enumerate(config["style"]):
                if not isinstance(style, str):
                    error_messages.append(f"style[{i}] -> must be of type string")
                elif not style:
                    error_messages.append(f"style[{i}] -> must not be empty")
    elif not config["style"]:
        error_messages.append("style -> must not be empty")
    return error_messages


def validate_config_cache(config: t.Any) -> t.List[str]:
    error_messages = []
    if "cache" in config:
        if not isinstance(config["cache"], str):
            error_messages.append("cache -> must be of type string")
        elif not config["cache"]:
            error_messages.append("cache -> must not be empty")
        elif not re.match(CONFIG_CACHE_REGEX, config["cache"]):
            error_messages.append(f"cache -> must match the regex {CONFIG_CACHE_REGEX}")
    return error_messages


def validate_config(config_path: str, config: t.Any) -> None:
    error_messages = [*validate_config_style(config), *validate_config_cache(config)]

    if error_messages:
        raise ProjectConfigInvalidConfigSchema(
            config_path,
            error_messages,
        )


@dataclass
class Config:
    path: t.Optional[str]

    def __post_init__(self) -> None:
        self.path, config = read_config(self.path)
        validate_config(self.path, config)
        self.dict_: t.Dict[str, t.Union[str, t.List[str]]] = config
        self.style = Style(self)

    def __getitem__(self, key: str) -> t.Any:
        return self.dict_.__getitem__(key)

    def __setitem__(self, key: str, value: t.Any) -> None:
        self.dict_.__setitem__(key, value)
