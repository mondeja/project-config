import json
import typing as t

from project_config.reporters.base import BaseColorReporter, BaseReporter


class JsonReporter(BaseReporter):
    def generate_errors_report(self) -> str:
        return json.dumps(
            self.errors,
            indent=2
            if self.format == "pretty"
            else (4 if self.format == "pretty4" else None),
        )

    def generate_data_report(self, data_key: str, data: t.Dict[str, t.Any]) -> str:
        return (
            json.dumps(
                data,
                indent=2
                if self.format == "pretty"
                else (4 if self.format == "pretty4" else None),
            )
            + "\n"
        )


class JsonColorReporter(BaseColorReporter):
    def generate_errors_report(self) -> str:
        message_key = self.format_key('"message"')
        definition_key = self.format_key('"definition"')

        # separators for pretty formatting
        if not self.format:
            newline0 = newline2 = newline4 = newline6 = ""
        else:
            space = " " if self.format == "pretty" else "  "
            newline0 = "\n"
            newline2 = "\n" + space * 2
            newline4 = "\n" + space * 4
            newline6 = "\n" + space * 6

        report = f"{self.format_metachar('{')}{newline2}"
        for f, (file, errors) in enumerate(self.errors.items()):
            report += (
                self.format_file(json.dumps(file))
                + self.format_metachar(": [")
                + newline4
            )
            for e, error in enumerate(errors):
                report += (
                    f"{self.format_metachar('{')}{newline6}{message_key}:"
                    f' {self.format_error_message(json.dumps(error["message"]))}'
                    f'{self.format_metachar(", ")}{newline6}'
                    f'{definition_key}{self.format_metachar(":")}'
                    f' {self.format_definition(json.dumps(error["definition"]))}'
                    f"{newline4}{self.format_metachar('}')}"
                )
                if e < len(errors) - 1:
                    report += f'{self.format_metachar(", ")}{newline4}'
            report += f"{newline2}{self.format_metachar(']')}"
            if f < len(self.errors) - 1:
                report += f'{self.format_metachar(", ")}{newline2}'

        return f"{report}{newline0}{self.format_metachar('}')}"
