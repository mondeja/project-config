"""Criptographic utilities."""

from __future__ import annotations

import hashlib


def hash_digest(data: bytes) -> bytes:
    """Return the hash digest of the data.

    :param data: The data to hash.
    :type data: bytes
    :return: The hash digest of the data.
    :rtype: bytes
    """
    return hashlib.blake2b(
        data,
        digest_size=32,
    ).digest()


def hash_file(filename: str) -> bytes:
    """Return the hash digest of the file.

    :param filename: The file to hash.
    :type filename: str
    :return: The hash digest of the file.
    :rtype: str
    """
    with open(filename, "rb") as f:
        return hash_digest(f.read())
