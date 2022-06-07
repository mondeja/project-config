import json
import os
import typing as t


def get(url: str) -> t.Any:
    path = os.path.expanduser(url)
    if os.path.isabs(path) and not path.startswith("file://"):
        path = "file://" + path.lstrip("/\\")

    with open(path) as f:
        return json.load(f)
