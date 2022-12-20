"""File system tree API."""

from __future__ import annotations

import contextlib
import functools
import os
import stat
from collections.abc import Iterable
from typing import Any
from urllib.parse import SplitResult

from project_config.cache import Cache
from project_config.fetchers import (
    download_file_from_urlsplit_scheme,
    urlsplit_with_scheme,
)
from project_config.serializers import (
    SerializerError,
    deserialize_for_url,
    guess_preferred_serializer,
    serialize_for_url,
)
from project_config.utils.crypto import hash_file


__all__ = (
    "cache_file",
    "cached_local_file",
    "fetch_remote_file",
    "edit_local_file",
)


IGNORE_SERIALIZATION_ERRORS_CTX = functools.partial(
    contextlib.suppress,
    SerializerError,
)


def _split_fname_preferred_serializer(
    fpath: str,
) -> tuple[str, str | None]:
    preferred_serializer: str | None = None
    fname = fpath
    if "?" in fpath:
        fname, preferred_serializer = fpath.split("?", maxsplit=1)
        # check if the serializer is really an URL with arguments after '?'
        if "&" in preferred_serializer or "=" in preferred_serializer:
            preferred_serializer = None
            fname = fpath
    return (fname, preferred_serializer)


def _split_fpath_parts(
    fpath: str,
) -> tuple[str, str | None, SplitResult, str]:
    fname, preferred_serializer = _split_fname_preferred_serializer(
        fpath,
    )
    uri_parts, scheme = urlsplit_with_scheme(fname)
    return (fname, preferred_serializer, uri_parts, scheme)


def cache_file(
    fpath: str,
    serializers: list[str] | None = None,
    forbid_serializers: Iterable[str] | None = None,
    ignore_serialization_errors: bool = False,
) -> None:
    """Cache the file content and its serialized version.

    If the file is local, the cache key is the file path, its last
    modification time and root directory name. If the file is remote,
    the cache key is the file URL.

    Args:
        fpath (str): The file path or URL.
        serializers (Iterable[str], optional): The serializers to use.
        forbid_serializers (Iterable[str], optional): The serializers to
            forbid. Only makes sense for serializers guessed for the
            file.
        ignore_serialization_errors (bool, optional): If True, ignore
            serialization errors.
    """
    (
        fname,
        preferred_serializer,
        uri_parts,
        scheme,
    ) = _split_fpath_parts(fpath)
    is_local_file = scheme == "file"

    if serializers is None:
        serializers = []
    if preferred_serializer is None:
        preferred_serializer = guess_preferred_serializer(fname)[1]
        if preferred_serializer is not None:
            serializers.append(preferred_serializer)

    # some serializers are forbidden in some calls, like the Python
    # one when we are precaching a Python file before executing
    # plugins
    if forbid_serializers:
        for serializer in forbid_serializers:
            if serializer in serializers:
                serializers.remove(serializer)

    serialization_context = (
        IGNORE_SERIALIZATION_ERRORS_CTX
        if ignore_serialization_errors
        else contextlib.nullcontext
    )

    previous_value_in_cache: dict[str, str] | None = None

    if is_local_file:
        # the file is local, check if exists in the cache unmodified
        try:
            fstat = os.stat(fname)
        except FileNotFoundError:
            # the file does not exist, skip caching
            return
        if stat.S_ISDIR(fstat.st_mode):
            # the file is a directory, skip caching
            return

        fhash = hash_file(fname)

        previous_value_in_cache = Cache.get(fhash)
        if previous_value_in_cache is None:
            # if not, cache the file content
            with open(fname, encoding="utf-8") as f:
                plain_fcontent = f.read()

            new_cache_value = {"_plain": plain_fcontent}

            with serialization_context():  # type: ignore
                for serializer in serializers or []:
                    new_cache_value[serializer] = serialize_for_url(
                        fname,
                        plain_fcontent,
                        prefer_serializer=serializer,
                    )

            Cache.set(
                fhash,
                new_cache_value,
            )
        else:
            # file is already cached, just update serialized versions
            _changed = False
            with serialization_context():  # type: ignore
                for serializer in serializers or []:
                    if serializer not in previous_value_in_cache:
                        previous_value_in_cache[serializer] = serialize_for_url(
                            fname,
                            previous_value_in_cache["_plain"],
                            prefer_serializer=serializer,
                        )
                        _changed = True

            if _changed:
                Cache.set(
                    fhash,
                    previous_value_in_cache,
                )
    else:
        # the file is remote, check if resides in the cache
        previous_value_in_cache = Cache.get(fname)

        if previous_value_in_cache is None:
            # TODO: What happens trying to download a directory?
            plain_fcontent = download_file_from_urlsplit_scheme(
                fname,
                uri_parts,
                scheme,
            )
            new_cache_value = {"_plain": plain_fcontent}

            with serialization_context():  # type: ignore
                for serializer in serializers or []:
                    new_cache_value[serializer] = serialize_for_url(
                        fname,
                        plain_fcontent,
                        prefer_serializer=serializer,
                    )

            Cache.set(fname, new_cache_value)
        else:
            # file is already cached, just update serialized versions
            _changed = False
            with serialization_context():  # type: ignore
                for serializer in serializers or []:
                    if serializer not in previous_value_in_cache:
                        previous_value_in_cache[serializer] = serialize_for_url(
                            fname,
                            previous_value_in_cache["_plain"],
                            prefer_serializer=serializer,
                        )
                        _changed = True

            if _changed:
                Cache.set(fname, previous_value_in_cache)


def cached_local_file(
    fpath: str,
    serializer: str | None = None,
) -> Any:
    """Get the cached file content.

    Args:
        fpath (str): The file path.

    Returns:
        str: The cached file content.
    """
    fname, preferred_serializer = _split_fname_preferred_serializer(fpath)

    if serializer is None:
        if preferred_serializer is None:
            preferred_serializer = guess_preferred_serializer(fname)[1]
        serializer = preferred_serializer

    fhash = hash_file(fname)
    previous_value_in_cache: dict[str, str] | None = Cache.get(fhash)

    if previous_value_in_cache is None:
        # A file could be requested but is not inside `files`
        # object, so it is not cached yet
        cache_file(
            fpath,
            serializers=(
                [serializer] if serializer not in ("_plain", None) else []
            ),
        )
        return cached_local_file(fpath, serializer=serializer)

    if serializer not in previous_value_in_cache:
        previous_value_in_cache[serializer] = serialize_for_url(
            fname,
            previous_value_in_cache["_plain"],
            prefer_serializer=serializer,
        )

        # Don't serialize Python files because some types like
        # modules can't be serialized by pickle
        #
        # TODO: Manage this in a better way
        if serializer == "py":
            result = previous_value_in_cache.pop("py")
        else:
            result = previous_value_in_cache[serializer]
        Cache.set(
            fhash,
            previous_value_in_cache,
        )
    else:
        result = previous_value_in_cache[serializer]
    return result


def fetch_remote_file(
    uri: str,
    serializer: str | None = None,
) -> Any:
    """Fetch the remote file content.

    Args:
        uri (str): The file uri.
        serializer (str, optional): The serializer to use.
    """
    (
        fname,
        preferred_serializer,
        uri_parts,
        scheme,
    ) = _split_fpath_parts(uri)
    if scheme == "file":
        cache_file(uri)
        return cached_local_file(uri)

    if serializer is None:
        if preferred_serializer is None:
            _, serializer = guess_preferred_serializer(fname)
        serializer = preferred_serializer

    previous_value_in_cache: dict[str, str] | None = Cache.get(fname)

    if previous_value_in_cache is None:
        plain_fcontent = download_file_from_urlsplit_scheme(
            fname,
            uri_parts,
            scheme,
        )
        new_cache_value = {"_plain": plain_fcontent}
    else:
        new_cache_value = previous_value_in_cache

    if serializer not in new_cache_value:
        new_cache_value[serializer] = serialize_for_url(  # type: ignore
            fname,
            plain_fcontent,
            prefer_serializer=serializer,
        )

        Cache.set(fname, new_cache_value)
    return new_cache_value[serializer]  # type: ignore


def edit_local_file(fpath: str, new_content: Any) -> bool:
    """Edit the local file and update the cache.

    Args:
        fpath (str): The file path.
        new_content (Any): The new object to serialize.
    """
    fpath, preferred_serializer = guess_preferred_serializer(fpath)
    previous_content_string = cached_local_file(fpath)

    new_content_string = deserialize_for_url(
        fpath,
        new_content,
        prefer_serializer=preferred_serializer,
    )

    if previous_content_string != new_content_string:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content_string)
        cache_file(
            fpath,
            serializers=(
                [preferred_serializer]
                if preferred_serializer is not None
                else []
            ),
        )
        return True
    return False
