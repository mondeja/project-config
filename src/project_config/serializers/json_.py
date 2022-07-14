"""JSON serializing."""

from __future__ import annotations

import json
import typing as t


def dumps(obj: t.Any, **kwargs: t.Any) -> str:  # noqa: D103
    return f"{json.dumps(obj, indent=2, **kwargs)}\n"


loads = json.loads
