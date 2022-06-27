"""HTTP/s resource URIs fetcher."""

import urllib.request

from project_config.fetchers import FetchError
from project_config.utils.http import GET, ProjectConfigHTTPError


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    """Fetch an HTTP/s resource performing a GET request."""
    try:
        return GET(url_parts.geturl())
    except ProjectConfigHTTPError as exc:
        raise FetchError(exc.__str__())
