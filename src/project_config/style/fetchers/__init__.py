import importlib
import typing as t


def fetch_style(url: str) -> t.Any:
    # TODO: depending on the url use a fetcher or another
    return getattr(
        importlib.import_module("project_config.style.fetchers.file"),
        "get",
    )(url)
