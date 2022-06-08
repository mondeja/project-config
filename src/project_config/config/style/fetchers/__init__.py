import importlib
import typing as t


def fetch_style(url: str) -> t.Any:
    # TODO: depending on the url use a fetcher or another
    try:
        style = getattr(
            importlib.import_module("project_config.config.style.fetchers.file"),
            "get",
        )(url)
    except FileNotFoundError:
        return None, f"'{url}' file not found"
    else:
        return style, None
