"""TOML reporters."""

import typing as t

import tomlkit

from project_config.reporters.base import BaseColorReporter, BaseReporter


class TomlReporter(BaseReporter):
    """Black/white reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white TOML format."""
        return t.cast(str, tomlkit.dumps(self.errors))

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate a data report in black/white TOML format."""
        return t.cast(str, tomlkit.dumps(data))


class TomlColorReporter(BaseColorReporter):
    """Color reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in TOML format with colors."""
        report = ""
        for line in tomlkit.dumps(self.errors).split("\n"):
            if line.startswith("[["):
                report += (
                    f"{self.format_metachar('[[')}"
                    f"{self.format_file(line[2:-2])}"
                    f"{self.format_metachar(']]')}\n"
                )
            elif line.startswith("message = "):
                error_message = self.format_error_message(
                    line.split(" ", maxsplit=2)[2],
                )
                report += (
                    f"{self.format_key('message')}"
                    f" {self.format_metachar('=')}"
                    f" {error_message}\n"
                )
            elif line.startswith("definition = "):
                definition = self.format_definition(
                    line.split(" ", maxsplit=2)[2],
                )
                report += (
                    f"{self.format_key('definition')}"
                    f" {self.format_metachar('=')}"
                    f" {definition}\n"
                )
            else:
                report += f"{line}\n"
        return report.rstrip("\n")
