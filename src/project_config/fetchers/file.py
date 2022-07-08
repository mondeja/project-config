"""Local resource URIs fetcher."""

from __future__ import annotations

import os
import urllib.parse


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    """Fetch a file, just read it from filesystem."""
    with open(os.path.expanduser(url_parts.geturl()), encoding="utf-8") as f:
        return f.read()
