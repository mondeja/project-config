import typing as t

from project_config.exceptions import ProjectConfigException


VALID_CONFIG_FILES = (
    ".project-config.toml",
    "pyproject.toml",
)


class ProjectConfigInvalidConfig(ProjectConfigException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProjectConfigInvalidConfigSchema(ProjectConfigInvalidConfig):
    def __init__(
        self,
        config_path: str,
        error_messages: t.List[str],
    ) -> None:
        errors = "\n".join([f"  - {msg}" for msg in error_messages])
        super().__init__(f"The configuration at {config_path} is invalid:\n{errors}")


class ConfigurationFilesNotFound(ProjectConfigInvalidConfig):
    def __init__(self) -> None:
        super().__init__(
            "None of the expected configuration files have been found:"
            f" {', '.join(VALID_CONFIG_FILES)}"
        )


class CustomConfigFileNotFound(ProjectConfigInvalidConfig):
    def __init__(self, fpath: str) -> None:
        super().__init__(f"Custom configuration file '{fpath}' not found")


class PyprojectTomlFoundButHasNoConfig(ProjectConfigInvalidConfig):
    def __init__(self) -> None:
        super().__init__(
            "- pyproject.toml file has been found but has not a [tool.project-config] section\n"
            "- .project-config.toml has not been found"
        )
