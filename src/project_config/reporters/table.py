import typing as t

from tabulate import tabulate

from project_config.reporters.base import (
    BaseColorReporter,
    BaseNoopFormattedReporter,
)


def _common_generate_rows(
    errors: t.Dict[str, t.List[t.Dict[str, str]]],
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
                ]
            )
    return rows


def _common_generate_errors_report(
    errors: t.Dict[str, t.List[t.Dict[str, str]]],
    format: str,
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
        tablefmt=format,
    )


class TableReporter(BaseNoopFormattedReporter):
    def generate_errors_report(self) -> str:
        return _common_generate_errors_report(
            self.errors,
            t.cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
        )


class TableColorReporter(BaseColorReporter):
    def generate_errors_report(self) -> str:
        return _common_generate_errors_report(
            self.errors,
            t.cast(str, self.format),
            self.format_key,
            self.format_file,
            self.format_error_message,
            self.format_definition,
        )
