import urllib.request


def normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n")


# TODO: cache GET results
def GET(url: str) -> str:
    return (  # type: ignore
        urllib.request.urlopen(urllib.request.Request(url)).read().decode("utf-8")
    )
