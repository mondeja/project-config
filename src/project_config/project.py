import os
import sys
import typing as t
from dataclasses import dataclass

from project_config import Error, InterruptingError, ResultValue
from project_config.config import Config
from project_config.plugins import InvalidPluginMethod
from project_config.reporters import (
    get_reporter,
    reporter_not_implemented_error_factory,
)
from project_config.tree import Tree, TreeNodeFiles


class InterruptCheck(Exception):
    pass


class ConditionalsFalseResult(InterruptCheck):
    pass


@dataclass
class Project:
    command: str
    config_path: str
    rootdir: str
    reporter_name: str
    color: bool
    reporter_format: t.Optional[str] = None

    def __post_init__(self) -> None:
        self.config = Config(self.config_path)
        self.tree = Tree(self.rootdir)
        self.reporter, self.reporter_name, self.reporter_format = get_reporter(
            self.reporter_name,
            self.color,
            self.rootdir,
            self.command,
        )

    def _check_files_existence(
        self,
        files: TreeNodeFiles,
        rule_index: int,
    ) -> None:
        for f, (fpath, fcontent) in enumerate(files):
            if fcontent is None:  # file or directory does not exist
                ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
                self.reporter.report_error(
                    {
                        "message": f"Expected existing {ftype} does not exists",
                        "file": fpath,
                        "definition": f"rules[{rule_index}].files[{f}]",
                    },
                )

    def _check_files_absence(
        self,
        files: t.Union[t.List[str], t.Dict[str, str]],
        rule_index: int,
    ):
        if isinstance(files, dict):
            for fpath, reason in files.items():
                normalized_fpath = os.path.join(self.rootdir, fpath)
                ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
                exists = (
                    os.path.isdir(normalized_fpath)
                    if ftype == "directory"
                    else os.path.isfile(normalized_fpath)
                )
                if exists:
                    message = f"Expected absent {ftype} exists"
                    if reason:
                        message += f". {reason}"
                    self.reporter.report_error(
                        {
                            "message": message,
                            "file": fpath,
                            "definition": f"rules[{rule_index}].files.not[{fpath}]",
                        },
                    )
        else:
            for f, fpath in enumerate(files):
                normalized_fpath = os.path.join(self.rootdir, fpath)
                ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
                exists = (
                    os.path.isdir(normalized_fpath)
                    if ftype == "directory"
                    else os.path.isfile(normalized_fpath)
                )
                if exists:
                    self.reporter.report_error(
                        {
                            "message": f"Expected absent {ftype} exists",
                            "file": fpath,
                            "definition": f"rules[{rule_index}].files.not[{f}]",
                        },
                    )

    def _process_conditionals_for_rule(
        self,
        conditionals: t.List[str],
        tree: Tree,
        rule: t.Any,  # TODO: improve this type
        rule_index: int,
    ) -> None:
        for conditional in conditionals:
            try:
                action_function = self.config.style.plugins.get_method_for_action(
                    conditional,
                )
            except InvalidPluginMethod as exc:
                self.reporter.report_error(
                    {
                        "message": exc.message,
                        "definition": f"rules[{rule_index}].{conditional}",
                        "file": None,
                    },
                )
                raise InterruptCheck()
            for breakage_type, breakage_value in action_function(
                rule[conditional],
                tree,
                rule,
            ):
                if breakage_type == InterruptingError:
                    breakage_value["definition"] = (
                        f"rules[{rule_index}]" + breakage_value["definition"]
                    )
                    self.reporter.report_error(breakage_value)
                    raise InterruptCheck()
                elif breakage_type == ResultValue:
                    if breakage_value is False:
                        raise ConditionalsFalseResult()
                    else:
                        break
                else:
                    raise NotImplementedError(
                        f"Breakage type '{breakage_type}' is not implemented"
                        " for conditionals checking",
                    )

    def _run_check(self) -> None:
        for r, rule in enumerate(self.config["style"]["rules"]):
            files = rule.pop("files")
            if isinstance(files, list):
                self.tree.cache_files(files)
                # check if files exists
                self._check_files_existence(self.tree.files, r)
            else:
                # requiring absent of files
                self._check_files_absence(files["not"], r)
                continue  # any other verb can be used in the rule

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
                try:
                    action_function = self.config.style.plugins.get_method_for_action(
                        verb,
                    )
                except InvalidPluginMethod as exc:
                    self.reporter.report_error(
                        {
                            "message": exc.message,
                            "definition": f"rules[{r}].{verb}",
                            "file": None,
                        },
                    )
                    raise InterruptCheck()
                    # TODO: show 'INTERRUPTED' in report
                for breakage_type, breakage_value in action_function(
                    rule[verb],
                    self.tree,
                    rule,
                ):
                    if breakage_type == Error:
                        # prepend rule index to definition, so plugins don't need to specify it
                        breakage_value["definition"] = (
                            f"rules[{r}]" + breakage_value["definition"]
                        )
                        self.reporter.report_error(breakage_value)
                    elif breakage_type == InterruptingError:
                        breakage_value["definition"] = (
                            f"rules[{r}]" + breakage_value["definition"]
                        )
                        self.reporter.report_error(breakage_value)
                        raise InterruptCheck()
                        # TODO: show 'INTERRUPTED' in report
                    else:
                        raise NotImplementedError(
                            f"Breakage type '{breakage_type}' is not implemented"
                            " for verbs checking",
                        )

    def check(self, args: t.List[t.Any]) -> None:
        try:
            self._run_check()
        except InterruptCheck:
            pass
        finally:
            self.reporter.raise_errors()

    def show(self, args: t.List[t.Any]) -> None:
        data = self.config.dict_
        if args.data == "config":
            data.pop("style")
            data["style"] = data.pop("_style")
        else:
            data = data.pop("style")

        try:
            report = self.reporter.generate_data_report(args.data, data)
        except NotImplementedError:
            raise reporter_not_implemented_error_factory(
                self.reporter_name,
                self.reporter_format,
                args.command,
            )
        sys.stdout.write(report)
