"""Table reporters."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from tabulate import tabulate

from project_config.reporters.base import (
    BaseColorReporter,
    BaseNoopFormattedReporter,
)


if TYPE_CHECKING:
    from project_config.reporters.base import (
        FilesErrors,
        FormatterDefinitionType,
    )


def _common_generate_rows(
    errors: FilesErrors,
    format_file: FormatterDefinitionType,
    format_error_message: FormatterDefinitionType,
    format_definition: FormatterDefinitionType,
    format_hint: FormatterDefinitionType,
) -> list[list[str]]:
    rows = []
    for file, file_errors in errors.items():
        for i, error in enumerate(file_errors):
            rows.append(
                [
                    format_file(file) if i == 0 else "",
                    format_error_message(error["message"]),
                    format_definition(error["definition"]),
                    format_hint(error.get("hint", "")),
                ],
            )
    return rows


def _common_generate_errors_report(
    errors: FilesErrors,
    fmt: str,
    format_key: FormatterDefinitionType,
    format_file: FormatterDefinitionType,
    format_error_message: FormatterDefinitionType,
    format_definition: FormatterDefinitionType,
    format_hint: FormatterDefinitionType,
) -> str:
    return tabulate(
        _common_generate_rows(
            errors,
            format_file,
            format_error_message,
            format_definition,
            format_hint,
        ),
        headers=[
            format_key("files"),
            format_key("message"),
            format_key("definition"),
            format_key("hint"),
        ],
        tablefmt=fmt,
    )


class TableReporter(BaseNoopFormattedReporter):
    """Black/white reporter in table formats."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white table format."""
        return _common_generate_errors_report(
            self.errors,
            cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
            self.format_hint,
        ).rstrip("\n")


class TableColorReporter(BaseColorReporter):
    """Color reporter in table formats."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in table format with colors."""
        return _common_generate_errors_report(
            self.errors,
            cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
            self.format_hint,
        ).rstrip("\n")
