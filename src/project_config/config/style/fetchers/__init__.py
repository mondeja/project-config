import importlib
import os
import sys
import typing as t
import urllib.parse

import typing_extensions

from project_config.exceptions import (
    ProjectConfigException,
    ProjectConfigNotImplementedError,
)


FetchResult = t.Dict[str, t.List[str]]


class DecoderFunction(typing_extensions.Protocol):
    def __call__(self, style_string: str, **kwargs: t.Any) -> FetchResult:
        ...


class FetchStyleError(ProjectConfigException):
    pass


class SchemeProtocolNotImplementedError(ProjectConfigNotImplementedError):
    def __init__(self, scheme: str):
        super().__init__(
            f"Retrieving of styles from scheme protocol '{scheme}:'"
            " is not implemented."
        )


# TODO: improve type to take into account optional fields
decoders: t.Dict[str, t.Dict[str, t.Any]] = {
    ".json": {
        "module": "json",
    },
    ".json5": {
        "module": "pyjson5",
        # TODO: json5 as fallback module
    },
    ".yaml": {
        "module": "yaml",
        "function": "load",
        "function_kwargs": {
            "Loader": {
                "module": "yaml",
                "object": "CSafeLoader",
                "object_fallback": "SafeLoader",
            }
        },
    },
    ".toml": {
        # TODO: use tomlkit as fallback, try tomli first or toml
        #   if we are in Python >= 3.11
        "module": "tomlkit",
        "function": "parse",
    },
}

schemes_to_modnames = {
    "gh": "github",
    # TODO: add more fetchers
}


def _file_can_not_be_decoded_as_json_error(
    url: str,
    error_message: str,
) -> str:
    return f"'{url}' can't be decoded as a valid JSON file:{error_message}"


def _decode_style_string(url: str, style_string: str) -> FetchResult:
    ext = os.path.splitext(url)[-1]
    try:
        decoder = decoders[ext]
    except KeyError:
        decoder = decoders[".json"]  # JSON as fallback

    # prepare decoder function
    loader_function: DecoderFunction = getattr(
        importlib.import_module(decoder["module"]),
        decoder.get("function", "loads"),
    )
    if "function_kwargs" in decoder:
        function_kwargs = {}
        for kwarg_name, kwarg_values in decoder["function_kwargs"].items():
            mod = importlib.import_module(kwarg_values["module"])
            try:
                obj = getattr(mod, kwarg_values["object"])
            except AttributeError:
                # fallback object, as with pyyaml use CSafeLoader instead
                # of SafeLoader if libyyaml bindings are available
                if "fallback_object" in kwarg_values:
                    obj = getattr(mod, kwarg_values["object"])
                else:
                    raise
            function_kwargs[kwarg_name] = obj
    else:
        function_kwargs = {}

    try:
        # decode
        result = loader_function(style_string, **function_kwargs)
    except Exception:
        # handle exceptions in third party packages without importing them
        exc_class, exc, _ = sys.exc_info()
        package_name = exc_class.__module__.split(".")[0]
        if package_name in (  # Examples:
            "json",  # json.decoder.JSONDecodeError
            "pyjson5",  # pyjson5.Json5IllegalCharacter
            "tomlkit",  # tomlkit.exceptions.UnexpectedEofError
        ):
            raise FetchStyleError(
                _file_can_not_be_decoded_as_json_error(url, f" {exc.args[0]}"),  # type: ignore
            )
        elif package_name == "yaml":
            # Example: yaml.scanner.ScannerError
            raise FetchStyleError(
                _file_can_not_be_decoded_as_json_error(url, f"\n{exc.__str__()}")
            )
        raise
    else:
        return result


def fetch_style(url: str) -> FetchResult:
    url_parts = urllib.parse.urlsplit(url)
    scheme = (
        "file"
        if not url_parts.scheme
        else (schemes_to_modnames.get(url_parts.scheme, url_parts.scheme))
    )
    try:
        mod = importlib.import_module(
            f"project_config.config.style.fetchers.{scheme}",
        )
    except ImportError:
        raise SchemeProtocolNotImplementedError(scheme)

    style_string = getattr(mod, "fetch")(url_parts)
    return _decode_style_string(url, style_string)


def resolve_maybe_relative_url(url: str, parent_url: str) -> str:
    url_parts = urllib.parse.urlsplit(url)

    if url_parts.scheme in ("", "file"):  # is a file
        parent_url_parts = urllib.parse.urlsplit(parent_url)

        if parent_url_parts.scheme in ("", "file"):  # parent url is file also
            # we are offline, doing just path manipulation
            if os.path.isabs(url):
                return url

            parent_dirpath = os.path.split(parent_url_parts.path)[0]
            return os.path.abspath(
                os.path.join(parent_dirpath, os.path.expanduser(url)),
            )
        elif parent_url_parts.scheme in ("gh", "github"):
            project, parent_path = parent_url_parts.path.lstrip("/").split(
                "/", maxsplit=1
            )
            parent_dirpath = os.path.split(parent_path)[0]
            return (
                f"{parent_url_parts.scheme}://{parent_url_parts.netloc}/"
                f"{project}/{urllib.parse.urljoin(parent_path, url)}"
            )

        # parent url is another protocol like https, so we are online,
        # must convert to a relative URI depending on the protocol
        raise SchemeProtocolNotImplementedError(parent_url_parts.scheme)

    # other protocols like https uses absolute URLs
    return url
