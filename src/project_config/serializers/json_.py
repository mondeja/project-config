"""JSON serializing."""

from __future__ import annotations

import json
from typing import Any


def dumps(obj: Any, **kwargs: Any) -> str:  # noqa: D103
    return f"{json.dumps(obj, indent=2, **kwargs)}\n"


loads = json.loads
