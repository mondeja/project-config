"""Common utilities."""

import urllib.request


# TODO: cache GET results
def GET(url: str) -> str:
    """Perform an HTTP/s GET request and return the result.

    Args:
        url (str): URL to which the request will be targeted.
    """
    return (  # type: ignore
        urllib.request.urlopen(urllib.request.Request(url))
        .read()
        .decode("utf-8")
    )
