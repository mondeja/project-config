import urllib.request


def GET(url: str) -> str:
    return (  # type: ignore
        urllib.request.urlopen(urllib.request.Request(url)).read().decode("utf-8")
    )


def fetch(url_parts: urllib.parse.SplitResult) -> str:
    return GET(url_parts.geturl())
