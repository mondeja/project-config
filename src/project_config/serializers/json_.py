"""JSON serializing."""

from __future__ import annotations

import json
import typing as t


def dumps(obj: t.Any, **kwargs: t.Any) -> str:  # noqa: D103
    return f"{json.dumps(obj, indent=2, **kwargs)}\n"


def loads(string: str, **kwargs: t.Any) -> t.Any:  # noqa: D103
    if string == "":
        string = "{}"
    return json.loads(string, **kwargs)
