"""project-config check command."""

from __future__ import annotations

import argparse
import os
import shutil
from typing import TYPE_CHECKING, Any

from contextlib_chdir import chdir as chdir_ctx

from project_config import tree
from project_config.config import Config, reporter_from_config
from project_config.constants import Error, InterruptingError, ResultValue
from project_config.plugins import InvalidPluginFunction
from project_config.serializers import (
    EMPTY_CONTENT_BY_SERIALIZER,
    guess_preferred_serializer,
)
from project_config.types import ActionsContext


if TYPE_CHECKING:
    from project_config.types import Rule


class InterruptCheck(Exception):
    """An action has reported an invalid context for a rule.

    This exceptions prevents to continue executing subsecuents rules.
    """


class ConditionalsFalseResult(InterruptCheck):
    """A conditional must skip a rule."""


class ProjectConfigChecker:
    """Project configuration checker.

    Args:
        config (:py:class:`project_config.config.Config`):
            Configuration to use.
        fix_mode (bool): Whether to fix the errors or not.
    """

    def __init__(self, config: Config, fix_mode: bool = False):
        self.config = config
        self.reporter = reporter_from_config(config)
        self.config.load_style()
        self.actions_context = ActionsContext(fix=fix_mode, files=[])

    def _check_files_existence(
        self,
        files: list[str],
        rule_index: int,
    ) -> None:
        for findex, fpath in enumerate(files):
            ftype = "directory" if fpath.endswith(("/", os.sep)) else "file"

            if ftype == "directory":
                exists = os.path.isdir(fpath)
            else:
                exists = os.path.isfile(fpath)

            if not exists:  # file or directory does not exist
                if self.actions_context.fix:
                    if ftype == "directory":
                        os.makedirs(fpath, exist_ok=True)
                    else:
                        _, serializer_name = guess_preferred_serializer(fpath)
                        new_content = (
                            ""
                            if not serializer_name
                            else EMPTY_CONTENT_BY_SERIALIZER.get(
                                serializer_name,
                                "",
                            )
                        )
                        with open(fpath, "w", encoding="utf-8") as fd:
                            fd.write(new_content)

                        # Cache the file.
                        #
                        # Serialization errors can't be raised here
                        # because the file is empty and created by the
                        # checker itself (see above)
                        tree.cache_file(
                            fpath,
                            forbid_serializers=("py",),
                        )
                self.reporter.report_error(
                    {
                        "message": f"Expected existing {ftype} does not exists",
                        "file": fpath,
                        "definition": f"rules[{rule_index}].files[{findex}]",
                        "fixed": self.actions_context.fix,
                        "fixable": True,
                    },
                )

    def _check_files_absence(
        self,
        files: list[str] | dict[str, str | int],
        rule_index: int,
    ) -> None:
        if isinstance(files, list):
            # i used for file index in the rule
            files = {fn: i for i, fn in enumerate(files)}
        else:
            files = files

        for fpath, reason_or_index in files.items():
            normalized_fpath = os.path.join(
                self.config.dict_["cli"]["rootdir"],
                fpath,
            )

            isdir = False
            if fpath.endswith("/"):
                isdir = True
                exists = os.path.isdir(normalized_fpath)
            else:
                exists = os.path.isfile(normalized_fpath)

            if exists:
                if self.actions_context.fix:
                    if isdir:
                        shutil.rmtree(normalized_fpath)
                    else:
                        os.remove(normalized_fpath)

                    # Take into account that this removal don't need
                    # to be cached as the digest of the file has been
                    # discarded

                message = (
                    f"Expected absent {'directory' if isdir else 'file'} exists"
                )
                if isinstance(reason_or_index, str):
                    message += f". {reason_or_index}"
                file_index = (
                    fpath
                    if isinstance(reason_or_index, str)
                    else reason_or_index
                )
                self.reporter.report_error(
                    {
                        "message": message,
                        "file": fpath,
                        "definition": (
                            f"rules[{rule_index}].files.not[{file_index}]"
                        ),
                        "fixed": self.actions_context.fix,
                        "fixable": True,
                    },
                )

    def _process_conditionals_for_rule(
        self,
        conditionals: list[tuple[str, Any]],
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
                rule,
                self.actions_context,
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
        for r, rule in enumerate(self.config.dict_["style"]["rules"]):
            hint = rule.pop("hint", None)
            files = rule.pop("files", [])

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
                    rule,
                    r,
                )
            except ConditionalsFalseResult:
                # conditionals skipping the rule, next...
                continue

            if isinstance(files, list):
                for file in files:
                    tree.cache_file(
                        file,
                        forbid_serializers=("py",),
                        ignore_serialization_errors=True,
                    )
                # check if files exists
                self._check_files_existence(files, r)
            else:
                # requiring absent of files
                self._check_files_absence(files["not"], r)
                continue  # no other verb can be used in the rule

            self.actions_context.files = files

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
                    # TODO: show 'INTERRUPTED' in report?
                for (breakage_type, breakage_value) in action_function(
                    rule[verb],  # type: ignore
                    rule,
                    self.actions_context,
                ):
                    if breakage_type == Error:
                        # prepend rule index to definition, so plugins do not
                        # need to specify them
                        #
                        # TODO: Currently the cast to ErrorDict is not available
                        # at runtime without installing typing_extensions,
                        # so we need to ignore the type here.
                        breakage_value[
                            "definition"
                        ] = f"rules[{r}]" + (  # type: ignore
                            breakage_value["definition"]  # type: ignore
                        )

                        if not self.actions_context.fix:
                            breakage_value["fixed"] = False  # type: ignore

                        # show hint if defined in the rule
                        if hint:
                            breakage_value["hint"] = hint  # type: ignore
                        self.reporter.report_error(breakage_value)

                    elif breakage_type == InterruptingError:
                        breakage_value[
                            "definition"
                        ] = f"rules[{r}]" + (  # type: ignore
                            breakage_value["definition"]  # type: ignore
                        )
                        self.reporter.report_error(breakage_value)
                        raise InterruptCheck()
                        # TODO: show 'INTERRUPTED' in report?
                    else:
                        raise NotImplementedError(
                            f"Breakage type '{breakage_type}' is not"
                            " implemented for verbal checking",
                        )

    def run(self) -> None:
        """Run the checker."""
        try:
            self._run_check()
        except InterruptCheck:
            pass
        finally:
            self.reporter.raise_errors()


def check(args: argparse.Namespace) -> None:  # noqa: U100
    """Checks that the styles configured for a project match.

    Raises errors if reported.
    """
    with chdir_ctx(args.rootdir):
        ProjectConfigChecker(
            Config(args),
            fix_mode=args.command == "fix",
        ).run()
