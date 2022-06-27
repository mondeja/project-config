"""HTTP/s utilities."""

import time
import typing as t
import urllib.request

from project_config.cache import Cache
from project_config.exceptions import ProjectConfigException


class ProjectConfigHTTPError(ProjectConfigException):
    """HTTP error."""


class ProjectConfigTimeoutError(ProjectConfigHTTPError):
    """Timeout error."""


def _GET(url: str, timeout: int = 10) -> str:
    start = time.time()
    end = start + timeout
    err = None
    while time.time() < end:
        try:
            return (  # type: ignore
                urllib.request.urlopen(urllib.request.Request(url))
                .read()
                .decode("utf-8")
            )
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            err = exc.__str__()
            time.sleep(1)

    error_reason = "" if not err else f" Possibly caused by: {err}"
    raise ProjectConfigTimeoutError(
        f"Impossible to fetch '{url}' after {timeout} seconds.{error_reason}",
    )


def GET(url: str, use_cache: bool = True, **kwargs: t.Any) -> str:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
        use_cache (bool): Specify if the cache must be used
            requesting the resource.
    """
    if use_cache:
        result = Cache.get(url)
        if result is None:
            result = _GET(url, **kwargs)
            Cache.set(url, result)
    else:
        result = _GET(url, **kwargs)
    return result  # type: ignore
