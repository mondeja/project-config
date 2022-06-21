"""High level logic for checking a project."""

import argparse
import os
import shutil
import sys
import typing as t
from dataclasses import dataclass

from project_config.config import Config
from project_config.constants import Error, InterruptingError, ResultValue
from project_config.plugins import InvalidPluginFunction
from project_config.reporters import ReporterNotImplementedError, get_reporter
from project_config.tree import Tree, TreeNodeFiles
from project_config.types import Rule


class InterruptCheck(Exception):
    """An action has reported an invalid context for a rule.

    This exceptions prevents to continue executing subsecuents rules.
    """


class ConditionalsFalseResult(InterruptCheck):
    """A conditional must skip a rule."""


@dataclass
class Project:
    """Wrapper for a single project.

    This class encapsulates all the high level logic to execute all
    CLI commands against a project.

    Its public method expose the commands that can be executed through
    the CLI.

    Args:
        command (str): Command that will be executed, used by the reporters.
        config_path (str): Custom configuration file path.
        rootdir (str): Root directory of the project.
        reporter_name (str): Reporter to use.
        color (bool): Colorized output in reporters.
        reporter_format (str): Additional format for reporter.
    """

    # TODO: don't pass command to reporters
    # TODO: refactor ``reporter_name`` -> ``reporter_id``
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
    ) -> None:
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
                            "file": f"{fpath}/"
                            if ftype == "directory"
                            else fpath,
                            "definition": (
                                f"rules[{rule_index}].files.not[{fpath}]"
                            ),
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
        rule: Rule,
        rule_index: int,
    ) -> None:
        for conditional in conditionals:
            try:
                action_function = (
                    self.config.style.plugins.get_function_for_action(
                        conditional,
                    )
                )
            except InvalidPluginFunction as exc:
                self.reporter.report_error(
                    {
                        "message": exc.message,
                        "definition": f"rules[{rule_index}].{conditional}",
                    },
                )
                raise InterruptCheck()
            for breakage_type, breakage_value in action_function(
                # typed dict with dinamic key, this type must be ignored
                # until some literal quirk comes, see:
                # https://stackoverflow.com/a/59583427/9167585
                rule[conditional],  # type: ignore
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
                    action_function = (
                        self.config.style.plugins.get_function_for_action(
                            verb,
                        )
                    )
                except InvalidPluginFunction as exc:
                    self.reporter.report_error(
                        {
                            "message": exc.message,
                            "definition": f"rules[{r}].{verb}",
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
                        # prepend rule index to definition, so plugins do not
                        # need to specify them
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
                            f"Breakage type '{breakage_type}' is not"
                            " implemented for verbal checking",
                        )

    def check(self, args: argparse.Namespace) -> None:
        """Checks that the styles configured for a project match.

        Raises an error if report errors.
        """
        try:
            self._run_check()
        except InterruptCheck:
            pass
        finally:
            self.reporter.raise_errors()

    def show(self, args: argparse.Namespace) -> None:
        """Show configuration or fetched style for a project.

        It will depend in the ``args.data`` property.
        """
        data = t.cast(t.Any, self.config.dict_)
        if args.data == "config":
            data.pop("style")
            data["style"] = data.pop("_style")
            data.pop("cache")
            data["cache"] = data.pop("_cache")
        else:
            data = data.pop("style")

        try:
            report = self.reporter.generate_data_report(args.data, data)
        except NotImplementedError:
            raise ReporterNotImplementedError.factory(
                self.reporter_name,
                self.reporter_format,
                args.command,
            )
        sys.stdout.write(report)

    def clean(self, args: argparse.Namespace) -> None:
        """Cleaning command."""
        from project_config.cache import _directory

        cache_directory = _directory()
        try:
            shutil.rmtree(cache_directory)
        except FileNotFoundError:
            pass
        finally:
            sys.stdout.write("Cache removed successfully!\n")
