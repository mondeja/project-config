import os
import typing as t

import tomlkit

from project_config.exceptions import ProjectConfigException

VALID_CONFIG_FILES = (
    ".project-config.toml",
    "pyproject.toml",
)


class ProjectConfigInvalidConfig(ProjectConfigException):
    pass


class ConfigurationFilesNotFound(ProjectConfigInvalidConfig):
    def __init__(self) -> None:
        self.message = (
            "None of the expected configuration files have been found:"
            f" {', '.join(VALID_CONFIG_FILES)}"
        )


class CustomConfigFileNotFound(ProjectConfigInvalidConfig):
    def __init__(self, fpath: str) -> None:
        self.message = f"Custom configuration file '{fpath}' not found"


def read_toml_file(fpath: str) -> tomlkit.toml_document.TOMLDocument:
    with open(fpath, "rb") as f:
        return tomlkit.load(f)


def read_config_from_pyproject_toml() -> t.Optional[t.Any]:
    pyproject_toml = read_toml_file("pyproject.toml")
    if "tool" in pyproject_toml and "project-config" in pyproject_toml["tool"]:
        return pyproject_toml["tool"]["project-config"]
    return None


def read_config(custom_file_path: str) -> t.Any:
    if custom_file_path:
        if not os.path.isfile(custom_file_path):
            raise CustomConfigFileNotFound(custom_file_path)
        return read_toml_file(custom_file_path)
    pyproject_toml_exists = os.path.isfile("pyproject.toml")
    config = None
    if pyproject_toml_exists:
        config = read_config_from_pyproject_toml()
    if config is not None:
        return config
    project_config_toml_exists = os.path.isfile(".project-config")
    if project_config_toml_exists:
        return read_toml_file(".project-config")
    raise ConfigurationFilesNotFound()
