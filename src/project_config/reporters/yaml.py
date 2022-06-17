"""YAML reporters."""

import typing as t

from project_config.reporters.base import BaseColorReporter, BaseReporter
from project_config.serializers.yaml import dumps as yaml_dumps


class YamlReporter(BaseReporter):
    """Black/white reporter in YAML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white YAML format."""
        report = ""
        for line in yaml_dumps(self.errors).splitlines():
            if line.startswith(("- ", "  ")):
                report += f"  {line}\n"
            else:
                report += f"{line}\n"
        return report


class YamlColorReporter(BaseColorReporter):
    """Color reporter in YAML format."""

    def generate_errors_report(self) -> t.Any:
        """Generate an errors report in YAML format with colors."""
        report = ""
        for line in yaml_dumps(self.errors).splitlines():
            if line.startswith("- "):  # definition
                report += (
                    f'  {self.format_metachar("-")}'
                    f' {self.format_key("definition")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_definition(line[15:])}\n"
                )
            elif line.startswith("  "):  # message
                report += (
                    f"   "
                    f' {self.format_key("message")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_error_message(line[11:])}\n"
                )
            elif line:
                report += (
                    f"{self.format_file(line[:-1])}"
                    f"{self.format_metachar(':')}\n"
                )
        return report.rstrip("\n")
