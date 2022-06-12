import json
import typing as t

import yaml


try:
    from yaml import CSafeDumper as Dumper
except ImportError:
    from yaml import SafeDumper as Dumper  # type: ignore

from project_config.reporters.base import BaseColorReporter, BaseReporter


def yaml_dump(obj: t.Any) -> t.Any:
    return yaml.dump(
        obj,
        Dumper=Dumper,
        default_flow_style=False,
        width=88888,  # no newlines in strings
    )


class YamlReporter(BaseReporter):
    def generate_errors_report(self) -> str:
        report = ""
        for line in yaml_dump(self.errors).split("\n"):
            if line.startswith(("- ", "  ")):
                report += f"  {line}\n"
            else:
                report += f"{line}\n"
        return report


class YamlColorReporter(BaseColorReporter):
    def generate_errors_report(self) -> t.Any:
        report = ""
        for line in yaml_dump(self.errors).split("\n"):
            if line.startswith("- "):  # definition
                report += (
                    f'  {self.format_metachar("-")}'
                    f' {self.format_key("definition")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_definition(line[15:])}\n"
                )
            elif line.startswith("  "):  # message
                report += (
                    f'  {self.format_metachar("-")}'
                    f' {self.format_key("message")}'
                    f'{self.format_metachar(":")}'
                    f" {self.format_error_message(line[11:])}\n"
                )
            elif line:
                report += (
                    f"{self.format_file(line[:-1])}" f"{self.format_metachar(':')}\n"
                )
        return report.rstrip("\n")
