"""Error reporters."""

from __future__ import annotations

import importlib
import json
import types
from collections.abc import Callable
from typing import Any

from tabulate import tabulate_formats

from project_config.compat import importlib_metadata
from project_config.exceptions import ProjectConfigException
from project_config.reporters.base import BaseReporter


DEFAULT_REPORTER = "default"
PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP = "project_config.reporters"


class UnparseableReporterError(ProjectConfigException):
    """Reporter can't be parsed."""

    def __init__(self, reporter_id: str) -> None:
        super().__init__(
            f"Reporter '{reporter_id}' can't be parsed. "
            "See 'project-config --help' for more information.",
        )


class InvalidThirdPartyReporterName(ProjectConfigException):
    """A third party reporter can't be loaded by his identifier."""

    def __init__(self, reporter_id: str) -> None:
        super().__init__(
            f"Reporter '{reporter_id}' not found. See all"
            " available running 'project-config show reporters'",
        )


class InvalidNotBasedThirdPartyReporter(ProjectConfigException):
    """Reporter not based on base reporter class.

    All reporters must be based on the base reporter class
    :py::class:``project_config.reporters.base.BaseReporter``.
    """


class InvalidThirdPartyReportersModule(ProjectConfigException):
    """Third party reporters module is invalid.

    Third party reporters module must expose a color and a black/white
    reporter.
    """


reporters = {
    "default": "DefaultReporter",
    "json": "JsonReporter",
    "json:pretty": "JsonReporter",
    "json:pretty4": "JsonReporter",
    "toml": "TomlReporter",
    "yaml": "YamlReporter",
    **{f"table:{fmt}": "TableReporter" for fmt in tabulate_formats},
}

reporters_modules = {
    "json": "json_",
}


def _parse_reporter_arguments(arguments_string: str) -> dict[str, Any]:
    result: dict[str, str] = {}
    for arg_value in arguments_string.split(";"):
        key, value = arg_value.split("=", maxsplit=1)
        result[key] = json.loads(value)
    return result


def parse_reporter_id(value: str) -> tuple[str, dict[str, Any]]:
    """Parse a reporter identifier.

    Returns the reporter name and the optional arguments for his class.

    Args:
        value (str): Reporter identifier.
    """
    if ";" in value:
        reporter_id, reporter_kwargs_string = value.split(";", maxsplit=1)
    else:
        reporter_id, reporter_kwargs_string = value, ""
    if ":" in reporter_id:
        reporter_name, fmt = reporter_id.split(":", maxsplit=1)
    else:
        reporter_name, fmt = reporter_id, None

    if reporter_kwargs_string:
        reporter_kwargs = _parse_reporter_arguments(reporter_kwargs_string)
    else:
        reporter_kwargs = {}
    return reporter_name, {**reporter_kwargs, "fmt": fmt}


def get_reporter(
    reporter_name: str,
    reporter_kwargs: dict[str, Any],
    color: bool | None,
    rootdir: str,
    only_hints: bool = False,
) -> Any:
    """Reporters factory.

    Args:
        reporter_name (str): Reporter identifier name.
        reporter_kwargs (dict): Optional arguments for reporter class.
        color (bool): Return the colorized version of the reporter,
            if is implemented, using the black/white version as
            a fallback.
        rootdir (str): Root directory of the project.
        only_hints (bool): If ``True``, only hints will be reported.
    """
    try:
        if reporter_name in reporters:
            reporter_class_name = reporters[reporter_name]
        else:
            reporter_class_name = reporters[
                f"{reporter_name}:{reporter_kwargs.get('fmt')}"
            ]
    except KeyError:
        # 3rd party reporter
        third_party_reporters = ThirdPartyReporters()
        reporter_module = third_party_reporters.load(reporter_name)
        (
            color_class_name,
            bw_class_name,
        ) = third_party_reporters.validate_reporter_module(
            reporter_module,
        )
        # validate both reporters in the class
        for class_name in (color_class_name, bw_class_name):
            third_party_reporters.validate_reporter_class(
                getattr(reporter_module, class_name),
            )

        reporter_class_name = color_class_name if color else bw_class_name
        Reporter = getattr(reporter_module, reporter_class_name)
        third_party_reporters.validate_reporter_class(Reporter)
    else:
        reporter_module_name = reporters_modules.get(
            reporter_name,
            reporter_name,
        )
        reporter_module = importlib.import_module(
            f"project_config.reporters.{reporter_module_name}",
        )
        if color in (True, None):
            reporter_class_name = reporter_class_name.replace(
                "Reporter",
                "ColorReporter",
            )
        Reporter = getattr(reporter_module, reporter_class_name)

    reporter_kwargs.update({"only_hints": only_hints})
    return Reporter(rootdir, **reporter_kwargs)


class ThirdPartyReporters:
    """Third party reporters loader from entrypoints."""

    # allow to reset the instance, just for testing purposes
    instance: ThirdPartyReporters | None = None

    def __new__(cls) -> ThirdPartyReporters:  # noqa: D102
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.reporters_loaders: dict[
            str,
            Callable[[], types.ModuleType],
        ] = {}
        self.loaded_reporters: dict[str, types.ModuleType] = {}
        self._prepare_third_party_reporters()

    @property
    def ids(self) -> list[str]:
        """Returns the identifiers of the 3rd party reporters."""
        return list(self.reporters_loaders.keys())

    def _prepare_third_party_reporters(self) -> None:
        for reporter_entrypoint in importlib_metadata.entry_points(
            group=PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP,
        ):
            self.reporters_loaders[
                reporter_entrypoint.name
            ] = reporter_entrypoint.load

    def load(self, reporter_name: str) -> types.ModuleType:
        """Load a third party reporter.

        Args:
            reporter_name (str): Reporter module entrypoint name.
        """
        if reporter_name not in self.loaded_reporters:
            try:
                reporter_impl = self.reporters_loaders[reporter_name]
            except KeyError:
                # A third party reporter was not found
                raise InvalidThirdPartyReporterName(reporter_name)
            else:
                self.loaded_reporters[reporter_name] = reporter_impl()
        return self.loaded_reporters[reporter_name]

    def validate_reporter_module(
        self,
        reporter_module: types.ModuleType,
    ) -> tuple[str, str]:
        """Validate a reporter module.

        Returns black/white and color reporter class names if the reporters
        module is valid.

        Args:
            reporter_module (type): Reporters module to validate.
        """
        color_reporter_class_name = ""
        bw_reporter_class_name = ""
        for object_name in dir(reporter_module):
            if object_name.startswith(("_", "Base")):
                continue
            if "ColorReporter" in object_name:
                if not color_reporter_class_name:
                    color_reporter_class_name = object_name
                else:
                    raise InvalidThirdPartyReportersModule(
                        "Multiple public color reporters found in module"
                        f" '{reporter_module.__name__}'",
                    )
            elif "Reporter" in object_name:
                if not bw_reporter_class_name:
                    bw_reporter_class_name = object_name
                else:
                    raise InvalidThirdPartyReportersModule(
                        "Multiple public black/white reporters found in"
                        f" module '{reporter_module.__name__}'",
                    )
        if not color_reporter_class_name:
            raise InvalidThirdPartyReportersModule(
                "No color reporter found in module"
                f" '{reporter_module.__name__}'",
            )
        if not bw_reporter_class_name:
            raise InvalidThirdPartyReportersModule(
                "No black/white reporter found in module"
                f" '{reporter_module.__name__}'",
            )
        return color_reporter_class_name, bw_reporter_class_name

    def validate_reporter_class(self, reporter_class: Any) -> None:
        """Validate a reporter class.

        Args:
            reporter_class (type): Reporter class to validate.
        """
        if not issubclass(reporter_class, BaseReporter):
            raise InvalidNotBasedThirdPartyReporter(
                f"Reporter class '{reporter_class.__name__}' is not"
                " a subclass of BaseReporter",
            )
