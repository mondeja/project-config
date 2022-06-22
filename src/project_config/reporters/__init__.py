"""Error reporters."""

import importlib
import types
import typing as t

from tabulate import tabulate_formats

from project_config.compat import importlib_metadata
from project_config.exceptions import ProjectConfigException


PROJECT_CONFIG_REPORTERS_ENTRYPOINTS_GROUP = "project_config.reporters"


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


def get_reporter(
    reporter_name: str,
    color: t.Optional[bool],
    rootdir: str,
) -> t.Any:
    """Reporters factory.

    Args:
        reporter_name (str): Reporter identifier name.
        color (bool): Return the colorized version of the reporter,
            if is implemented, using the black/white version as
            a fallback.
        rootdir (str): Root directory of the project.
    """
    # if ':' in the reporter, is passing the kwarg 'format' with the value
    if ":" in reporter_name:
        reporter_name, fmt = reporter_name.split(":")
    else:
        fmt = None

    try:
        if reporter_name in reporters:
            reporter_class_name = reporters[reporter_name]
        else:
            reporter_class_name = reporters[f"{reporter_name}:{fmt}"]
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
        reporter_class_name = color_class_name if color else bw_class_name
    else:
        reporter_module = importlib.import_module(
            f"project_config.reporters.{reporter_name}",
        )
        if color in (True, None):
            reporter_class_name = reporter_class_name.replace(
                "Reporter",
                "ColorReporter",
            )

    return getattr(reporter_module, reporter_class_name)(rootdir, fmt=fmt)


class ThirdPartyReporters:
    """Third party reporters loader from entrypoints."""

    # allow to reset the instance, just for testing purposes
    instance: t.Optional["ThirdPartyReporters"] = None

    def __new__(cls) -> "ThirdPartyReporters":  # noqa: D102
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.reporters_loaders: t.Dict[
            str,
            t.Callable[[], types.ModuleType],
        ] = {}
        self.loaded_reporters: t.Dict[str, types.ModuleType] = {}
        self._prepare_third_party_reporters()

    @property
    def ids(self) -> t.List[str]:
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
            self.loaded_reporters[reporter_name] = self.reporters_loaders[
                reporter_name
            ]()
        return self.loaded_reporters[reporter_name]

    def validate_reporter_module(
        self,
        reporter_module: types.ModuleType,
    ) -> t.Tuple[str, str]:
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
                        "Multiple public colors reporters found in module"
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
