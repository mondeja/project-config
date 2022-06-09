import importlib
import typing as t


reporters = {
    "default": "ProjectConfigDefaultReporter",
    "color": "ProjectConfigColorReporter",
    "colour": "ProjectConfigColorReporter",
    "colored": "ProjectConfigColorReporter",
    "json": "ProjectConfigJsonReporter",
    "toml": "ProjectConfigTomlReporter",
    "yaml": "ProjectConfigYamlReporter",
}


def get_reporter(reporter_name: str) -> t.Any:
    # TODO: custom reporters by module dotpath?
    return getattr(
        importlib.import_module(f"project_config.reporters.{reporter_name}"),
        reporters[reporter_name],
    )
