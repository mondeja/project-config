import os
import urllib.parse

from project_config.fetchers import FetchError


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    url = url_parts.geturl()
    try:
        with open(os.path.expanduser(url)) as f:
            return f.read()
    except FileNotFoundError as exc:
        raise FetchError(f"'{url}' file not found")
