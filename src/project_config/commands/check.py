import argparse
import os

from project_config.config import Config, read_config, validate_config
from project_config.plugins import Plugins
from project_config.reporters import reporters
from project_config.config.style import get_style
from project_config.tree import Tree


def check(args: argparse.Namespace) -> bool:
    config = Config(args.config).read()
    plugins = Plugins(config["style"]["plugins"])

    # run
    tree, reporter = Tree(args.rootdir), reporters[args.reporter]()

    for r, rule in enumerate(config["style"]["rules"]):
        files = tree.files_generator(rule.pop("files"))
        for verb in rule:
            verb_method = plugins.get_method_for_verb(verb)
            result = verb_method(rule[verb], files, rule, r)
            for error in result["errors"]:
                reporter.report(error)
    reporter.run()

    return True
