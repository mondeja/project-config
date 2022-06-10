import typing as t

import tomlkit

from project_config.reporters.base import BaseColorReporter, BaseReporter


class TomlReporter(BaseReporter):
    def generate_report(self) -> str:
        return t.cast(str, tomlkit.dumps(self.errors))


class TomlColorReporter(BaseColorReporter):
    def generate_report(self) -> str:
        report = ""
        for line in tomlkit.dumps(self.errors).split("\n"):
            if line.startswith("[["):
                report += (
                    f"{self.format_metachar('[[')}"
                    f"{self.format_file(line[2:-2])}"
                    f"{self.format_metachar(']]')}\n"
                )
            elif line.startswith("message = "):
                report += (
                    f"{self.format_key('message')}"
                    f" {self.format_metachar('=')}"
                    f" {self.format_error_message(line.split(' ', maxsplit=2)[2])}\n"
                )
            elif line.startswith("definition = "):
                report += (
                    f"{self.format_key('definition')}"
                    f" {self.format_metachar('=')}"
                    f" {self.format_definition(line.split(' ', maxsplit=2)[2])}\n"
                )
            else:
                report += f"{line}\n"
        return report.rstrip("\n")
