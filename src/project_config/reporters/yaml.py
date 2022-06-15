import typing as t

from project_config.decoders.yaml import dumps as yaml_dumps
from project_config.reporters.base import BaseColorReporter, BaseReporter


class YamlReporter(BaseReporter):
    def generate_errors_report(self) -> str:
        report = ""
        for line in yaml_dumps(self.errors).splitlines():
            if line.startswith(("- ", "  ")):
                report += f"  {line}\n"
            else:
                report += f"{line}\n"
        return report


class YamlColorReporter(BaseColorReporter):
    def generate_errors_report(self) -> t.Any:
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
                    f"{self.format_file(line[:-1])}" f"{self.format_metachar(':')}\n"
                )
        return report.rstrip("\n")
