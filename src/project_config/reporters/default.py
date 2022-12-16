"""Default reporters."""

from __future__ import annotations

import json
from typing import Any

from project_config.reporters.base import (
    BaseColorReporter,
    BaseFormattedReporter,
    BaseNoopFormattedReporter,
)


class BaseDefaultReporter(BaseFormattedReporter):
    """Base reporter for default reporters."""

    def generate_errors_report(self) -> str:
        """Generate errors report in custom project-config format."""
        report = ""
        for file, errors in self.errors.items():
            report += f"{self.format_file(file)}\n"
            for error in errors:
                fixed_prefix = (
                    "(FIXED) "
                    if error.get("fixed")
                    else ("(FIXABLE) " if error.get("fixable", False) else "")
                )
                error_message = (
                    f'{self.format_metachar("-")} '
                    f"{self.format_fixed(fixed_prefix)}"
                    f'{self.format_error_message(error["message"])}'
                )
                report += (
                    f"  {error_message}"
                    f" {self.format_definition(error['definition'])}"
                )
                if "hint" in error:
                    report += f" {self.format_hint(error['hint'])}"
                report += "\n"
        return report.rstrip("\n")

    def generate_data_report(
        self,
        data_key: str,
        data: dict[str, Any],
    ) -> str:
        """Generate data report in custom project-config format."""
        report = ""

        if data_key == "style":
            plugins = data.pop("plugins", [])
            if plugins:
                report += (
                    f'{self.format_config_key("plugins")}'
                    f'{self.format_metachar(":")}\n'
                )
                for plugin in plugins:
                    report += (
                        f'  {self.format_metachar("-")}'
                        f" {self.format_config_value(plugin)}\n"
                    )

            report += (
                f'{self.format_config_key("rules")}'
                f'{self.format_metachar(":")}\n'
            )
            for rule in data.pop("rules"):
                report += (
                    f'  {self.format_metachar("-")} {self.format_key("files")}'
                    f'{self.format_metachar(":")}\n'
                )
                files = rule.pop("files")
                if "not" in files and len(files) == 1:
                    report += f'      {self.format_key("not")}\n'
                    if isinstance(files["not"], dict):
                        for file, reason in files["not"].items():
                            report += (
                                "        "
                                f"{self.format_file(file)}"
                                f"{self.format_metachar(':')}"
                                f" {self.format_config_value(reason)}\n"
                            )
                    else:
                        for file in files["not"]:
                            report += (
                                f"        {self.format_metachar('-')}"
                                f" {self.format_file(file)}\n"
                            )
                else:
                    for file in files:
                        report += (
                            f"      {self.format_metachar('-')}"
                            f" {self.format_file(file)}\n"
                        )

                for key, value in rule.items():
                    indented_value = "\n".join(
                        " " * 6 + line
                        for line in json.dumps(value, indent=2).splitlines()
                    )
                    report += (
                        f"    {self.format_key(key)}"
                        f'{self.format_metachar(":")}'
                        f"\n{self.format_config_value(indented_value)}\n"
                    )
        else:  # config and plugins
            for key, value in data.items():
                report += (
                    f'{self.format_config_key(key)}{self.format_metachar(":")}'
                )
                if isinstance(value, list):
                    report += "\n"
                    for value_item in value:
                        report += (
                            f'  {self.format_metachar("-")}'
                            f" {self.format_config_value(value_item)}\n"
                        )
                else:
                    report += f" {self.format_config_value(value)}\n"

        return report.rstrip("\n")


class DefaultReporter(BaseNoopFormattedReporter, BaseDefaultReporter):
    """Default black/white reporter."""


class DefaultColorReporter(BaseColorReporter, BaseDefaultReporter):
    """Default color reporter."""
