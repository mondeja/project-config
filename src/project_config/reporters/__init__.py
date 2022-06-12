import functools
import importlib
import typing as t

from tabulate import tabulate_formats

from project_config.exceptions import ProjectConfigNotImplementedError


class ReporterNotImplementedError(ProjectConfigNotImplementedError):
    pass


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
) -> t.Any:
    # if ':' in the reporter, is passing the kwarg 'format' with the value
    if ":" in reporter_name:
        reporter_name, format = reporter_name.split(":")
    else:
        format = None

    try:
        reporter_class_name = reporters[reporter_name]
    except KeyError:
        reporter_class_name = reporters[f"{reporter_name}:{format}"]

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
        return Reporter(rootdir, format=format), reporter_name, format
    except TypeError as exc:
        if "Can't instantiate abstract class" in str(exc) and color is None:
            # reporter not implemented for color
            #
            # try black/white variant
            try:
                Reporter = getattr(
                    importlib.import_module(
                        f"project_config.reporters.{reporter_name}"
                    ),
                    reporter_class_name.replace(
                        "ColorReporter",
                        "Reporter",
                    ),
                )
                return Reporter(rootdir, format=format), reporter_name, format
            except TypeError as exc:
                if "Can't instantiate abstract class" not in str(exc):
                    raise
                raise reporter_not_implemented_error_factory(
                    reporter_name,
                    format,
                    command,
                )
        raise


def reporter_not_implemented_error_factory(
    reporter_name: str,
    format: t.Optional[str],
    command: str,
) -> type:
    format_message = f" with format '{format}'" if format else ""
    return ReporterNotImplementedError(
        f"The reporter '{reporter_name}'{format_message}"
        f" has not been implemented for the command '{command}'"
    )
