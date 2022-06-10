import json
import typing as t

import yaml


try:
    from yaml import CSafeDumper as Dumper, CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader, SafeDumper as Dumper  # type: ignore

from project_config.reporters.base import BaseColorReporter, BaseReporter


class YamlReporterMixin:
    def dump_yaml_lines(self) -> t.List[str]:
        return yaml.dump(
            yaml.load(
                json.dumps(self.errors),
                Loader=Loader,
            ),
            Dumper=Dumper,
            default_flow_style=False,
            width=88888,  # no newlines in strings
        ).split("\n")


class YamlReporter(YamlReporterMixin, BaseReporter):
    def generate_report(self) -> str:
        report = ""
        for line in self.dump_yaml_lines():
            if line.startswith(("- ", "  ")):
                report += f"  {line}\n"
            else:
                report += f"{line}\n"
        return report


class YamlColorReporter(YamlReporterMixin, BaseColorReporter):
    def generate_report(self) -> t.Any:
        report = ""
        for line in self.dump_yaml_lines():
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
                report += f"{self.format_file(line)}\n"
        return report.rstrip("\n")
