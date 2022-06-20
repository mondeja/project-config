"""Fetchers for different types of resources by URI schema."""

import importlib
import os
import urllib.parse

from project_config.compat import TypeAlias
from project_config.exceptions import ProjectConfigNotImplementedError
from project_config.serializers import (
    SerializerError,
    SerializerResult,
    serialize_for_url,
)


FetchResult: TypeAlias = SerializerResult


class FetchError(SerializerError):
    """Error happened during the fetching of a resource."""


class SchemeProtocolNotImplementedError(ProjectConfigNotImplementedError):
    """A URI schema has not been implemented."""

    def __init__(self, scheme: str):
        super().__init__(
            f"Retrieving of styles from scheme protocol '{scheme}:'"
            " is not implemented.",
        )


schemes_to_modnames = {
    "gh": "github",
    "http": "https",
    # TODO: add Python library fetcher, see:
    #   https://nitpick.readthedocs.io/en/latest/configuration.html#style-inside-python-package
}


def fetch(url: str) -> FetchResult:
    """Fetch a result given an URI.

    Args:
        url (str): The URL of the resource to fetch.
    """
    url_parts = urllib.parse.urlsplit(url)
    scheme = (
        "file"
        if not url_parts.scheme
        else (schemes_to_modnames.get(url_parts.scheme, url_parts.scheme))
    )
    try:
        mod = importlib.import_module(f"project_config.fetchers.{scheme}")
    except ImportError:
        raise SchemeProtocolNotImplementedError(scheme)

    string = getattr(mod, "fetch")(url_parts)
    return serialize_for_url(url, string)


def resolve_maybe_relative_url(url: str, parent_url: str) -> str:
    """Relative URL resolver.

    Args:
        url (str): URL or relative URI to the target resource.
        parent_url (str): Absolute URI of the origin resource, which
            acts as the requester.

    Returns:
        str: Absolute URI for the children resource.
    """
    url_parts = urllib.parse.urlsplit(url)

    if url_parts.scheme in ("", "file"):  # is a file
        parent_url_parts = urllib.parse.urlsplit(parent_url)

        if parent_url_parts.scheme in ("", "file"):  # parent url is file also
            # we are offline, doing just path manipulation
            if os.path.isabs(url):
                return url

            parent_dirpath = os.path.split(parent_url_parts.path)[0]
            return os.path.abspath(
                os.path.join(parent_dirpath, os.path.expanduser(url)),
            )

        elif parent_url_parts.scheme in ("gh", "github"):
            project, parent_path = parent_url_parts.path.lstrip("/").split(
                "/",
                maxsplit=1,
            )
            parent_dirpath = os.path.split(parent_path)[0]
            return (
                f"{parent_url_parts.scheme}://{parent_url_parts.netloc}/"
                f"{project}/{urllib.parse.urljoin(parent_path, url)}"
            )

        # parent url is another protocol like https, so we are online,
        # must convert to a relative URI depending on the protocol
        raise SchemeProtocolNotImplementedError(parent_url_parts.scheme)

    # other protocols like https uses absolute URLs
    return url
