import urllib.request

from project_config.utils import GET


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    return GET(url_parts.geturl())
