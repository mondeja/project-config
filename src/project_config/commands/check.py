import argparse

from project_config.config import read_config, validate_config
from project_config.plugins import get_plugins
from project_config.style import get_style


def check(args: argparse.Namespace) -> bool:
    config_path, config = read_config(args.config)
    validate_config(config_path, config)
    style = get_style(config["style"])
    plugins = get_plugins(plugin_names=style["plugins"])

    return True
