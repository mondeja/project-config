import pprint
import typing as t

from project_config.reporters.base import (
    BaseColorReporter,
    BaseFormattedReporter,
    BaseNoopFormattedReporter,
)


class DefaultBaseReporter(BaseFormattedReporter):
    def generate_errors_report(self) -> str:
        report = ""
        for file, errors in self.errors.items():
            report += f"{self.format_file(file)}\n"
            for error in errors:
                report += (
                    f"  {self.format_error_message(error['message'].rstrip('.'))}"
                    f" {self.format_definition(error['definition'])}\n"
                )
        return report.rstrip("\n")

    def generate_data_report(self, data_key: str, data: t.Dict[str, t.Any]) -> str:
        report = ""

        if data_key == "config":
            for key, value in data.items():
                report += f'{self.format_config_key(key)}{self.format_metachar(":")}'
                if isinstance(value, list):
                    report += "\n"
                    for value_item in value:
                        report += f'  {self.format_metachar("-")} {self.format_config_value(value_item)}\n'
                else:
                    report += f" {self.format_config_value(value)}\n"
        else:
            plugins = data.pop("plugins", [])
            if plugins:
                report += (
                    f'{self.format_config_key("plugins")}{self.format_metachar(":")}\n'
                )
                for plugin in plugins:
                    report += f'  {self.format_metachar("-")} {self.format_config_value(plugin)}\n'

            report += f'{self.format_config_key("rules")}{self.format_metachar(":")}\n'
            for rule in data.pop("rules"):
                report += (
                    f'  {self.format_metachar("-")} {self.format_key("files")}'
                    f'{self.format_metachar(":")}\n'
                )
                for file in rule.pop("files"):
                    report += f"      {self.format_file(file)}\n"

                for key, value in rule.items():
                    report += (
                        f'    {self.format_key(key)}{self.format_metachar(":")} '
                        f"{self.format_config_value(pprint.pformat(value))}\n"
                    )

        return report


class DefaultReporter(BaseNoopFormattedReporter, DefaultBaseReporter):
    def format_error_message(self, error_message: str) -> str:
        return f"- {error_message}"


class DefaultColorReporter(BaseColorReporter, DefaultBaseReporter):
    def format_error_message(self, error_message: str) -> str:
        return (
            f"{super().format_metachar('-')}"
            f" {super().format_error_message(error_message)}"
        )
