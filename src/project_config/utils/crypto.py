"""Criptographic utilities."""

from __future__ import annotations

import hashlib


def _build_hash(data: bytes) -> hashlib.blake2b:
    return hashlib.blake2b(data, digest_size=32)


def hash_hexdigest(data: bytes) -> str:
    """Return the hexadecimal hash digest of the data.

    :param data: The data to hash.
    :type data: bytes
    :return: The hexadecimal hash digest of the data.
    :rtype: str
    """
    return _build_hash(data).hexdigest()


def hash_file(filename: str) -> str:
    """Return the hash digest of the file.

    :param filename: The file to hash.
    :type filename: str
    :return: The hash digest of the file.
    :rtype: str
    """
    with open(filename, "rb") as f:
        return hash_hexdigest(f.read())
