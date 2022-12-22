"""Configuration exceptions."""

from __future__ import annotations

import os

from project_config.exceptions import ProjectConfigException


VALID_CONFIG_FILES = (
    ".project-config.toml",
    "pyproject.toml",
)


class ProjectConfigInvalidConfig(ProjectConfigException):
    """Invalid configuration of project-config found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProjectConfigInvalidConfigSchema(ProjectConfigInvalidConfig):
    """The configuration of project-config is invalid."""

    def __init__(
        self,
        config_path: str,
        error_messages: list[str],
    ) -> None:
        errors = "\n".join([f"  - {msg}" for msg in error_messages])
        super().__init__(
            f"The configuration at {config_path} is invalid:\n{errors}",
        )


class ConfigurationFilesNotFound(ProjectConfigInvalidConfig):
    """The expected configuration files have not been found."""

    def __init__(self) -> None:
        super().__init__(
            "None of the expected configuration files have been found:"
            f" {', '.join(VALID_CONFIG_FILES)}",
        )


class CustomConfigFileNotFound(ProjectConfigInvalidConfig):
    """A custom configuration file has not been found."""

    def __init__(self, fpath: str) -> None:
        super().__init__(
            f"Custom configuration file '{fpath}' not found",
        )


class PyprojectTomlFoundButHasNoConfig(ProjectConfigInvalidConfig):
    """A `pyproject.toml` file has been found but has no configuration."""

    def __init__(self) -> None:
        super().__init__(
            "- pyproject.toml file has been found but has not a"
            " [tool.project-config] section\n"
            "- .project-config.toml has not been found",
        )


class ProjectConfigAlreadyInitialized(ProjectConfigException):
    """The project-config has already been initialized."""

    def __init__(self, config_path: str) -> None:
        super().__init__(
            "The configuration for project-config has already been"
            f" initialized at {os.path.relpath(config_path, os.getcwd())}",
        )
