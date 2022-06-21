"""Table reporters."""

import typing as t

from tabulate import tabulate

from project_config.reporters.base import (
    BaseColorReporter,
    BaseNoopFormattedReporter,
    FilesErrors,
)


def _common_generate_rows(
    errors: FilesErrors,
    format_file: t.Callable[[str], str],
    format_error_message: t.Callable[[str], str],
    format_definition: t.Callable[[str], str],
) -> t.List[t.List[str]]:
    rows = []
    for file, file_errors in errors.items():
        for i, error in enumerate(file_errors):
            rows.append(
                [
                    format_file(file) if i == 0 else "",
                    format_error_message(error["message"]),
                    format_definition(error["definition"]),
                ],
            )
    return rows


def _common_generate_errors_report(
    errors: FilesErrors,
    fmt: str,
    format_key: t.Callable[[str], str],
    format_file: t.Callable[[str], str],
    format_error_message: t.Callable[[str], str],
    format_definition: t.Callable[[str], str],
) -> str:
    return tabulate(
        _common_generate_rows(
            errors,
            format_file,
            format_error_message,
            format_definition,
        ),
        headers=[
            format_key("files"),
            format_key("message"),
            format_key("definition"),
        ],
        tablefmt=fmt,
    )


class TableReporter(BaseNoopFormattedReporter):
    """Black/white reporter in table formats."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in black/white table format."""
        return _common_generate_errors_report(
            self.errors,
            t.cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
        )


class TableColorReporter(BaseColorReporter):
    """Color reporter in table formats."""

    def generate_errors_report(self) -> str:
        """Generate an errors report in table format with colors."""
        return _common_generate_errors_report(
            self.errors,
            t.cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
        )
