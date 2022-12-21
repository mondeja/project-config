"""HTTP/s utilities."""

from __future__ import annotations

import os
import time
import urllib.request
from typing import Any

from project_config.cache import Cache
from project_config.exceptions import ProjectConfigException


class ProjectConfigHTTPError(ProjectConfigException):
    """HTTP error."""


class ProjectConfigTimeoutError(ProjectConfigHTTPError):
    """Timeout error."""


def _GET(
    url: str,
    timeout: float | None = None,
    sleep: float = 1.0,
) -> str:
    start = time.time()
    timeout = timeout or float(
        os.environ.get("PROJECT_CONFIG_REQUESTS_TIMEOUT", 10),
    )
    end = start + timeout
    err = None
    while time.time() < end:
        try:
            with urllib.request.urlopen(url) as req:
                response = req.read().decode("utf-8")
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            urllib.error.ContentTooShortError,
        ) as exc:
            err = exc.__str__()
            time.sleep(sleep)
        else:
            return response  # type: ignore

    error_reason = "" if not err else f" Possibly caused by: {err}"
    raise ProjectConfigTimeoutError(
        f"Impossible to fetch '{url}' after {timeout} seconds.{error_reason}",
    )


def GET(url: str, use_cache: bool = True, **kwargs: Any) -> Any:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
        use_cache (bool): Specify if the cache must be used
            requesting the resource.
    """
    if use_cache:
        result = Cache.get(url)  # this could return Any
        if result is None:
            result = _GET(url, **kwargs)
            Cache.set(url, result)
    else:
        result = _GET(url, **kwargs)
    return result
