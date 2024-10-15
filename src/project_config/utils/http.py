"""HTTP/s utilities."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.error import ContentTooShortError, HTTPError, URLError
from urllib.request import Request, urlopen

from project_config.cache import Cache
from project_config.exceptions import ProjectConfigException


class ProjectConfigHTTPError(ProjectConfigException):
    """HTTP error."""


class ProjectConfigTimeoutError(ProjectConfigHTTPError):
    """Timeout error."""


def _GET_impl(
    url: str,
    timeout: float | None = None,
    sleep: float = 1.0,
    headers: dict[str, str] | None = None,
) -> str:
    start = time.time()
    timeout = timeout or float(
        os.environ.get("PROJECT_CONFIG_REQUESTS_TIMEOUT", 10),
    )
    end = start + timeout
    err = None
    request = Request(url)
    if headers:
        for key, value in headers.items():
            request.add_header(key, value)
    while time.time() < end:
        try:
            with urlopen(request) as req:
                response = req.read().decode("utf-8")
        except (
            URLError,
            HTTPError,
            ContentTooShortError,
        ) as exc:
            err = exc.__str__()
            time.sleep(sleep)
        else:
            return response  # type: ignore

    error_reason = "" if not err else f" Possibly caused by: {err}"
    raise ProjectConfigTimeoutError(
        f"Impossible to fetch '{url}' after {timeout} seconds.{error_reason}",
    )


def GET(
    url: str,
    use_cache: bool = True,  # noqa: FBT001, FBT002
    **kwargs: Any,
) -> Any:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
        use_cache (bool): Specify if the cache must be used
            requesting the resource.
        **kwargs: Keyword arguments ``timeout`` and ``sleep``
            passed to the internal wrapper GET function.
    """
    if use_cache:
        result = Cache.get(url)  # this could return Any
        if result is None:
            result = _GET_impl(url, **kwargs)
            Cache.set(url, result)
    else:
        result = _GET_impl(url, **kwargs)
    return result
