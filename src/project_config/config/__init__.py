"""Configuration handler."""

import os
import re
import typing as t

from project_config.cache import Cache
from project_config.compat import TypeAlias
from project_config.config.exceptions import (
    ConfigurationFilesNotFound,
    CustomConfigFileNotFound,
    ProjectConfigInvalidConfig,
    ProjectConfigInvalidConfigSchema,
    PyprojectTomlFoundButHasNoConfig,
)
from project_config.config.style import Style
from project_config.fetchers import fetch
from project_config.reporters import DEFAULT_REPORTER, POSSIBLE_REPORTER_IDS


CONFIG_CACHE_REGEX = (
    r"^(\d+ ((seconds?)|(minutes?)|(hours?)|(days?)|(weeks?)))|(never)$"
)

ConfigType: TypeAlias = t.Dict[str, t.Union[str, t.List[str]]]


def read_config_from_pyproject_toml() -> t.Optional[t.Any]:
    """Read the configuration from the `pyproject.toml` file.

    Returns:
        object: ``None`` if not found, configuration data otherwise.
    """
    pyproject_toml = fetch("pyproject.toml")
    if "tool" in pyproject_toml and "project-config" in pyproject_toml["tool"]:
        return pyproject_toml["tool"]["project-config"]
    return None


def read_config(
    custom_file_path: t.Optional[str] = None,
) -> t.Tuple[str, t.Any]:
    """Read the configuration from a file.

    Args:
        custom_file_path (str): Custom configuration file path
            or ``None`` if the configuration must be read from
            one of the default configuration file paths.

    Returns:
        object: Configuration data.
    """
    if custom_file_path:
        if not os.path.isfile(custom_file_path):
            raise CustomConfigFileNotFound(custom_file_path)
        return custom_file_path, dict(fetch(custom_file_path))

    pyproject_toml_exists = os.path.isfile("pyproject.toml")
    config = None
    if pyproject_toml_exists:
        config = read_config_from_pyproject_toml()
    if config is not None:
        return '"pyproject.toml".[tool.project-config]', dict(config)

    project_config_toml_exists = os.path.isfile(".project-config.toml")
    if project_config_toml_exists:
        return ".project-config.toml", dict(
            fetch(".project-config.toml"),
        )

    if pyproject_toml_exists:
        raise PyprojectTomlFoundButHasNoConfig()
    raise ConfigurationFilesNotFound()


def validate_config_style(config: t.Any) -> t.List[str]:
    """Validate the ``style`` field of a configuration object.

    Args:
        config (object): Configuration data to validate.

    Returns:
        list: Found error messages.
    """
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
                    error_messages.append(
                        f"style[{i}] -> must be of type string",
                    )
                elif not style:
                    error_messages.append(f"style[{i}] -> must not be empty")
    elif not config["style"]:
        error_messages.append("style -> must not be empty")
    return error_messages


def _cache_string_to_seconds(cache_string: str) -> int:
    if "never" in cache_string:
        return 0
    cache_number = int(cache_string.split(" ", maxsplit=1)[0])

    if "minute" in cache_string:
        return cache_number * 60
    elif "hour" in cache_string:
        return cache_number * 60 * 60
    elif "day" in cache_string:
        return cache_number * 60 * 60 * 24
    elif "second" in cache_string:
        return cache_number
    elif "week" in cache_string:
        return cache_number * 60 * 60 * 24 * 7
    raise ValueError(cache_string)


def validate_config_cache(config: t.Any) -> t.List[str]:
    """Validate the ``cache`` field of a configuration object.

    Args:
        config (object): Configuration data to validate.

    Returns:
        list: Found error messages.
    """
    error_messages = []
    if "cache" in config:
        if not isinstance(config["cache"], str):
            error_messages.append("cache -> must be of type string")
        elif not config["cache"]:
            error_messages.append("cache -> must not be empty")
        elif not re.match(CONFIG_CACHE_REGEX, config["cache"]):
            error_messages.append(
                f"cache -> must match the regex {CONFIG_CACHE_REGEX}",
            )
    else:
        # 5 minutes as default cache
        config["cache"] = "5 minutes"
    return error_messages


def validate_config(config_path: str, config: t.Any) -> None:
    """Validate a configuration.

    Args:
        config_path (str): Configuration file path.
        config (object): Configuration data to validate.
    """
    error_messages = [
        *validate_config_style(config),
        *validate_config_cache(config),
    ]

    if error_messages:
        raise ProjectConfigInvalidConfigSchema(
            config_path,
            error_messages,
        )


def _validate_cli_config(config: t.Dict[str, t.Any]) -> t.List[str]:
    errors: t.List[str] = []
    if "reporter" in config:
        if not isinstance(config["reporter"], str):
            errors.append("cli.reporter -> must be of type string")
        elif not config["reporter"]:
            errors.append("cli.reporter -> must not be empty")
        elif config["reporter"] not in POSSIBLE_REPORTER_IDS:
            errors.append(
                "cli.reporter -> must be one of the available reporters",
            )

    if "color" in config:
        if not isinstance(config["color"], bool):
            errors.append("cli.color -> must be of type boolean")

    if "colors" in config:
        if not isinstance(config["colors"], dict):
            errors.append("cli.colors -> must be of type object")
        elif not config["colors"]:
            errors.append("cli.colors -> must not be empty")

        # colors are validated in the reporter

    if "rootdir" in config:
        if not isinstance(config["rootdir"], str):
            errors.append("cli.rootdir -> must be of type string")
        elif not config["rootdir"]:
            errors.append("cli.rootdir -> must not be empty")
        else:
            config["rootdir"] = os.path.abspath(
                os.path.expanduser(config["rootdir"]),
            )

    return errors


def validate_cli_config(
    config_path: str,
    config: t.Dict[str, t.Any],
) -> t.Dict[str, t.Any]:
    """Validates the CLI configuration.

    Args:
        config (dict): Raw CLI configuration.

    Returns:
        object: CLI configuration data.
    """
    errors = _validate_cli_config(config)
    if errors:
        raise ProjectConfigInvalidConfigSchema(config_path, errors)
    return config


class Config:
    """Configuration wrapper.

    Args:
        rootdir (str): Project root directory.
        path (str): Path to the file from which the configuration
            will be loaded.
        fetch_styles (bool): Whether to fetch the styles in the styles
            loader.
        validate_cli_config (bool): Whether to validate the CLI
            configuration.
    """

    def __init__(
        self,
        rootdir: str,
        path: t.Optional[str],
    ) -> None:
        self.rootdir = rootdir
        self.path, config = read_config(path)
        validate_config(self.path, config)

        # cli configuration in file
        self.cli = validate_cli_config(self.path, config.pop("cli", {}))

        config["_cache"] = config["cache"]
        config["cache"] = _cache_string_to_seconds(config["cache"])

        # set the cache expiration time globally
        Cache.set(
            Cache.Keys.expiration,
            config["cache"],
            expire=None,
        )
        # main configuration in file
        self.dict_: ConfigType = config

    def load_style(self) -> None:  # noqa: D102
        self.style = Style.from_config(self)

    def guess_from_cli_arguments(
        self,
        color: t.Optional[bool],
        reporter: t.Dict[str, t.Any],
        rootdir: str,
    ) -> t.Tuple[t.Any, t.Dict[str, t.Any], t.Any]:
        """Guess the final configuration merging file with CLI arguments."""
        # colorize output?
        color = self.cli.get("color") if color is True else color

        # reporter definition
        reporter_kwargs = reporter.get("kwargs", {})
        reporter_id = reporter.get(
            "name",
            self.cli.get("reporter", DEFAULT_REPORTER),
        )
        if ":" in reporter_id:
            reporter["name"], reporter_kwargs["fmt"] = reporter_id.split(
                ":",
                maxsplit=1,
            )
        else:
            reporter["name"] = reporter_id

        if color in (True, None):
            if "colors" in self.cli:
                colors = self.cli.get("colors", {})
                for key, value in reporter_kwargs.get("colors", {}).items():
                    colors[key] = value  # cli overrides config
                reporter_kwargs["colors"] = colors
            reporter["kwargs"] = reporter_kwargs
        else:
            reporter["kwargs"] = reporter_kwargs

        if not rootdir:
            rootdir = self.cli.get("rootdir")  # type: ignore
            if rootdir:
                self.rootdir = os.path.expanduser(rootdir)
            else:
                self.rootdir = os.getcwd()
        else:
            self.rootdir = os.path.abspath(rootdir)

        if not os.path.isdir(self.rootdir):  # pragma: no cover
            raise ProjectConfigInvalidConfig(
                f"Root directory '{rootdir}' must be an existing directory",
            )

        return (
            color,
            reporter,
            self.rootdir,
        )

    def __getitem__(self, key: str) -> t.Any:
        return self.dict_.__getitem__(key)

    def __setitem__(self, key: str, value: t.Any) -> None:
        self.dict_.__setitem__(key, value)
