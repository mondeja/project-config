import os
import urllib.parse

from project_config.config.style.fetchers import FetchStyleError


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    url = url_parts.geturl()
    try:
        with open(os.path.expanduser(url)) as f:
            return f.read()
    except FileNotFoundError as exc:
        raise FetchStyleError(f"'{url}' file not found")
