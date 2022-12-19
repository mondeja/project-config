"""Configuration handler."""

from __future__ import annotations

import argparse
import importlib
import os
import re
from typing import TYPE_CHECKING, Any

from project_config.cache import Cache
from project_config.compat import TypedDict, tomllib_package_name
from project_config.config.exceptions import (
    ConfigurationFilesNotFound,
    CustomConfigFileNotFound,
    ProjectConfigAlreadyInitialized,
    ProjectConfigInvalidConfig,
    ProjectConfigInvalidConfigSchema,
    PyprojectTomlFoundButHasNoConfig,
)
from project_config.config.style import Style
from project_config.fetchers import fetch
from project_config.reporters import (
    DEFAULT_REPORTER,
    POSSIBLE_REPORTER_IDS,
    get_reporter,
)


CONFIG_CACHE_REGEX = (
    r"^(\d+ ((seconds?)|(minutes?)|(hours?)|(days?)|(weeks?)))|(never)$"
)

if TYPE_CHECKING:
    from project_config.compat import NotRequired
    from project_config.config.style import StyleType

    class CLIConfigType(TypedDict):  # noqa: D101
        rootdir: str
        reporter: str
        color: bool
        colors: dict[str, str]
        only_hints: bool
        _reporter_definition: dict[str, Any]

    class BaseConfigType(TypedDict):  # noqa: D101
        style: NotRequired[StyleType]
        cli: CLIConfigType

    class RawConfigType(BaseConfigType):  # noqa: D101
        cache: int

    class ConfigType(BaseConfigType):  # noqa: D101
        """Type of the configuration."""

        cache: str


def read_config_from_pyproject_toml(filepath: str) -> Any:
    """Read the configuration from the `pyproject.toml` file.

    Returns:
        object: ``None`` if not found, configuration data otherwise.
    """
    tomllib = importlib.import_module(tomllib_package_name)
    with open(filepath, "rb") as f:
        pyproject_toml = tomllib.load(f)
    if "tool" in pyproject_toml and "project-config" in pyproject_toml["tool"]:
        return pyproject_toml["tool"]["project-config"]
    return None


def read_config(
    rootdir: str,
    custom_file_path: str | None = None,
) -> tuple[str, Any]:
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

    pyproject_toml_path = os.path.join(rootdir, "pyproject.toml")
    pyproject_toml_exists = os.path.isfile(pyproject_toml_path)
    config = None
    if pyproject_toml_exists:
        config = read_config_from_pyproject_toml(pyproject_toml_path)
    if config is not None:
        return '"pyproject.toml".[tool.project-config]', dict(config)

    project_config_toml_path = os.path.join(rootdir, ".project-config.toml")
    project_config_toml_exists = os.path.isfile(project_config_toml_path)
    if project_config_toml_exists:
        tomllib = importlib.import_module(tomllib_package_name)
        with open(project_config_toml_path, "rb") as f:
            project_config_toml = tomllib.load(f)
        return ".project-config.toml", project_config_toml

    if pyproject_toml_exists:
        raise PyprojectTomlFoundButHasNoConfig()
    raise ConfigurationFilesNotFound()


def validate_config_style(config: Any) -> list[str]:
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


def validate_config_cache(config: Any) -> list[str]:
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


def validate_config(config_path: str, config: Any) -> None:
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


def _validate_cli_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
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
    config: dict[str, Any],
) -> dict[str, Any]:
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


class FileConfig:
    """File configuration wrapper.

    Stores the data of the project-config configuration defined in
    the file '.project-config.toml' or equivalent. The configuration
    of the file is stored in the ``dict_`` attribute and can be accesed
    with ``__getitem__`` and ``__setitems__`` calls.

    Args:
        rootdir (str): Project root directory.
        path (str): Path to the file from which the configuration
            will be loaded.
        store_raw_config (bool): If ``True``, the raw configuration
            of the file will be stored in the ``raw_`` attribute.
    """

    def __init__(
        self,
        rootdir: str,
        path: str | None,
        store_raw_config: bool = False,
    ) -> None:
        self.path, config = read_config(rootdir, path)

        if store_raw_config:
            import copy

            self.raw_: RawConfigType = copy.deepcopy(config)

        validate_config(self.path, config)
        config["cache"] = _cache_string_to_seconds(config["cache"])

        # cli configuration in file
        config["cli"] = validate_cli_config(self.path, config.get("cli", {}))

        # set the cache expiration time globally
        Cache.set_expiration_time(config["cache"])

        # configuration
        self.dict_: ConfigType = config

    def load_style(self) -> None:  # noqa: D102
        self.style = Style.from_config(self)


class Config(FileConfig):
    """Main configuration wrapper.

    This class is the main configuration wrapper. It is used to
    load a configuration object from CLI arguments.
    """

    def __init__(self, args: argparse.Namespace, **kwargs: Any) -> None:
        """Guess the final configuration merging file with CLI arguments."""
        super().__init__(args.rootdir or os.getcwd(), args.config, **kwargs)

        # colorize output?
        self.dict_["cli"]["color"] = (
            self.dict_["cli"].get("color") if args.color is True else args.color
        )

        # reporter definition
        reporter_kwargs = args.reporter.get("kwargs", {})
        reporter_id = args.reporter.get(
            "name",
            self.dict_["cli"].get("reporter", DEFAULT_REPORTER),
        )
        if ":" in reporter_id:
            args.reporter["name"], reporter_kwargs["fmt"] = reporter_id.split(
                ":",
                maxsplit=1,
            )
        else:
            args.reporter["name"] = reporter_id

        if args.color in (True, None):
            if "colors" in self.dict_["cli"]:
                colors = self.dict_["cli"].get("colors", {})
                for key, value in reporter_kwargs.get("colors", {}).items():
                    colors[key] = value  # cli overrides config
                reporter_kwargs["colors"] = colors
            args.reporter["kwargs"] = reporter_kwargs
        else:
            args.reporter["kwargs"] = reporter_kwargs
        self.dict_["cli"]["_reporter_definition"] = args.reporter

        if not args.rootdir:
            _rootdir = self.dict_["cli"].get("rootdir")
            if isinstance(_rootdir, str):
                self.dict_["cli"]["rootdir"] = os.path.expanduser(_rootdir)
            else:
                self.dict_["cli"]["rootdir"] = os.getcwd()
        else:
            self.dict_["cli"]["rootdir"] = os.path.abspath(args.rootdir)

        if not os.path.isdir(self.dict_["cli"]["rootdir"]):  # pragma: no cover
            rootdir = self.dict_["cli"]["rootdir"]
            raise ProjectConfigInvalidConfig(
                f"Root directory '{rootdir}' must be an existing directory",
            )
        else:
            # set rootdir as an internal environment variable to be
            # used by plugins
            os.environ["PROJECT_CONFIG_ROOTDIR"] = self.dict_["cli"]["rootdir"]

        self.dict_["cli"]["only_hints"] = (
            self.dict_["cli"].get("only_hints") is True
            or args.only_hints is True
        )


def reporter_from_config(config: Config) -> Any:
    """Instanciate a reporter from a configuration object.

    Args:
        config (Config): Configuration object.
    """
    config_cli = config.dict_.get("cli", {})
    return get_reporter(
        config_cli.get("_reporter_definition", {}).get(
            "name",
            DEFAULT_REPORTER,
        ),
        config_cli.get("_reporter_definition", {}).get("kwargs", {}),
        config_cli.get("color", None),
        config_cli.get("rootdir", os.getcwd()),
        only_hints=config_cli.get("only_hints", False),
    )


def initialize_config(config_filepath: str) -> str:
    """Initialize the configuration.

    Args:
        config_filepath (str): Path to the file in which the configuration will
            be stored.

    Returns:
        str: Path to the configuration.
    """
    config_dirpath = os.path.join(
        os.path.abspath(os.path.dirname(config_filepath)),
    )
    os.makedirs(config_dirpath, exist_ok=True)

    if not os.path.isfile(config_filepath):
        with open(config_filepath, "w", encoding="ascii") as f:
            f.write("")

    style_filepath = os.path.join(config_dirpath, "style.json5")

    config_file_basename = os.path.basename(config_filepath)

    def create_default_style_file(
        config_prefix: str = "@",
        prefix_jmespaths: str = "",
    ) -> None:
        """Create the default style file if it does not exist."""
        if config_prefix == "@":

            def key_matcher(key: str) -> str:
                return key

            style_setter = "set(@, 'style', ['style.json5'])"
            cache_setter = "set(@, 'cache', '5 minutes')"
        else:

            def key_matcher(key: str) -> str:
                return f'tool.\\"project-config\\".{key}'

            style_setter = (
                "set(@, 'tool', set(tool, 'project-config',"
                ' set(tool.\\"project-config\\",'
                " 'style', ['style.json5'])))"
            )
            cache_setter = (
                "set(@, 'tool', set(tool, 'project-config',"
                ' set(tool.\\"project-config\\",'
                " 'cache', '5 minutes')))"
            )

        with open(style_filepath, "w", encoding="ascii") as f:
            f.write(
                '''{
  rules: [
    {
      files: ["'''
                + config_file_basename
                + """"],
      JMESPathsMatch: [\n        """
                + prefix_jmespaths
                + """["type("""
                + key_matcher("style")
                + """)", "array"],
        ["op(length("""
                + key_matcher("style")
                + """), '>', `0`)", true, """
                + '"'
                + style_setter
                + '"'
                + """],
        ["type("""
                + key_matcher("cache")
                + """)", "string", """
                + '"'
                + cache_setter
                + '"'
                + """],
        [
          "regex_match('(\\\\d+ ((seconds?)|(minutes?)|(hours?)|(days?)|(weeks?)))|(never)$', """  # noqa: E501,
                + key_matcher("cache")
                + """)",
          true,
          "5 minutes",
        ],
      ]
    }
  ]
}
""",
            )

    def build_config_string(pyproject_toml: bool = False) -> str:
        result = ""
        if pyproject_toml:
            result += "[tool.project-config]\n"
        return f'{result}style = ["style.json5"]\ncache = "5 minutes"\n'

    def add_config_string_to_file(string: str) -> None:
        with open(config_filepath, encoding="ascii") as f:
            config_lines = f.read().splitlines()
        if config_lines:
            add_separator = config_lines[-1] != ""
        else:
            add_separator = False

        with open(config_filepath, "a", encoding="ascii") as f:
            if add_separator:
                f.write("\n")
            f.write(string)

    if config_file_basename == "pyproject.toml":
        config = read_config_from_pyproject_toml(config_filepath)
        if config:
            raise ProjectConfigAlreadyInitialized(
                f"{config_filepath}[tool.project-config]",
            )

        add_config_string_to_file(build_config_string(pyproject_toml=True))

        create_default_style_file(
            config_prefix='tool.\\"project-config\\"',
            prefix_jmespaths=(
                '["type(tool)", "object"],'
                '\n        ["type(tool.\\"project-config\\")", "object"],'
                "\n        "
            ),
        )
        return f"{config_filepath}[tool.project-config]"

    if os.path.isfile(config_filepath):
        with open(config_filepath, encoding="ascii") as f:
            if f.read():
                raise ProjectConfigAlreadyInitialized(config_filepath)

    add_config_string_to_file(build_config_string())
    create_default_style_file()
    return config_filepath
