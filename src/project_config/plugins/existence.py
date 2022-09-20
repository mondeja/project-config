"""Conditional files existence checker plugin."""

from __future__ import annotations

import os
import typing as t

from project_config import (
    ActionsContext,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)


class ExistencePlugin:
    @staticmethod
    def ifFilesExist(
        value: t.List[str],
        tree: Tree,
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
            return
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
            return

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
                continue
            normalized_fpath = tree.normalize_path(fpath)
            if fpath.endswith("/"):
                if not os.path.isdir(normalized_fpath):
                    yield ResultValue, False
            elif not os.path.isfile(normalized_fpath):
                yield ResultValue, False
