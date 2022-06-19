"""JSON serializers."""

import functools
import importlib
import os
import sys
import typing as t

from identify import identify

from project_config.compat import Protocol, tomllib_package_name
from project_config.exceptions import ProjectConfigException


SerializerResult = t.Dict[str, t.Any]


class SerializerFunction(Protocol):
    """Typecheck protocol for function resolved by serialization factory."""

    def __call__(  # noqa: D102
        self,
        string: str,
        **kwargs: t.Any,
    ) -> SerializerResult:
        ...


class SerializerError(ProjectConfigException):
    """Error happened serializing content as JSON."""


# TODO: improve type to take into account optional fields
serializers: t.Dict[str, t.List[t.Dict[str, t.Any]]] = {
    ".json": [{"module": "json"}],
    ".json5": [{"module": "pyjson5"}, {"module": "json5"}],
    ".yaml": [
        {
            # Implementation notes:
            #
            # PyYaml is currently using the Yaml 1.1 specification,
            # which converts some words like `on` and `off` to `True`
            # and `False`. This leads to problems, for example, checking
            # `on.` objects in Github workflows.
            #
            # There is an issue open to track the progress to support
            # YAML 1.2 at https://github.com/yaml/pyyaml/issues/486
            #
            # Comparison of v1.1 vs v1.2 at:
            # https://perlpunk.github.io/yaml-test-schema/schemas.html
            #
            # "module": "yaml",
            # "function": "load",
            # "function_kwargs": {
            #    "Loader": {
            #        "module": "yaml",
            #        "object": "CSafeLoader",
            #        "object_fallback": "SafeLoader",
            #    },
            # },
            #
            # So we use ruamel.yaml, which supports v1.2 by default
            "module": "project_config.serializers.yaml",
        },
    ],
    ".toml": [{"module": tomllib_package_name}],
    ".ini": [{"module": "project_config.serializers.ini"}],
    ".editorconfig": [{"module": "project_config.serializers.editorconfig"}],
    ".py": [
        {
            "module": "project_config.serializers.python",
            "function_kwargs_from_url": lambda url: {
                "namespace": {"__file__": url},
            },
        },
    ],
}


def _get_serializer(url: str) -> t.Any:  # TODO: improve this type
    ext = os.path.splitext(url)[-1]
    try:
        serializer_implementations = serializers[ext]
    except KeyError:
        # try to guess the file type with identify
        serializer_implementations = None
        for tag in identify.tags_from_filename(os.path.basename(url)):
            if f".{tag}" in serializers:
                serializer_implementations = serializers[f".{tag}"]
                break
        if serializer_implementations is None:
            serializer_implementations = serializers[
                ".json"
            ]  # JSON as fallback

    # prepare serializer function
    serializer, module = None, None
    for i, serializer_implementation in enumerate(
        serializer_implementations,  # type: ignore
    ):
        try:
            module = importlib.import_module(
                serializer_implementation["module"],
            )
        except ImportError:
            # if module for implementation is not importable, try next maybe
            if i > len(serializer) - 1:  # type: ignore
                raise
        else:
            serializer = serializer_implementation
            break

    loader_function: SerializerFunction = getattr(
        module,
        serializer.get("function", "loads"),  # type: ignore
    )

    function_kwargs: t.Dict[str, t.Any] = {}
    if "function_kwargs" in serializer:  # type: ignore
        function_kwargs = {}
        for kwarg_name, kwarg_values in serializer[
            "function_kwargs"
        ].items():  # type: ignore
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

    if "function_kwargs_from_url" in serializer:  # type: ignore
        function_kwargs.update(
            serializer["function_kwargs_from_url"](url),  # type: ignore
        )

    return functools.partial(loader_function, **function_kwargs)


def _file_can_not_be_serialized_as_json_error(
    url: str,
    error_message: str,
) -> str:
    return f"'{url}' can't be serialized as a valid JSON file:{error_message}"


def serialize_for_url(url: str, string: str) -> SerializerResult:
    """Serializes to JSON a string according to the given URI.

    Args:
        url (str): URI of the file, used to detect the type of the file,
            either using the extension or through ``identify``.
        string (str): File content to serialize.

    Returns:
        dict: Result of the JSON serialization.
    """
    # TODO: intersphinx for identify in documentation
    try:
        # serialize
        result = _get_serializer(url)(string)
    except Exception:
        # handle exceptions in third party packages without importing them
        exc_class, exc, _ = sys.exc_info()
        package_name = exc_class.__module__.split(".")[0]
        if package_name in (  # Examples:
            "json",  # json.serializer.JSONDecodeError
            "pyjson5",  # pyjson5.Json5IllegalCharacter
            "tomlkit",  # tomlkit.exceptions.UnexpectedEofError
        ):
            raise SerializerError(
                _file_can_not_be_serialized_as_json_error(
                    url,
                    f" {exc.args[0]}",  # type: ignore
                ),
            )
        elif package_name == "yaml":
            # Example: yaml.scanner.ScannerError
            raise SerializerError(
                _file_can_not_be_serialized_as_json_error(
                    url,
                    f"\n{exc.__str__()}",
                ),
            )
        raise
    return result  # type: ignore
