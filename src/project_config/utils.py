"""Common utilities."""

import typing as t
import urllib.request

from project_config.cache import Cache


def GET(url: str) -> str:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
    """
    result = Cache.get(url)
    if result is None:
        result = (
            urllib.request.urlopen(urllib.request.Request(url))
            .read()
            .decode("utf-8")
        )
        Cache.set(url, result)
    return t.cast(str, result)
