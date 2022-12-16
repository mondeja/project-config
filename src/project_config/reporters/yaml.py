"""YAML reporters."""

from __future__ import annotations

from typing import Any

from project_config.reporters.base import BaseColorReporter, BaseReporter
from project_config.serializers import yaml


class YamlReporter(BaseReporter):
    """Black/white reporter in YAML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white YAML format."""
        if not self.errors:
            return ""

        return yaml.dumps(self.errors).rstrip("\n")

    def generate_data_report(
        self,
        data_key: str,  # noqa: U100
        data: dict[str, Any],
    ) -> str:
        """Generate a data report in black/white JSON format."""
        report = yaml.dumps(data)
        if report.startswith("plugins: []"):
            report = "\n".join(report.splitlines()[1:])
        return report.rstrip("\n")


class YamlColorReporter(BaseColorReporter):
    """Color reporter in YAML format."""

    def _transform_errors(self, value: str) -> str:
        report = ""
        for line in value.splitlines():
            if line.startswith("  - "):  # definition
                report += (
                    f'  {self.format_metachar("-")}'
                    f' {self.format_key("definition")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_definition(line[16:])}\n"
                )
            elif line.startswith("    message"):  # message
                report += (
                    f"   "
                    f' {self.format_key("message")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_error_message(line[13:])}\n"
                )
            elif line.startswith("    hint"):  # hint
                report += (
                    f"   "
                    f' {self.format_key("hint")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_hint(line[10:])}\n"
                )
            elif line.startswith("    fixed"):  # hint
                report += (
                    f"   "
                    f' {self.format_key("fixed")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_fixed('true')}\n"
                )
            elif line.startswith("    fixable"):  # hint
                report += (
                    f"   "
                    f' {self.format_key("fixable")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_fixed('true')}\n"
                )
            elif line:
                report += (
                    f"{self.format_file(line[:-1])}"
                    f"{self.format_metachar(':')}\n"
                )
        return report.rstrip("\n")

    def generate_errors_report(self) -> Any:
        """Generate an errors report in YAML format with colors."""
        if not self.errors:
            return ""

        return yaml.dumps(self.errors, transform=self._transform_errors)

    def _transform_config_data(self, value: str) -> str:
        report = ""
        for line in value.splitlines():
            if line.startswith("  - "):
                report += (
                    f'  {self.format_metachar("-")}'
                    f" {self.format_config_value(line[4:].strip())}"
                )
            else:
                # key: value
                key, value = line.split(":", maxsplit=1)
                report += (
                    f"{self.format_config_key(key)}"
                    f"{self.format_metachar(':')}"
                    f" {self.format_config_value(value.strip())}"
                ).rstrip()
            report += "\n"
        return report.rstrip("\n")

    _transform_plugins_data = _transform_config_data

    def _transform_style_data(self, value: str) -> str:
        report = ""

        section, subsection = None, None

        def format_section(section_name: str) -> str:
            return (
                f"{self.format_config_key(section_name)}"
                f"{self.format_metachar(':')}"
            )

        for line in value.splitlines():
            if line.startswith("plugins:"):
                if line.endswith("[]"):
                    continue
                else:
                    report += format_section("plugins")
                    section = "plugins"
            elif line.startswith("rules:"):
                report += format_section("rules")
                section = "rules"
            elif section == "plugins":
                report += (
                    f'  {self.format_metachar("-")}'
                    f" {self.format_config_value(line[4:].strip())}"
                )
            elif section == "rules":
                if line.startswith("  - "):  # files or action
                    report += (
                        f'  {self.format_metachar("-")}'
                        f" {self.format_key(line[4:-1])}"
                        f'{self.format_metachar(":")}'
                    )
                    subsection = (
                        "files" if line.endswith("files:") else "action"
                    )
                elif line.startswith("      "):  # subsection
                    if subsection == "files":
                        if line == "      not:":
                            report += (
                                f"      {self.format_key('not')}"
                                f"{self.format_metachar(':')}"
                            )
                        elif line.lstrip().startswith("- "):  # file
                            offset, file = line.split("-", maxsplit=1)
                            report += (
                                f"{offset}{self.format_metachar('-')}"
                                f" {self.format_file(file.strip())}"
                            )
                        else:  # not: file
                            report += (
                                f"        {self.format_file(line.strip())}"
                            )
                    else:
                        # actions
                        report += self.format_config_value(line)
                elif line.startswith("    "):
                    report += (
                        f"    {self.format_key(line[4:-1])}"
                        f'{self.format_metachar(":")}'
                    )
                    subsection = (
                        "files" if line.endswith("files:") else "action"
                    )
            report += "\n"
        return report.rstrip("\n")

    def generate_data_report(
        self,
        data_key: str,
        data: dict[str, Any],
    ) -> str:
        """Generate a data report in color YAML format."""
        return yaml.dumps(
            data,
            transform=getattr(self, f"_transform_{data_key}_data"),
        )
