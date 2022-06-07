import argparse
import importlib
import sys
from typing import List, Type

from importlib_metadata_argparse_version import ImportlibMetadataVersionAction

from project_config.exceptions import ProjectConfigException


def add_check_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "check",
        help="Check the configuration of the project",
    )
    return parser


def add_fix_command_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "fix",
        help="Fix the configuration of the project",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the configuration of your project against the configured styles."
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

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )
    add_check_command_parser(subparsers)
    add_fix_command_parser(subparsers)
    return parser


def run(argv: List[str] = []) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        valid = getattr(
            importlib.import_module(f"project_config.commands.{args.command}"),
            args.command,
        )(args)
    except ProjectConfigException as exc:
        if args.traceback:
            raise
        sys.stderr.write(f"{exc.message}\n")
        return 1
    else:
        return 0 if valid else 1


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
