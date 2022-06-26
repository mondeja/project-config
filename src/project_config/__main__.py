"""Command line interface."""

import argparse
import os
import sys
import typing as t

from importlib_metadata_argparse_version import ImportlibMetadataVersionAction

from project_config.exceptions import ProjectConfigException
from project_config.project import Project
from project_config.reporters import ThirdPartyReporters, reporters


def _controlled_error(
    show_traceback: bool,
    exc: Exception,
    message: str,
) -> int:
    if show_traceback:
        raise exc
    sys.stderr.write(f"{message}\n")
    return 1


def _build_main_parser() -> argparse.ArgumentParser:
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
        default=os.getcwd(),
    )
    parser.add_argument(
        "-r",
        "--reporter",
        dest="reporter",
        default="default",
        choices=list(reporters) + ThirdPartyReporters().ids,
        help="Style of generated report when failed.",
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
        "command",
        choices=["check", "show", "clean"],
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
                choices=["config", "style", "cache"],
                help=(
                    "Indicate which data must be shown, discovered"
                    " configuration, extended style or cache directory"
                    " location."
                ),
            )
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


def run(argv: t.List[str] = []) -> int:  # noqa: D103
    os.environ["PROJECT_CONFIG"] = "true"
    parser = _build_main_parser()
    args, subcommand_args = parser.parse_known_args(argv)
    subargs, remaining = _parse_command_args(args.command, subcommand_args)
    if remaining:
        parser.print_help()
        return 1

    try:
        project = Project(
            args.config,
            args.rootdir,
            args.reporter,
            args.color,
        )
        getattr(project, args.command)(subargs)
    except ProjectConfigException as exc:
        return _controlled_error(args.traceback, exc, exc.message)
    except FileNotFoundError as exc:
        return _controlled_error(
            args.traceback,
            exc,
            f"{exc.args[1]} '{exc.filename}'",
        )
    return 0


def main() -> None:  # noqa: D103
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
