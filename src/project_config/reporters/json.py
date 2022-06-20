"""JSON reporters."""

import json
import typing as t

from project_config.reporters.base import BaseColorReporter, BaseReporter


class JsonReporter(BaseReporter):
    """Black/white reporter in JSON format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white JSON format."""
        return json.dumps(
            self.errors,
            indent=2
            if self.format == "pretty"
            else (4 if self.format == "pretty4" else None),
        )

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate a data report in black/white JSON format."""
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
    """Color reporter in JSON format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in JSON format with colors."""
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
                error_message = self.format_error_message(
                    json.dumps(error["message"]),
                )
                definition = self.format_definition(
                    json.dumps(error["definition"]),
                )
                report += (
                    f"{self.format_metachar('{')}{newline6}{message_key}:"
                    f" {error_message}"
                    f'{self.format_metachar(", ")}{newline6}'
                    f'{definition_key}{self.format_metachar(":")}'
                    f" {definition}"
                    f"{newline4}{self.format_metachar('}')}"
                )
                if e < len(errors) - 1:
                    report += f'{self.format_metachar(", ")}{newline4}'
            report += f"{newline2}{self.format_metachar(']')}"
            if f < len(self.errors) - 1:
                report += f'{self.format_metachar(", ")}{newline2}'

        return f"{report}{newline0}{self.format_metachar('}')}"

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate data report in JSON format with colors."""
        if not self.format:
            space = ""
            newline0 = newline2 = newline4 = newline6 = newline8 = ""
            newline10 = ""
        else:
            space = " " if self.format == "pretty" else "  "
            newline0 = "\n"
            newline2 = "\n" + space * 2
            newline4 = "\n" + space * 4
            newline6 = "\n" + space * 6
            newline8 = "\n" + space * 8
            newline10 = "\n" + space * 10

        report = f"{self.format_metachar('{')}{newline2}"
        if data_key == "config":
            for d, (key, value) in enumerate(data.items()):
                report += (
                    f"{self.format_config_key(json.dumps(key))}"
                    f'{self.format_metachar(":")}'
                )
                if isinstance(value, list):
                    report += f' {self.format_metachar("[")}{newline4}'
                    for i, value_item in enumerate(value):
                        report += self.format_config_value(
                            json.dumps(value_item),
                        )
                        if i < len(value) - 1:
                            report += f'{self.format_metachar(",")} {newline4}'
                        else:
                            report += f'{newline2}{self.format_metachar("]")}'
                else:
                    report += f" {self.format_config_value(json.dumps(value))}"

                if d < len(data) - 1:
                    report += f'{self.format_metachar(",")} {newline2}'
            report += f'{newline0}{self.format_metachar("}")}'
        else:
            plugins = data.pop("plugins", [])
            if plugins:
                report += (
                    f'{self.format_config_key(json.dumps("plugins"))}'
                    f'{self.format_metachar(":")}'
                    f'{space}{self.format_metachar("[")}{newline4}'
                )
                for p, plugin in enumerate(plugins):
                    report += f"{self.format_config_value(json.dumps(plugin))}"
                    if p < len(plugins) - 1:
                        report += f'{self.format_metachar(",")}{newline4}'
                report += f'{newline2}{self.format_metachar("],")}{newline2}'
            report += (
                f'{self.format_config_key(json.dumps("rules"))}'
                f'{self.format_metachar(":")}'
                f'{space}{self.format_metachar("[")}{newline4}'
            )
            rules = data.pop("rules")
            for r, rule in enumerate(rules):
                report += (
                    f'{self.format_metachar("{")}{newline6}'
                    f'{self.format_key(json.dumps("files"))}'
                    f'{self.format_metachar(":")}{space}'
                )
                files = rule.pop("files")
                if "not" in files and len(files) == 1:
                    report += (
                        f"{self.format_metachar('{')}{newline8}"
                        f"{self.format_key(json.dumps('not'))}"
                        f"{self.format_metachar(':')}{space}"
                    )
                    if isinstance(files["not"], list):
                        #  [...files...]
                        report += f'{self.format_metachar("[")} {newline10}'
                        for f, file in enumerate(files["not"]):
                            report += f"{self.format_file(json.dumps(file))}"
                            if f < len(files["not"]) - 1:
                                report += (
                                    f'{self.format_metachar(",")}{newline10}'
                                )
                            else:
                                report += (
                                    f'{newline8}{self.format_metachar("]")}'
                                )
                        report += f'{newline6}{self.format_metachar("}")}'
                    else:
                        # {file: reason}
                        report += f'{self.format_metachar("{")} {newline10}'
                        for f, (file, reason) in enumerate(
                            files["not"].items(),
                        ):
                            formatted_reason = self.format_config_value(
                                json.dumps(reason),
                            )
                            report += (
                                f"{self.format_file(json.dumps(file))}"
                                f'{self.format_metachar(":")}'
                                f"{space}{formatted_reason}"
                            )
                            if f < len(files["not"]) - 1:
                                report += (
                                    f'{self.format_metachar(",")}{newline10}'
                                )
                            else:
                                report += newline8
                        report += (
                            f'{self.format_metachar("}")}{space}{newline6}'
                            f'{self.format_metachar("}")}'
                        )
                else:
                    report += f"{self.format_metachar('[')}{newline8}"
                    for f, file in enumerate(files):
                        report += f"{self.format_file(json.dumps(file))}"
                        if f < len(files) - 1:
                            report += f'{self.format_metachar(",")}{newline8}'
                        else:
                            report += f'{newline6}{self.format_metachar("]")}'

                for rule_item_index, (key, value) in enumerate(rule.items()):
                    if rule_item_index == 0:
                        report += f'{self.format_metachar(",")}{newline6}'
                    indented_value = "\n".join(
                        ((space * 6 + line) if line_index > 0 else line)
                        for line_index, line in enumerate(
                            json.dumps(
                                value,
                                indent=None if not space else space * 2,
                            ).splitlines(),
                        )
                    )
                    report += (
                        f"{self.format_key(json.dumps(key))}"
                        f'{self.format_metachar(":")}'
                        f"{space}"
                        f"{self.format_config_value(indented_value)}"
                    )
                    if rule_item_index < len(rule) - 1:
                        report += f'{self.format_metachar(",")}{newline6}'

                report += f'{newline4}{self.format_metachar("}")}'
                if r < len(rules) - 1:
                    report += f'{self.format_metachar(",")}{newline4}'
            report += (
                f'{newline2}{self.format_metachar("]")}'
                f'{newline0}{self.format_metachar("}")}'
            )

        return report + "\n"
