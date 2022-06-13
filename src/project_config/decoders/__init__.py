import functools
import importlib
import os
import sys
import typing as t

import typing_extensions as te
from identify import identify

from project_config.exceptions import ProjectConfigException


DecoderResult = t.Dict[str, t.List[str]]


class DecoderFunction(te.Protocol):
    def __call__(self, string: str, **kwargs: t.Any) -> DecoderResult:
        ...


class DecoderError(ProjectConfigException):
    pass


# TODO: improve type to take into account optional fields
decoders: t.Dict[str, t.Dict[str, t.Any]] = {
    ".json": {"module": "json"},
    ".json5": {"module": "pyjson5"},  # TODO: json5 as fallback
    ".yaml": {
        "module": "yaml",
        "function": "load",
        "function_kwargs": {
            "Loader": {
                "module": "yaml",
                "object": "CSafeLoader",
                "object_fallback": "SafeLoader",
            },
        },
    },
    ".toml": {
        # TODO: tomlkit as fallback, try tomli first or toml
        #   if we are in Python >= 3.11
        "module": "tomli"
        if sys.version_info < (3, 11)
        else "tomllib",
    },
    ".ini": {"module": "project_config.decoders.ini"},
    ".editorconfig": {"module": "project_config.decoders.editorconfig"},
}


def get_decoder(url: str) -> t.Any:  # TODO: improve this type
    ext = os.path.splitext(url)[-1]
    try:
        decoder = decoders[ext]
    except KeyError:
        # try to guess the file type with identify
        decoder = None
        for tag in identify.tags_from_filename(os.path.basename(url)):
            if f".{tag}" in decoders:
                decoder = decoders[f".{tag}"]
                break
        if decoder is None:
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

    return functools.partial(loader_function, **function_kwargs)


def _file_can_not_be_decoded_as_json_error(
    url: str,
    error_message: str,
) -> str:
    return f"'{url}' can't be decoded as a valid JSON file:{error_message}"


def decode_for_url(url: str, string: str) -> DecoderResult:
    try:
        # decode
        result = get_decoder(url)(string)
    except Exception:
        # handle exceptions in third party packages without importing them
        exc_class, exc, _ = sys.exc_info()
        package_name = exc_class.__module__.split(".")[0]
        if package_name in (  # Examples:
            "json",  # json.decoder.JSONDecodeError
            "pyjson5",  # pyjson5.Json5IllegalCharacter
            "tomlkit",  # tomlkit.exceptions.UnexpectedEofError
        ):
            raise DecoderError(
                _file_can_not_be_decoded_as_json_error(url, f" {exc.args[0]}"),  # type: ignore
            )
        elif package_name == "yaml":
            # Example: yaml.scanner.ScannerError
            raise DecoderError(
                _file_can_not_be_decoded_as_json_error(url, f"\n{exc.__str__()}"),
            )
        raise
    return result
