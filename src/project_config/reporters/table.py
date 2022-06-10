import typing as t

from tabulate import tabulate

from project_config.reporters.base import (
    BaseColorReporter,
    BaseNoopFormattedReporter,
)


class TableReporterMixin:
    def generate_rows(self) -> t.List[t.List[str]]:
        rows = []
        for file, errors in self.errors.items():
            for (
                i,
                error,
            ) in enumerate(errors):
                rows.append(
                    [
                        self.format_file(file) if i == 0 else "",
                        self.format_error_message(error["message"]),
                        self.format_definition(error["definition"]),
                    ]
                )
        return rows

    def generate_report(self) -> str:
        return tabulate(
            self.generate_rows(),
            headers=[
                self.format_key("files"),
                self.format_key("message"),
                self.format_key("definition"),
            ],
            tablefmt=self.format,
        )


class TableReporter(
    TableReporterMixin,
    BaseNoopFormattedReporter,
):
    pass


class TableColorReporter(
    TableReporterMixin,
    BaseColorReporter,
):
    pass
