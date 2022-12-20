"""Fetchers for different types of resources by URI schema."""

from __future__ import annotations

import importlib
import os
import urllib.parse
from typing import Any

from project_config.exceptions import (
    ProjectConfigException,
    ProjectConfigNotImplementedError,
)
from project_config.serializers import (
    SerializerError,
    guess_preferred_serializer,
    serialize_for_url,
)
from project_config.utils.http import ProjectConfigTimeoutError


class FetchError(ProjectConfigException):
    """Error happened during the fetching of a resource."""


class SchemeProtocolNotImplementedError(ProjectConfigNotImplementedError):
    """A URI schema has not been implemented."""

    def __init__(self, scheme: str, action: str = "Fetching"):
        super().__init__(
            f"{action} from scheme protocol '{scheme}:' is not implemented.",
        )


schemes_to_modnames = {
    "gh": "github",
    "http": "https",
    # TODO: add Python library fetcher, see:
    #   https://nitpick.readthedocs.io/en/latest/configuration.html#style-inside-python-package
}


def _get_scheme_from_urlparts(url_parts: urllib.parse.SplitResult) -> str:
    return (
        "file"
        if not url_parts.scheme
        else (
            schemes_to_modnames.get(
                url_parts.scheme,
                # in Windows, schemes could be confused with drive letters,
                # as in "C:\foo\bar.txt" so in case that the scheme has only
                # length 1 we assume it is a drive letter. Note that in Windows
                # drive letters are of length 1 (to support more drives
                # mounted paths must be used) and that network schemes don't
                # have a length larger than 1:
                (url_parts.scheme if len(url_parts.scheme) > 1 else "file"),
            )
        )
    )


def uri_is_pointing_to_local_file(uri: str) -> bool:
    """Return True if an URI is pointing to a local file."""
    url_parts = urllib.parse.urlsplit(uri)
    return _get_scheme_from_urlparts(url_parts) == "file"


def urlsplit_with_scheme(url: str) -> tuple[urllib.parse.SplitResult, str]:
    """Return a tuple with the URL parts and the scheme."""
    url_parts = urllib.parse.urlsplit(url)
    scheme = _get_scheme_from_urlparts(url_parts)
    return url_parts, scheme


def download_file_from_urlsplit_scheme(
    url: str,
    url_parts: urllib.parse.SplitResult,
    scheme: str,
    **kwargs: Any,
) -> str:
    """Download a file from a URL knowing its scheme."""
    try:
        module = importlib.import_module(f"project_config.fetchers.{scheme}")
    except ImportError:
        raise SchemeProtocolNotImplementedError(scheme)

    try:
        # TODO: ModuleType with protocol here?
        return module.fetch(url_parts, **kwargs)  # type: ignore
    except FileNotFoundError:
        raise FetchError(f"'{url}' file not found")
    except ProjectConfigTimeoutError as exc:
        raise FetchError(exc.message)


def fetch(url: str, **kwargs: Any) -> Any:
    """Fetch a result given an URI.

    Args:
        url (str): The URL of the resource to fetch.
    """
    url, serializer_name = guess_preferred_serializer(url)

    url_parts = urllib.parse.urlsplit(url)
    scheme = _get_scheme_from_urlparts(url_parts)

    string = download_file_from_urlsplit_scheme(
        url,
        url_parts,
        scheme,
        **kwargs,
    )

    try:
        return serialize_for_url(
            url,
            string,
            prefer_serializer=serializer_name,
        )
    except SerializerError as exc:
        raise FetchError(exc.message)


def resolve_url(url: str) -> tuple[str, str]:
    """Resolve an URL from a custom URI to their real counterpart.

    Args:
        url (str): URI to the target resource.

    Returns:
        tuple: Real URL for the target resource and scheme.
    """
    url_parts = urllib.parse.urlsplit(url)
    scheme = _get_scheme_from_urlparts(url_parts)
    try:
        module = importlib.import_module(f"project_config.fetchers.{scheme}")
    except ImportError:  # pragma: no cover
        raise SchemeProtocolNotImplementedError(scheme, action="Resolving")
    return (
        getattr(
            module,
            "resolve_url",
            lambda url_parts_: url,  # noqa: U100
        )(url_parts),
        scheme,
    )


def resolve_maybe_relative_url(url: str, parent_url: str, rootdir: str) -> str:
    """Relative URL resolver.

    Args:
        url (str): URL or relative URI to the target resource.
        parent_url (str): Absolute URI of the origin resource, which
            acts as the requester.

    Returns:
        str: Absolute URI for the children resource.
    """
    url_parts = urllib.parse.urlsplit(url)
    url_scheme = _get_scheme_from_urlparts(url_parts)

    if url_scheme == "file":  # child url is a file
        parent_url_parts = urllib.parse.urlsplit(parent_url)
        parent_url_scheme = _get_scheme_from_urlparts(parent_url_parts)

        if parent_url_scheme == "file":  # parent url is file also
            # we are offline, doing just path manipulation
            if os.path.isabs(url):
                return url

            abs_parent_url = (
                parent_url
                if os.path.isabs(parent_url)
                else os.path.join(rootdir, parent_url)
            )
            abs_parent_dir_url = (
                os.path.split(abs_parent_url)[0]
                if not os.path.isdir(abs_parent_url)
                else abs_parent_url
            )
            resolved_url = os.path.abspath(
                os.path.join(abs_parent_dir_url, url),
            )

            return os.path.relpath(resolved_url, rootdir)

        elif parent_url_scheme in ("gh", "github"):
            project, parent_path = parent_url_parts.path.lstrip("/").split(
                "/",
                maxsplit=1,
            )
            return (
                # here `urljoin` does the relative resolvement
                f"{parent_url_parts.scheme}://{parent_url_parts.netloc}/"
                f"{project}/{urllib.parse.urljoin(parent_path, url)}"
            )

        # parent url is another protocol like https, so we are online,
        # must convert to a relative URI depending on the protocol
        raise SchemeProtocolNotImplementedError(
            parent_url_parts.scheme,
            action="Resolving",
        )

    # other protocols like https are supposed to use absolute URLs
    #
    # TODO: Implement (or test) relative URLs for other protocols
    return url
