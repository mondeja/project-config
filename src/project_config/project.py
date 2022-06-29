"""High level logic for checking a project."""

import argparse
import os
import sys
import typing as t
from dataclasses import dataclass

from project_config.config import Config
from project_config.constants import Error, InterruptingError, ResultValue
from project_config.exceptions import ProjectConfigException
from project_config.plugins import InvalidPluginFunction, Plugins
from project_config.reporters import DEFAULT_REPORTER, get_reporter
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
        config_path (str): Custom configuration file path.
        rootdir (str): Root directory of the project.
        reporter_ (dict): Reporter to use.
        color (bool): Colorized output in reporters.
    """

    config_path: str
    rootdir: str
    reporter_: t.Dict[str, t.Any]
    color: bool

    def _load(
        self,
        fetch_styles: bool = True,
        tree: bool = True,
    ) -> None:
        self.config = Config(
            self.rootdir,
            self.config_path,
            fetch_styles=fetch_styles,
        )

        self.color = (
            self.config.cli.get("color")  # type: ignore
            if self.color is True
            else self.color
        )

        reporter_kwargs = self.reporter_.get("kwargs", {})
        reporter_id = self.reporter_.get(
            "name",
            self.config.cli.get("reporter", DEFAULT_REPORTER),
        )
        if ":" in reporter_id:
            self.reporter_["name"], reporter_kwargs["fmt"] = reporter_id.split(
                ":",
                maxsplit=1,
            )
        else:
            self.reporter_["name"] = reporter_id

        if self.color in (True, None):
            if "colors" in self.config.cli:
                colors = self.config.cli.get("colors", {})
                for key, value in reporter_kwargs.get("colors", {}).items():
                    colors[key] = value  # cli overrides config
                reporter_kwargs["colors"] = colors
            self.reporter_["kwargs"] = reporter_kwargs
        else:
            self.reporter_["kwargs"] = reporter_kwargs

        if not self.rootdir:
            self.rootdir = self.config.cli.get("rootdir")  # type: ignore
            if self.rootdir:
                self.rootdir = os.path.expanduser(self.rootdir)
            else:
                self.rootdir = os.getcwd()
        else:
            self.rootdir = os.path.abspath(self.rootdir)

        if not os.path.isdir(self.rootdir):
            raise ProjectConfigException(
                f"Root directory '{self.rootdir}' must be an"
                " existing directory",
            )

        if tree:
            self.tree = Tree(self.rootdir)

        self.reporter = get_reporter(
            self.reporter_["name"],
            self.reporter_["kwargs"],
            self.color,
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
        conditional_failed = False
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
                if breakage_type in (InterruptingError, Error):
                    breakage_value["definition"] = (
                        f"rules[{rule_index}]" + breakage_value["definition"]
                    )
                    self.reporter.report_error(breakage_value)
                    conditional_failed = True
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
        if conditional_failed:
            raise InterruptCheck()

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

            hint = rule.pop("hint", None)

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
                        # show hint if defined in the rule
                        if hint:
                            breakage_value["hint"] = hint
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
        self._load()
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
        if args.data == "cache":
            from project_config.cache import Cache

            report = Cache.get_directory()
        else:
            if args.data == "config":
                self._load(fetch_styles=False, tree=False)
                data = self.config.dict_
                data.pop("cache")
                data["cache"] = data.pop("_cache")
            elif args.data == "plugins":
                self._load(fetch_styles=False, tree=False)
                data = Plugins(  # type: ignore
                    prepare_all=True,
                ).plugin_action_names
            else:  # style
                self._load(tree=False)
                data = self.config.dict_.pop("style")  # type: ignore

            report = self.reporter.generate_data_report(args.data, data)

        sys.stdout.write(f"{report}\n")

    def clean(self, args: argparse.Namespace) -> None:
        """Cleaning command."""
        from project_config.cache import Cache

        if Cache.clean():
            sys.stdout.write("Cache removed successfully!\n")
