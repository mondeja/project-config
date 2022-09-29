"""Command line interface."""

from __future__ import annotations

import argparse
import os
import sys
import typing as t
from gettext import gettext as _

from importlib_metadata_argparse_version import ImportlibMetadataVersionAction

from project_config.exceptions import ProjectConfigException
from project_config.project import Project
from project_config.reporters import POSSIBLE_REPORTER_IDS, parse_reporter_id


SPHINX_IS_RUNNING = "sphinx" in sys.modules
OPEN_QUOTE_CHAR = "”" if SPHINX_IS_RUNNING else '"'
CLOSE_QUOTE_CHAR = "”" if SPHINX_IS_RUNNING else '"'


class ReporterAction(argparse.Action):
    """Custom argparse action for reporter CLI option."""

    def _raise_invalid_reporter_error(self, reporter_id: str) -> None:
        raise argparse.ArgumentError(
            self,
            _("invalid choice: %(value)r (choose from %(choices)s)")
            % {
                "value": reporter_id,
                "choices": ", ".join(
                    [f"'{rep}'" for rep in POSSIBLE_REPORTER_IDS],
                ),
            },
        )

    def __call__(  # type: ignore  # noqa: D102
        self,
        parser: argparse.ArgumentParser,  # noqa: U100
        namespace: argparse.Namespace,
        value: str,
        option_string: str,  # noqa: U100
    ) -> None:
        reporter: t.Dict[str, t.Any] = {}
        if value:

            try:
                reporter_name, reporter_kwargs = parse_reporter_id(value)
            except Exception:
                self._raise_invalid_reporter_error(value)
            reporter_id = reporter_name
            if reporter_kwargs["fmt"]:
                reporter_id += f':{reporter_kwargs["fmt"]}'

            if reporter_id not in POSSIBLE_REPORTER_IDS:
                self._raise_invalid_reporter_error(reporter_id)
            reporter["name"] = reporter_name
            reporter["kwargs"] = reporter_kwargs

        namespace.reporter = reporter


def _controlled_error(
    show_traceback: bool,
    exc: Exception,
    message: str,
) -> int:
    if show_traceback:
        raise exc
    sys.stderr.write(f"{message}\n")
    return 1


def build_main_parser() -> argparse.ArgumentParser:  # noqa: D103
    parser = argparse.ArgumentParser(
        description=(
            "Validate the configuration of your project against the"
            " configured styles."
        ),
        prog="project-config",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show project-config's help and exit.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action=ImportlibMetadataVersionAction,
        help="Show project-config's version number and exit.",
        importlib_metadata_version_from="project-config",
    )

    # common arguments
    parser.add_argument(
        "-T",
        "--traceback",
        action="store_true",
        help=(
            "Display the full traceback when a exception is found."
            " Useful for debugging purposes."
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Custom configuration file path.",
    )
    parser.add_argument(
        "--root",
        "--rootdir",
        dest="rootdir",
        type=str,
        help=(
            "Root directory of the project. Useful if you want to"
            " execute project-config for another project rather than the"
            " current working directory."
        ),
    )
    possible_reporters_msg = ", ".join(
        [f"'{rep}'" for rep in POSSIBLE_REPORTER_IDS],
    )
    example = (
        f"{OPEN_QUOTE_CHAR}file{CLOSE_QUOTE_CHAR}:"
        f"{OPEN_QUOTE_CHAR}blue{CLOSE_QUOTE_CHAR}"
    )
    parser.add_argument(
        "-r",
        "--reporter",
        action=ReporterAction,
        default={},
        metavar="NAME[:FORMAT];OPTION=VALUE",
        help=(
            "Reporter for generated output when failed. Possible values"
            f" are {possible_reporters_msg}. Additionally, options can be"
            " passed to the reporter appending ';' to the end of the reporter"
            " id with the syntax '<OPTION>=<JSON VALUE>'. Console reporters can"
            " take an argument 'color' which accepts a JSON object to customize"
            " the colors for parts of the report like files, for example:"
            " table:simple;colors={%s}." % example
        ),
    )
    parser.add_argument(
        "--no-color",
        "--nocolor",
        dest="color",
        action="store_false",
        help=(
            "Disable colored output. You can also set a value in"
            " the environment variable NO_COLOR."
        ),
    )
    parser.add_argument(
        "--no-cache",
        "--nocache",
        dest="cache",
        action="store_false",
        help=(
            "Disable cache for the current execution. You can also set"
            " the value 'false' in the environment variable"
            " PROJECT_CONFIG_USE_CACHE."
        ),
    )
    parser.add_argument(
        "--only-hints",
        dest="only_hints",
        action="store_true",
        help=("Only show the hint messages rather than complete errors."),
    )
    parser.add_argument(
        "command",
        choices=["check", "fix", "show", "clean", "init"],
        help="Command to execute.",
    )

    return parser


def _parse_command_args(
    command: str,
    subcommand_args: t.List[str],
) -> t.Tuple[argparse.Namespace, t.List[str]]:
    if command in ("show", "clean"):
        if command == "show":
            parser = argparse.ArgumentParser(prog="project-config show")
            parser.add_argument(
                "data",
                choices=["config", "style", "cache", "plugins", "file"],
                help=(
                    "Indicate which data must be shown, discovered"
                    " configuration (config), extended style (style),"
                    " cache directory location (cache), plugins with"
                    " their actions (plugins) or a file as a"
                    " serialized object (file <path>)."
                ),
            )
            args, remaining = parser.parse_known_args(subcommand_args)
            if args.data == "file":
                parser = argparse.ArgumentParser(
                    prog="project-config show file",
                )
                parser.add_argument(
                    "file",
                    type=str,
                    help=(
                        "File to deserialize and show. This is useful for"
                        " debugging purposes."
                    ),
                )
                subargs, remaining = parser.parse_known_args(remaining)
                args.__dict__.update(subargs.__dict__)
        else:  # command == "clean"
            parser = argparse.ArgumentParser(prog="project-config clean")
            parser.add_argument(
                "data",
                choices=["cache"],
                help=(
                    "Indicate which data must be cleaned. Currently, only"
                    " 'cache' is the possible data to clean."
                ),
            )
            args, remaining = parser.parse_known_args(subcommand_args)

    else:
        args = argparse.Namespace()
        remaining = subcommand_args
    return args, remaining


def parse_cli_args_and_subargs(  # noqa: D103
    parser: argparse.ArgumentParser,
    argv: t.List[str],
) -> t.Tuple[argparse.Namespace, argparse.Namespace]:
    args, subcommand_args = parser.parse_known_args(argv)
    subargs, remaining = _parse_command_args(args.command, subcommand_args)
    if remaining:
        parser.print_help()
        raise SystemExit(1)
    return args, subargs


def parse_args(argv: t.List[str]) -> argparse.Namespace:  # noqa: D103
    args, subargs = parse_cli_args_and_subargs(build_main_parser(), argv)

    if args.cache is False:
        os.environ["PROJECT_CONFIG_USE_CACHE"] = "false"

    return argparse.Namespace(**vars(args), **vars(subargs))


def run(argv: t.List[str]) -> int:  # noqa: D103
    os.environ["PROJECT_CONFIG"] = "true"
    args = parse_args(argv)

    try:
        project = Project(
            args.config,
            args.rootdir,
            args.reporter,
            args.color,
            fix=args.command == "fix",
            only_hints=args.only_hints,
        )
        method_name = "check" if args.command == "fix" else args.command
        getattr(project, method_name)(args)
    except ProjectConfigException as exc:
        return _controlled_error(args.traceback, exc, exc.message)
    except FileNotFoundError as exc:  # pragma: no cover
        return _controlled_error(
            args.traceback,
            exc,
            f"{exc.args[1]} '{exc.filename}'",
        )
    return 0


def main() -> None:  # noqa: D103  # pragma: no cover
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
