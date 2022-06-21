"""Error reporters."""

import importlib
import typing as t

from tabulate import tabulate_formats

from project_config.exceptions import ProjectConfigNotImplementedError
from project_config.reporters.base import BaseReporter


class ReporterNotImplementedError(ProjectConfigNotImplementedError):
    """A reporter has not been implemented."""

    @classmethod
    def factory(
        cls,
        reporter_name: str,
        fmt: t.Optional[str],
        command: str,
    ) -> "ReporterNotImplementedError":
        """Create an error using convenient arguments.

        Args:
            reporter_name (str): Reporter name.
            fmt (str): Format for reporter.
            command (str): Check mode used.
        """
        format_message = f" with format '{fmt}'" if fmt else ""
        return cls(
            f"The reporter '{reporter_name}'{format_message}"
            f" has not been implemented for the command '{command}'",
        )


reporters = {
    "default": "DefaultReporter",
    "json": "JsonReporter",
    "json:pretty": "JsonReporter",
    "json:pretty4": "JsonReporter",
    "toml": "TomlReporter",
    "yaml": "YamlReporter",
    **{f"table:{fmt}": "TableReporter" for fmt in tabulate_formats},
}

# TODO: custom reporters by module dotpath?


def get_reporter(
    reporter_name: str,
    color: t.Optional[bool],
    rootdir: str,
    command: str,
) -> t.Tuple[BaseReporter, str, t.Optional[str]]:
    """Reporters factory.

    Args:
        reporter_name (str): Reporter identifier name.
        color (bool): Return the colorized version of the reporter,
            if is implemented, using the black/white version as
            a fallback.
        rootdir (str): Root directory of the project.
        command (str): Check mode used.
    """
    # if ':' in the reporter, is passing the kwarg 'format' with the value
    if ":" in reporter_name:
        reporter_name, fmt = reporter_name.split(":")
    else:
        fmt = None

    try:
        reporter_class_name = reporters[reporter_name]
    except KeyError:
        reporter_class_name = reporters[f"{reporter_name}:{fmt}"]

    if color in (True, None):
        reporter_class_name = reporter_class_name.replace(
            "Reporter",
            "ColorReporter",
        )

    Reporter = getattr(
        importlib.import_module(f"project_config.reporters.{reporter_name}"),
        reporter_class_name,
    )
    try:
        return Reporter(rootdir, fmt=fmt), reporter_name, fmt
    except TypeError as exc:
        if "Can't instantiate abstract class" in str(exc) and color is None:
            # reporter not implemented for color
            #
            # try black/white variant
            try:
                Reporter = getattr(
                    importlib.import_module(
                        f"project_config.reporters.{reporter_name}",
                    ),
                    reporter_class_name.replace(
                        "ColorReporter",
                        "Reporter",
                    ),
                )
                return Reporter(rootdir, fmt=fmt), reporter_name, fmt
            except TypeError as exc:
                if "Can't instantiate abstract class" not in str(exc):
                    raise
                raise ReporterNotImplementedError.factory(
                    reporter_name,
                    fmt,
                    command,
                )
        raise
