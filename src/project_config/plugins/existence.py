"""Conditional files existence checker plugin."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from project_config import ActionsContext, InterruptingError, ResultValue


if TYPE_CHECKING:
    from project_config import Results, Rule


class ExistencePlugin:
    @staticmethod
    def ifFilesExist(
        value: list[str],
        rule: Rule,  # noqa: U100
        context: ActionsContext,  # noqa: U100
    ) -> Results:
        if not isinstance(value, list):
            yield (
                InterruptingError,
                {
                    "message": (
                        "The files to check for existence"
                        " must be of type array"
                    ),
                    "definition": ".ifFilesExist",
                },
            )
        elif not value:
            yield (
                InterruptingError,
                {
                    "message": (
                        "The files to check for existence must not be empty"
                    ),
                    "definition": ".ifFilesExist",
                },
            )

        for f, fpath in enumerate(value):
            if not isinstance(fpath, str):
                yield (
                    InterruptingError,
                    {
                        "message": (
                            "The file to check for existence"
                            " must be of type string"
                        ),
                        "definition": f".ifFilesExist[{f}]",
                    },
                )
            if fpath.endswith("/"):
                if not os.path.isdir(fpath):
                    yield ResultValue, False
            elif not os.path.isfile(fpath):
                yield ResultValue, False
