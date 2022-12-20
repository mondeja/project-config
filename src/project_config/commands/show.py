"""project-config show command."""

from __future__ import annotations

import argparse
import json
import sys


def show(args: argparse.Namespace) -> None:
    """Show configuration or fetched style for a project.

    It will depend in the ``args.data`` property.
    """
    if args.data == "cache":
        from project_config.cache import CACHE_DIR as report
    elif args.data == "reporters":
        # TODO: Add tests for this
        from project_config.reporters import ThirdPartyReporters, reporters

        reporters_ids = list(reporters) + ThirdPartyReporters().ids
        report = ", ".join(
            [f"'{rep}'" for rep in reporters_ids],
        )
    else:
        if args.data == "file":
            from project_config.fetchers import fetch

            fmt = args.reporter.get("kwargs", {}).get("fmt", {})
            indent = (
                None if "pretty" not in fmt else (2 if fmt == "pretty" else 4)
            )
            data = fetch(args.file)
            report = json.dumps(data, indent=indent)
        else:
            from project_config.config import Config, reporter_from_config

            if args.data == "config":
                config = Config(args, store_raw_config=True)
                reporter = reporter_from_config(config)
                data = config.raw_
            else:
                config = Config(args)
                reporter = reporter_from_config(config)

                if args.data == "plugins":
                    from project_config.plugins import Plugins

                    data = Plugins(prepare_all=True).plugin_action_names
                else:  # style
                    config.load_style()
                    data = config.dict_.pop("style")

            report = reporter.generate_data_report(args.data, data)

    sys.stdout.write(f"{report}\n")
