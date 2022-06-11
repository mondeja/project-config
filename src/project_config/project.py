import os
import typing as t
from dataclasses import dataclass

from project_config import Error, InterruptingError, ResultValue
from project_config.config import Config
from project_config.reporters import get_reporter
from project_config.tree import Tree, TreeNodeFiles


class InterruptCheck(Exception):
    pass


class ConditionalsFalseResult(InterruptCheck):
    pass


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

    def _check_files_existence(
        self,
        files: TreeNodeFiles,
        rule_index: int,
    ) -> None:
        for f, (fpath, fcontent) in enumerate(files):
            if fcontent is None:  # file or directory does not exist
                ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
                self.reporter.report(
                    {
                        "message": f"Expected {ftype} does not exists",
                        "file": fpath,
                        "definition": f".rules[{rule_index}].files[{f}]",
                    }
                )

    def _process_conditionals_for_rule(
        self,
        conditionals: t.List[str],
        tree: Tree,
        rule: t.Any,  # TODO: improve this type
        rule_index: int,
    ) -> None:
        for conditional in conditionals:
            action_function = self.config.style.plugins.get_method_for_action(
                conditional,
            )
            for breakage_type, breakage_value in action_function(
                rule[conditional],
                tree,
                rule,
            ):
                if breakage_type == InterruptingError:
                    breakage_value["definition"] = (
                        f".rules[{rule_index}]" + breakage_value["definition"]
                    )
                    self.reporter.report(breakage_value)
                    raise InterruptCheck()
                elif breakage_type == ResultValue:
                    if breakage_value is False:
                        raise ConditionalsFalseResult()
                    else:
                        break
                else:
                    raise NotImplementedError(
                        f"Breakage type '{breakage_type}' is not implemented"
                        " for conditionals checking"
                    )

    def _run_check(self) -> None:
        for r, rule in enumerate(self.config["style"]["rules"]):
            self.tree.cache_files(rule.pop("files"))
            # check if files exists
            self._check_files_existence(self.tree.files, r)

            verbs, conditionals = ([], [])
            for action in rule:
                if action.startswith("if"):
                    conditionals.append(action)
                else:
                    verbs.append(action)

            # handle conditionals
            try:
                self._process_conditionals_for_rule(
                    conditionals,
                    self.tree,
                    rule,
                    r,
                )
            except ConditionalsFalseResult:
                # conditionals skipping the rule, next...
                continue

            # handle verbs
            for verb in verbs:
                action_function = self.config.style.plugins.get_method_for_action(verb)
                for breakage_type, breakage_value in action_function(
                    rule[verb],
                    self.tree,
                    rule,
                ):
                    if breakage_type == Error:
                        # prepend rule index to definition, so plugins don't need to specify it
                        breakage_value["definition"] = (
                            f".rules[{r}]" + breakage_value["definition"]
                        )
                        self.reporter.report(breakage_value)
                    elif breakage_type == InterruptingError:
                        breakage_value["definition"] = (
                            f".rules[{r}]" + breakage_value["definition"]
                        )
                        self.reporter.report(breakage_value)
                        raise InterruptCheck()
                        # TODO: show 'INTERRUPTED' in report
                    else:
                        raise NotImplementedError(
                            f"Breakage type '{breakage_type}' is not implemented"
                            " for verbs checking"
                        )

    def check(self) -> None:
        try:
            self._run_check()
        except InterruptCheck:
            pass
        finally:
            self.reporter.run()
