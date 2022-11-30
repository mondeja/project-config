"""High level logic for checking a project."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import typing as t
from dataclasses import dataclass

from project_config.config import Config
from project_config.constants import Error, InterruptingError, ResultValue
from project_config.fetchers import fetch
from project_config.plugins import InvalidPluginFunction, Plugins
from project_config.reporters import get_reporter
from project_config.serializers import (
    build_empty_file_for_serializer,
    guess_preferred_serializer,
)
from project_config.tree import Tree
from project_config.types import ActionsContext, Rule


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
        fix (bool): Fix errors.
    """

    config_path: str
    rootdir: str
    reporter_: t.Dict[str, t.Any]
    color: bool
    _actions_context: t.Optional[ActionsContext] = None
    fix: bool = False
    only_hints: bool = False

    def _load(
        self,
        fetch_styles: bool = True,
        init_tree: bool = True,
    ) -> None:
        self.config = Config(
            self.rootdir,
            self.config_path,
        )

        (
            self.color,
            self.reporter_,
            self.rootdir,
            config_only_hints,
        ) = self.config.guess_from_cli_arguments(
            self.color,
            self.reporter_,
            self.rootdir,
        )
        # TODO: Configure fix from config file

        if fetch_styles:
            self.config.load_style()

        if init_tree:
            self.tree = Tree(self.rootdir)

        self.reporter = get_reporter(
            self.reporter_["name"],
            self.reporter_["kwargs"],
            self.color,
            self.rootdir,
            only_hints=self.only_hints or config_only_hints,
        )

        # set rootdir as an internal environment variable to be used by plugins
        os.environ["PROJECT_CONFIG_ROOTDIR"] = self.rootdir

        self._actions_context = ActionsContext(fix=self.fix)

    def _check_files_existence(
        self,
        files: t.List[t.Tuple[str, t.Any]],
        rule_index: int,
    ) -> None:
        for f, (fpath, fcontent) in enumerate(files):
            ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"
            if fcontent is None:  # file or directory does not exist

                if self.fix:
                    if ftype == "directory":
                        os.makedirs(fpath, exist_ok=True)
                        self.tree.cache_files([fpath])
                    else:
                        _, serializer_name = guess_preferred_serializer(fpath)
                        new_content = (
                            ""
                            if not serializer_name
                            else build_empty_file_for_serializer(
                                serializer_name,
                            )
                        )
                        with open(fpath, "w", encoding="utf-8") as fd:
                            fd.write(new_content)
                        self.tree.cache_files([fpath])
                self.reporter.report_error(
                    {
                        "message": f"Expected existing {ftype} does not exists",
                        "file": fpath,
                        "definition": f"rules[{rule_index}].files[{f}]",
                        "fixed": self.fix,
                        "fixable": True,
                    },
                )

    def _check_files_absence(
        self,
        files: t.Union[t.List[str], t.Dict[str, str]],
        rule_index: int,
    ) -> None:
        fixed_files = []
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
                    if self.fix:
                        if ftype == "directory":
                            shutil.rmtree(normalized_fpath)
                        else:
                            os.remove(normalized_fpath)
                        fixed_files.append(fpath)

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
                            "fixed": self.fix,
                            "fixable": True,
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
                    if self.fix:
                        if ftype == "directory":
                            shutil.rmtree(normalized_fpath)
                        else:
                            os.remove(normalized_fpath)
                        fixed_files.append(fpath)
                    self.reporter.report_error(
                        {
                            "message": f"Expected absent {ftype} exists",
                            "file": fpath,
                            "definition": f"rules[{rule_index}].files.not[{f}]",
                            "fixed": self.fix,
                            "fixable": True,
                        },
                    )

        if fixed_files:
            self.tree.cache_files(fixed_files)

    def _process_conditionals_for_rule(
        self,
        conditionals: t.List[t.Tuple[str, t.Any]],
        tree: Tree,
        rule: Rule,
        rule_index: int,
    ) -> None:
        conditional_failed = False
        for conditional, action_function in conditionals:
            for breakage_type, breakage_value in action_function(
                # typed dict with dinamic key, this type must be ignored
                # until some literal quirk comes, see:
                # https://stackoverflow.com/a/59583427/9167585
                rule[conditional],  # type: ignore
                tree,
                rule,
                self._actions_context,
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
                    else:  # pragma: no cover
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
            hint = rule.pop("hint", None)
            files = rule.pop("files")

            verbs, conditionals_functions = [], []
            for action in rule:
                if action.startswith("if"):
                    try:
                        action_function = (
                            self.config.style.plugins.get_function_for_action(
                                action,
                            )
                        )
                    except InvalidPluginFunction as exc:
                        self.reporter.report_error(
                            {
                                "message": exc.message,
                                "definition": f"rules[{r}].{action}",
                            },
                        )
                        raise InterruptCheck()
                    conditionals_functions.append((action, action_function))
                else:
                    verbs.append(action)

            try:
                self._process_conditionals_for_rule(
                    conditionals_functions,
                    self.tree,
                    rule,
                    r,
                )
            except ConditionalsFalseResult:
                # conditionals skipping the rule, next...
                continue

            if isinstance(files, list):
                self.tree.cache_files(files)
                # check if files exists
                self._check_files_existence(self.tree.files, r)
            else:
                # requiring absent of files
                self._check_files_absence(files["not"], r)
                continue  # no other verb can be used in the rule

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
                    self._actions_context,
                ):
                    if breakage_type == Error:
                        # prepend rule index to definition, so plugins do not
                        # need to specify them
                        breakage_value["definition"] = (
                            f"rules[{r}]" + breakage_value["definition"]
                        )

                        if not self.fix:
                            breakage_value["fixed"] = False

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

    def check(self, args: argparse.Namespace) -> None:  # noqa: U100
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
        if args.data == "file":
            fmt = args.reporter.get("kwargs", {}).get("fmt", {})
            indent = (
                None if "pretty" not in fmt else (2 if fmt == "pretty" else 4)
            )
            data = fetch(args.file)
            report = json.dumps(data, indent=indent)
        elif args.data == "cache":
            from project_config.cache import Cache

            report = Cache.get_directory()
        else:
            if args.data == "config":
                self._load(fetch_styles=False, init_tree=False)
                data = self.config.dict_
                data.pop("cache")
                data["cache"] = data.pop("_cache")
            elif args.data == "plugins":
                self._load(fetch_styles=False, init_tree=False)
                data = Plugins(prepare_all=True).plugin_action_names
            else:  # style
                self._load(init_tree=False)
                data = self.config.dict_.pop("style")

            report = self.reporter.generate_data_report(args.data, data)

        sys.stdout.write(f"{report}\n")

    def clean(self, args: argparse.Namespace) -> None:  # noqa: U100
        """Cleaning command."""
        from project_config.cache import Cache

        if Cache.clean():
            sys.stdout.write("Cache removed successfully!\n")

    def init(self, args: argparse.Namespace) -> None:
        """Initialize the configuration for a project."""
        from project_config.config import initialize_config

        cwd = os.getcwd()
        rootdir = (
            cwd if getattr(args, "rootdir", None) is None else args.rootdir
        )
        config_path = initialize_config(
            os.path.join(
                rootdir,
                getattr(args, "config", None) or ".project-config.toml",
            ),
        )
        sys.stdout.write(
            "Configuration initialized at"
            f" {os.path.relpath(config_path, cwd)}\n",
        )
