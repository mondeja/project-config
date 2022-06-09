import importlib

reporters = {
    "default": 'ProjectConfigDefaultReporter',
    "json": 'ProjectConfigJsonReporter',
    "toml": 'ProjectConfigTomlReporter',
    "yaml": 'ProjectConfigYamlReporter',
}

def get_reporter(reporter_name: str) -> type:
    # TODO: custom reporters by module dotpath?
    return getattr(
        importlib.import_module(f"project_config.reporters.{reporter_name}"),
        reporters[reporter_name],
    )