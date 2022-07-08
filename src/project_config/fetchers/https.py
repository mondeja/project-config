"""HTTP/s resource URIs fetcher."""

from __future__ import annotations

import typing as t
import urllib.request

from project_config.utils.http import GET


def fetch(url_parts: urllib.parse.SplitResult, **kwargs: t.Any) -> str:
    """Fetch an HTTP/s resource performing a GET request."""
    return GET(url_parts.geturl(), **kwargs)
