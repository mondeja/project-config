"""Command line interface."""

import argparse
import os
import sys
import typing as t

from importlib_metadata_argparse_version import ImportlibMetadataVersionAction

from project_config.exceptions import ProjectConfigException
from project_config.project import Project
from project_config.reporters import reporters


def _controlled_error(
    show_traceback: bool,
    exc: Exception,
    message: str,
) -> int:
    if show_traceback:
        raise exc
    sys.stderr.write(f"{message}\n")
    return 1


def _add_check_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    subparsers.add_parser(
        "check",
        help="Check the configuration of the project",
        add_help=False,
    )


def _add_show_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser(
        "show",
        help="Show configuration or style.",
        add_help=False,
    )
    parser.add_argument(
        "data",
        choices=["config", "style"],
        help=(
            "Indicate which data must be shown, discovered configuration"
            " or extended style."
        ),
    )


def _add_clean_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser(
        "clean",
        help="Cleaning commands.",
        add_help=False,
    )
    parser.add_argument(
        "data",
        choices=["cache"],
        help=(
            "Indicate which data must be cleaned. Currently, only"
            " 'cache' is the possible data to clean."
        ),
    )


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
        choices=list(reporters),
        help="Style of generated report when failed.",
    )
    parser.add_argument(
        "--no-color",
        "--nocolor",
        dest="color",
        action="store_const",
        const=False,
        default=None,
        help=(
            "Disable colored output. You can also set a value in"
            " the environment variable NO_COLOR."
        ),
    )

    return parser


def _add_subparsers(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )
    _add_check_command_parser(subparsers)
    _add_show_command_parser(subparsers)
    _add_clean_command_parser(subparsers)


def run(argv: t.List[str] = []) -> int:  # noqa: D103
    parser = _build_main_parser()
    _add_subparsers(parser)
    args = parser.parse_args(argv)

    try:
        project = Project(
            args.command,
            args.config,
            args.rootdir,
            args.reporter,
            args.color,
        )
        getattr(project, args.command)(args)
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
