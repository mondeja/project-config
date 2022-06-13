import argparse
import os
import sys
import typing as t

from importlib_metadata_argparse_version import ImportlibMetadataVersionAction

from project_config.exceptions import ProjectConfigException
from project_config.project import Project
from project_config.reporters import reporters


def controlled_error(show_traceback: bool, exc: Exception, message: str) -> int:
    if show_traceback:
        raise exc
    sys.stderr.write(f"{message}\n")
    return 1


def add_check_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "check",
        help="Check the configuration of the project",
    )
    return parser


def add_show_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("show", help="Show configuration or style.")
    parser.add_argument(
        "data",
        choices=["config", "style"],
        help="Indicate which data must be shown, discovered configuration or extended style.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the configuration of your project against the configured styles.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action=ImportlibMetadataVersionAction,
        importlib_metadata_version_from="project-config",
    )

    # common arguments
    parser.add_argument(
        "-T",
        "--traceback",
        action="store_true",
        help="Display the full traceback when a exception is found. Useful for debugging purposes.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Custom configuration file path. As default is read from .project-config.toml or pyproject.toml",
    )
    parser.add_argument(
        "--root",
        "--rootdir",
        dest="rootdir",
        type=str,
        help="Root directory of the project. Useful if you want to execute project-config for another project rather than the current working directory.",
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

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )
    add_check_command_parser(subparsers)
    add_show_command_parser(subparsers)
    return parser


def run(argv: t.List[str] = []) -> int:
    parser = build_parser()
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
        return controlled_error(args.traceback, exc, exc.message)
    except FileNotFoundError as exc:
        return controlled_error(args.traceback, exc, f"{exc.args[1]} '{exc.filename}'")
    return 0


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
