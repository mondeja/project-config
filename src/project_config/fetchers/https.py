"""HTTP/s resource URIs fetcher."""

from __future__ import annotations

import urllib.request
from typing import Any

from project_config.utils.http import GET


def fetch(url_parts: urllib.parse.SplitResult, **kwargs: Any) -> Any:
    """Fetch an HTTP/s resource performing a GET request."""
    return GET(url_parts.geturl(), **kwargs)
