"""project-config init command."""

from __future__ import annotations

import argparse
import os
import sys

from project_config.config import initialize_config


def init(args: argparse.Namespace) -> None:
    """Initialize the configuration for a project."""
    cwd = os.getcwd()
    rootdir = cwd if getattr(args, "rootdir", None) is None else args.rootdir
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
