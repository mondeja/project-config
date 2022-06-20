"""TOML reporters."""

import json
import typing as t

import tomli_w

from project_config.reporters.base import BaseColorReporter, BaseReporter


def _toml_dump_flow_style(obj: t.Any, indent: int = 0) -> str:
    result = ""
    if obj is None:
        result += (" " * indent) + '""'
    elif isinstance(obj, str):
        result += (" " * indent) + json.dumps(obj)
    elif isinstance(obj, list):
        # FIXME: error in arrays inside objects
        result += (" " * indent) + "[\n"
        for item in obj:
            result += _toml_dump_flow_style(item, indent=indent + 2) + ",\n"
        result += (" " * indent) + "],"
    elif isinstance(obj, dict):
        result += (" " * indent) + "{\n"
        for key, value in obj.items():
            result += (
                _toml_dump_flow_style(key, indent=indent + 2)
                + " = "
                + _toml_dump_flow_style(value, indent=indent + 2)
                + "\n"
            )
        result += (" " * indent) + "}\n"
    elif isinstance(obj, bool):
        result += (" " * indent) + ("true" if obj else "false")
    else:
        result += (" " * indent) + str(obj)
    return result.rstrip("\n").rstrip(",")


class TomlReporter(BaseReporter):
    """Black/white reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white TOML format."""
        return tomli_w.dumps(self.errors)  # type: ignore

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate a data report in black/white TOML format."""
        return tomli_w.dumps(data)  # type: ignore


class TomlColorReporter(BaseColorReporter):
    """Color reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in TOML format with colors."""
        report = ""
        for line in tomli_w.dumps(self.errors).splitlines():
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

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate data report in TOML format with colors."""
        report = ""
        if data_key == "config":
            report += (
                f"{self.format_config_key('style')}"
                f" {self.format_metachar('=')}"
            )
            if isinstance(data["style"], list):
                report += f' {self.format_metachar("[")}\n'
                for i, style in enumerate(data["style"]):
                    report += (
                        f"  {self.format_config_value(json.dumps(style))}"
                        f'{self.format_metachar(",")}\n'
                    )
                report += f'{self.format_metachar("]")}\n'
            else:
                report += (
                    f' {self.format_config_value(json.dumps(data["style"]))}\n'
                )

            report += (
                f'{self.format_config_key("cache")}'
                f' {self.format_metachar("=")}'
                f' {self.format_config_value(json.dumps(data["cache"]))}\n'
            )
        else:
            plugins = data.pop("plugins", [])
            if plugins:
                report += (
                    f'{self.format_config_key("plugins")}'
                    f' {self.format_metachar("=")} '
                )
                if len(plugins) == 1:
                    report += (
                        f'{self.format_metachar("[")}'
                        f"{self.format_config_value(json.dumps(plugins[0]))}"
                        f'{self.format_metachar("]")}'
                    )
                else:
                    report += f'{self.format_metachar("[")}\n'
                    for plugin in plugins:
                        report += (
                            f"  {self.format_config_value(json.dumps(plugin))}"
                            f'{self.format_metachar(",")}\n'
                        )
                    report += self.format_metachar("]")
                report += "\n\n"

            for rule in data.pop("rules"):
                report += (
                    f'{self.format_metachar("[[")}'
                    f'{self.format_config_key("rules")}'
                    f'{self.format_metachar("]]")}\n'
                )

                files = rule.pop("files")
                report += (
                    f'{self.format_key("files")} {self.format_metachar("=")} '
                )
                if "not" in files and len(files) == 1:
                    if isinstance(files["not"], dict):
                        report += f'{self.format_metachar("{")}\n'
                        for file, reason in files["not"].items():
                            json_reason = json.dumps(reason)
                            report += (
                                f"  {self.format_file(json.dumps(file))}"
                                f' {self.format_metachar("=")}'
                                f" {self.format_config_value(json_reason)}"
                                f'{self.format_metachar(",")}\n'
                            )
                        report += f'{self.format_metachar("}")}'
                    else:
                        report += f'{self.format_metachar("[")}\n'
                        for file in files["not"]:
                            report += (
                                f"  {self.format_file(json.dumps(file))}"
                                f'{self.format_metachar(",")}\n'
                            )
                        report += f'{self.format_metachar("]")}'
                else:
                    report += f'{self.format_metachar("[")}\n'
                    for file in files:
                        report += (
                            f"  {self.format_file(json.dumps(file))}"
                            f'{self.format_metachar(",")}\n'
                        )
                    report += f'{self.format_metachar("]")}'
                report += "\n"

                for action_index, (action_name, action_value) in enumerate(
                    rule.items(),
                ):
                    serialized_value = _toml_dump_flow_style(action_value)
                    report += (
                        f"{self.format_key(action_name)}"
                        f' {self.format_metachar("=")}'
                        f" {self.format_config_value(serialized_value)}"
                    )
                    if action_index < len(rule) - 1:
                        report += "\n"
                report += "\n"
                if rule:
                    report += "\n"

        return report
