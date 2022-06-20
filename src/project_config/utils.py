"""Common utilities."""

import urllib.request

from project_config.cache import Cache
from project_config.exceptions import ProjectConfigException


class HTTPError(ProjectConfigException):
    """HTTP error wrapper."""


def _GET(url: str) -> str:
    try:
        return (  # type: ignore
            urllib.request.urlopen(urllib.request.Request(url))
            .read()
            .decode("utf-8")
        )
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise HTTPError(exc.__str__())


def GET(url: str, use_cache: bool = True) -> str:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
        use_cache (bool): Specify if the cache must be used
            requesting the resource.
    """
    if use_cache:
        result = Cache.get(url)
        if result is None:
            result = _GET(url)
            Cache.set(url, result)
    else:
        result = _GET(url)
    return result  # type: ignore
