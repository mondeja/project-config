"""TOML reporters."""

import json
import typing as t

import tomli_w

from project_config.reporters.base import (
    BaseColorReporter,
    BaseNoopFormattedReporter,
    FilesErrors,
    FormatterDefinitionType,
)


def _replace_nulls_by_repr_strings_in_dict(
    data: t.Dict[str, t.Any],
) -> t.Dict[str, t.Any]:
    """Iterates through a dictionary and replaces nulls by empty strings."""
    if isinstance(data, dict):
        return {
            key: _replace_nulls_by_repr_strings_in_dict(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [_replace_nulls_by_repr_strings_in_dict(value) for value in data]
    elif data is None:
        return "!!null"
    return data


def _normalize_indentation_to_2_spaces(string: str) -> str:
    """Normalizes indentation of the beginning of lines to 2 spaces."""
    new_lines: t.List[str] = []

    for line in string.splitlines():
        # count number of spaces at the beginning of the line
        spaces_at_start = len(line) - len(line.lstrip())
        if spaces_at_start < 3:
            new_lines.append(line)
        else:
            new_lines.append(f'{" " * int(spaces_at_start / 2)}{line.lstrip()}')

    return "\n".join(new_lines)


def _common_generate_errors_report(
    files_errors: FilesErrors,
    format_metachar: FormatterDefinitionType,
    format_file: FormatterDefinitionType,
    format_key: FormatterDefinitionType,
    format_error_message: FormatterDefinitionType,
    format_definition: FormatterDefinitionType,
    format_hint: FormatterDefinitionType,
) -> str:
    report = ""
    for file, errors in files_errors.items():
        report += (
            f"{format_metachar('[[')}{format_file(json.dumps(file))}"
            f"{format_metachar(']]')}\n"
        )

        for error in errors:
            report += (
                f"{format_key('message')} ="
                f" {format_error_message(json.dumps(error['message']))}\n"
                f"{format_key('definition')} ="
                f" {format_definition(json.dumps(error['definition']))}\n"
            )
            if "hint" in error:
                report += (
                    f"{format_key('hint')} ="
                    f" {format_hint(json.dumps(error['hint']))}\n"
                )
            report += "\n"
    return report.rstrip("\n")


class TomlReporter(BaseNoopFormattedReporter):
    """Black/white reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white TOML format."""
        return _common_generate_errors_report(
            self.errors,
            self.format_metachar,
            self.format_file,
            self.format_key,
            self.format_error_message,
            self.format_definition,
            self.format_hint,
        )

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate a data report in black/white TOML format."""
        report = ""
        if "plugins" in data:
            if not data["plugins"]:
                data.pop("plugins")
            elif len(data["plugins"]) == 1:
                plugin = data.pop("plugins")[0]
                report += f"plugins = [{json.dumps(plugin)}]\n\n"
        report += tomli_w.dumps(
            _replace_nulls_by_repr_strings_in_dict(data),
        )
        return _normalize_indentation_to_2_spaces(report)


class TomlColorReporter(BaseColorReporter):
    """Color reporter in TOML format."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in TOML format with colors."""
        return _common_generate_errors_report(
            self.errors,
            self.format_metachar,
            self.format_file,
            self.format_key,
            self.format_error_message,
            self.format_definition,
            self.format_hint,
        )

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
    ) -> str:
        """Generate data report in TOML format with colors."""
        report = ""
        if data_key == "config":
            report += (
                f'{self.format_config_key("cache")}'
                f' {self.format_metachar("=")}'
                f' {self.format_config_value(json.dumps(data["cache"]))}\n'
            )

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

            context = None
            for line in tomli_w.dumps(
                _replace_nulls_by_repr_strings_in_dict(data),
            ).splitlines():
                if not line:
                    report += "\n"
                elif line.startswith("[[") and line.endswith("]]"):
                    report += (
                        f"{self.format_metachar('[[')}"
                        f"{self.format_config_key(line[2:-2])}"
                        f"{self.format_metachar(']]')}\n"
                    )
                elif line.startswith("[") and line.endswith("]"):
                    points_after_rules = self.format_metachar(".").join(
                        [
                            self.format_key(action)
                            for action in line[1:-1].split(".")[1:]
                        ],
                    )
                    report += (
                        f"{self.format_metachar('[')}"
                        f"{self.format_config_key('rules')}"
                        f"{self.format_metachar('.')}"
                        f"{points_after_rules}"
                        f"{self.format_metachar(']')}\n"
                    )

                    actions_end = line.rstrip("]")
                    if actions_end.endswith(("files", "files.not")):
                        context = "files"
                    else:
                        context = "action"
                elif line.startswith("files ="):
                    report += (
                        f"{self.format_key('files')}"
                        f" {self.format_metachar('=')}"
                        f" {self.format_metachar(line[8:])}\n"
                    )
                    context = "files"
                elif line[0].isalpha():
                    key, value = line.split("=", maxsplit=1)
                    report += (
                        f"{self.format_key(key.strip())}"
                        f" {self.format_metachar('=')}"
                        f" {self.format_config_value(value.strip())}\n"
                    )
                    context = "action"
                elif not line.startswith("    "):
                    if len(line) == 1:  # end of action like ']'
                        formatter = (
                            self.format_metachar
                            if context == "files"
                            else self.format_config_value
                        )
                        report += f"{formatter(line)}\n"
                    else:
                        if context == "files":
                            # files: not
                            #
                            # file = reason
                            file, reason = line.split("=", maxsplit=1)
                            report += (
                                f"{self.format_file(file.strip())}"
                                f" {self.format_metachar('=')}"
                                f" {self.format_config_value(reason.strip())}\n"
                            )
                        else:
                            report += f"{self.format_config_value(line)}\n"
                elif context == "files":
                    indent = len(line) - len(line.lstrip())
                    report += (
                        f"{' ' * indent}"
                        f"{self.format_file(line[indent:-1])}"
                        f"{self.format_metachar(line[-1])}\n"
                    )
                else:  # context == "action"
                    indent = len(line) - len(line.lstrip())
                    report += (
                        f"{' ' * indent}"
                        f"{self.format_config_value(line[indent:])}\n"
                    )

        return _normalize_indentation_to_2_spaces(report)
