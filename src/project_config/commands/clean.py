"""project-config clean command."""

from __future__ import annotations

import argparse
import sys

from project_config.cache import Cache


def clean(_args: argparse.Namespace) -> None:
    """Cache cleaning command."""
    Cache.clean()
    sys.stdout.write("Cache removed successfully!\n")
