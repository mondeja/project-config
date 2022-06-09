from dataclasses import dataclass

from project_config.config import Config
from project_config.plugins import Plugins
from project_config.reporters import get_reporter
from project_config.tree import Tree


@dataclass
class Project:
    config_path: str
    rootdir: str
    reporter_name: str

    def __post_init__(self) -> None:
        self.config = Config(self.config_path)
        self.tree = Tree(self.rootdir)
        self.reporter = get_reporter(self.reporter_name)()

    def check(self) -> None:
        for r, rule in enumerate(self.config["style"]["rules"]):
            files = self.tree.files_generator(rule.pop("files"))
            for verb in rule:
                result = self.config.style.plugins.get_method_for_verb(verb)(
                    rule[verb],
                    files,
                    rule,
                    r,
                )
                for error in result["errors"]:
                    self.reporter.report(error)
        self.reporter.run()
