import abc

import simple_chalk

from project_config.reporters.base import (
    BaseColorReporter,
    BaseFormattedReporter,
    BaseNoopFormattedReporter,
)


class DefaultBaseReporter(BaseFormattedReporter):
    def generate_report(self) -> str:
        report_message = ""
        for file, errors in self.errors.items():
            report_message += f"{self.format_file(file)}\n"
            for error in errors:
                report_message += (
                    f"  {self.format_error_message(error['message'].rstrip('.'))}"
                    f" {self.format_definition(error['definition'])}\n"
                )
        return report_message.rstrip("\n")


class DefaultReporter(BaseNoopFormattedReporter, DefaultBaseReporter):
    def format_error_message(self, error_message: str) -> str:
        return f"- {error_message}"


class DefaultColorReporter(BaseColorReporter, DefaultBaseReporter):
    def format_error_message(self, error_message: str) -> str:
        return simple_chalk.bold.yellow(f"- {error_message}")
