import os
from dataclasses import dataclass

from project_config.config import Config
from project_config.reporters import get_reporter
from project_config.tree import Tree


@dataclass
class Project:
    config_path: str
    rootdir: str
    reporter_name: str
    color: bool

    def __post_init__(self) -> None:
        self.config = Config(self.config_path)
        self.tree = Tree(self.rootdir)
        self.reporter = get_reporter(self.reporter_name, self.color)(
            self.rootdir,
        )

    def check(self) -> None:
        for r, rule in enumerate(self.config["style"]["rules"]):
            files = list(self.tree.generator(rule.pop("files")))
            # check if files exists
            for f, (fpath, fcontent) in enumerate(files):
                if fcontent is None:  # file or directory does not exist
                    ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
                    self.reporter.report(
                        {
                            "message": f"Expected {ftype} does not exists",
                            "file": fpath,
                            "definition": f".rules[{r}].files[{f}]",
                        }
                    )

            verbs, conditionals = ([], [])
            for action in rule:
                if action.startswith("if"):
                    conditionals.append(action)
                else:
                    verbs.append(action)
            actions = conditionals + verbs

            for action in actions:
                action_function = self.config.style.plugins.get_method_for_action(
                    action
                )
                for result_type, result_value in action_function(
                    rule[action],
                    files,
                    rule,
                ):
                    if result_type == "error":
                        # prepend rule index to definition, so plugins don't need to specify it
                        result_value["definition"] = (
                            f".rules[{r}]" + result_value["definition"]
                        )
                        self.reporter.report(result_value)
        self.reporter.run()
