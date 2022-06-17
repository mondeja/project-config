"""HTTP/s resource URIs fetcher."""

import urllib.request

from project_config.utils import GET


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    """Fetch an HTTP/s resource performing a GET request."""
    return GET(url_parts.geturl())
