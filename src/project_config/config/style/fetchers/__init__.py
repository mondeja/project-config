import importlib
import os
import sys
import typing as t
import urllib.request

from project_config.exceptions import ProjectConfigNotImplementedError

FetchResult = t.Dict[str, t.Union[str, t.List[str]]]

class SchemeProtocolNotImplementedError(ProjectConfigNotImplementedError):
    def __init__(self, scheme: str):
        super().__init__(
            f"Retrieving of styles from scheme protocol '{scheme}:'"
            " is not implemented."
        )


decoders = {
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
                "object_fallback": "SafeLoader"
            }
        }
    },
    ".toml": {
        # TODO: use tomlkit as fallback, try tomli first or toml
        #   if we are in Python >= 3.11
        "module": "tomlkit",
        "function": "parse",
    }
}

def _file_can_not_be_decoded_as_json_error(
    url,
    error_message,
):
    return f"'{url}' can't be decoded as a valid JSON file:{error_message}"


def _decode_style_string(url: str, style_string: str) -> FetchResult:
    ext = os.path.splitext(url)[-1]
    try:
        decoder = decoders[ext]
    except KeyError:
        decoder = decoders[".json"]  # JSON as fallback

    # prepare decoder function
    loader_function = getattr(
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
            "json",           # json.decoder.JSONDecodeError
            "pyjson5",        # pyjson5.Json5IllegalCharacter
            "tomlkit",        # tomlkit.exceptions.UnexpectedEofError
        ):
            return None, _file_can_not_be_decoded_as_json_error(url, f" {exc.args[0]}")
        elif package_name == "yaml":
            # Example: yaml.scanner.ScannerError
            return None, _file_can_not_be_decoded_as_json_error(url, f"\n{exc.__str__()}")
        raise
    else:
        return result, None


def fetch_style(url: str) -> FetchResult:
    scheme = urllib.request.urlsplit(url).scheme or 'file'
    try:
        mod = importlib.import_module(f"project_config.config.style.fetchers.{scheme}")
    except ImportError:
        # TODO: add more fetchers
        raise SchemeProtocolNotImplementedError(scheme)
    try:
        style_string = getattr(mod, "fetch")(url)
    except FileNotFoundError:
        return None, f"'{url}' file not found"
    return _decode_style_string(url, style_string)


def resolve_maybe_relative_url(url: str, parent_url: str) -> str:
    url_parts = urllib.request.urlsplit(url)

    if url_parts.scheme in ('', 'file'):  # is a file
        if os.path.isabs(url):
            return url

        parent_path = urllib.request.urlsplit(parent_url).path
        parent_dirpath = os.path.split(parent_path)[0]
        return os.path.abspath(
            os.path.join(
                parent_dirpath,
                os.path.expanduser(url)
            )
        )

    raise SchemeProtocolNotImplementedError(url_parts.scheme)
