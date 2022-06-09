import os

from project_config.config.style.fetchers import FetchStyleError


def fetch(url: str) -> str:
    try:
        with open(os.path.expanduser(url)) as f:
            return f.read()
    except FileNotFoundError as exc:
        raise FetchStyleError(f"'{url}' file not found")
