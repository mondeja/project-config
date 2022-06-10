import functools
import importlib
import typing as t

from tabulate import tabulate_formats


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

def get_reporter(reporter_name: str, color: bool) -> t.Any:
    # if ':' in the reporter, is passing the kwarg 'format' with the value
    if ":" in reporter_name:
        reporter_name, format = reporter_name.split(":")
    else:
        format = None

    try:
        reporter_class_name = reporters[reporter_name]
    except KeyError:
        reporter_class_name = reporters[f"{reporter_name}:{format}"]
    if color:
        reporter_class_name = reporter_class_name.replace(
            "Reporter",
            "ColorReporter",
        )

    reporter_class = getattr(
        importlib.import_module(f"project_config.reporters.{reporter_name}"),
        reporter_class_name,
    )

    return functools.partial(reporter_class, format=format)
