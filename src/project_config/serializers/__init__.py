"""Object serializers."""

from __future__ import annotations

import functools
import importlib
import os
import sys
import urllib.parse
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from identify import identify

from project_config.exceptions import ProjectConfigException


class SerializerError(ProjectConfigException):
    """Error happened serializing content as JSON."""


if TYPE_CHECKING:
    from project_config.compat import (
        NotRequired,
        Protocol,
        TypeAlias,
        TypedDict,
    )

    class SerializerFunction(Protocol):
        """Typecheck protocol for function resolved by serialization factory."""

        def __call__(  # noqa: D102
            self,
            _value: Any,
            **_kwargs: Any,
        ) -> Any: ...

    SerializerFunctionKwargs: TypeAlias = dict[str, Any]

    class SerializerDefinitionType(TypedDict):
        """Serializer definition type."""

        module: str

        function: NotRequired[str]
        function_kwargs_from_url_path: NotRequired[
            Callable[[str], SerializerFunctionKwargs]
        ]

    SerializerDefinitionsType: TypeAlias = list[SerializerDefinitionType]


serializers: dict[
    str,
    tuple[SerializerDefinitionsType, SerializerDefinitionsType],
] = {
    ".json": (
        [{"module": "json"}],  # loads
        [{"module": "project_config.serializers.json"}],  # dumps
    ),
    ".json5": (
        [{"module": "pyjson5"}, {"module": "json5"}],
        [{"module": "pyjson5"}, {"module": "json5"}],
    ),
    ".yaml": (
        [
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
                #    },
                # },
                #
                # So we use ruamel.yaml, which supports v1.2 by default
                "module": "project_config.serializers.yaml",
            },
        ],
        [{"module": "project_config.serializers.yaml"}],
    ),
    ".toml": (
        [{"module": "project_config.serializers.toml"}],
        [{"module": "tomlkit"}],
    ),
    ".ini": (
        [{"module": "project_config.serializers.ini"}],
        [{"module": "project_config.serializers.ini"}],
    ),
    ".editorconfig": (
        [{"module": "project_config.serializers.editorconfig"}],
        [{"module": "project_config.serializers.editorconfig"}],
    ),
    ".py": (
        [
            {
                "module": "project_config.serializers.python",
                "function_kwargs_from_url_path": lambda path: {
                    "namespace": {"__file__": path},
                },
            },
        ],
        [{"module": "project_config.serializers.python"}],
    ),
}

serializers_fallback: tuple[
    SerializerDefinitionsType,
    SerializerDefinitionsType,
] = (
    [{"module": "project_config.serializers.text"}],
    [{"module": "project_config.serializers.text"}],
)

EMPTY_CONTENT_BY_SERIALIZER = {
    "json": "{}",
    "json5": "{}",
}

SERIALIZER_FROM_EXT_FILENAME = {
    ".yaml": {
        ".pre-commit-config.yaml": (
            [{"module": "project_config.serializers.yaml"}],
            [{"module": "project_config.serializers.contrib.pre_commit"}],
        ),
    },
}


def _identify_serializer(filename: str) -> str:
    tag: str | None = None
    for identified_tag in identify.tags_from_filename(filename):
        if f".{identified_tag}" in serializers:
            tag = identified_tag
            break
    return tag if tag is not None else "text"


def guess_serializer_for_path(
    path: str,
) -> tuple[Any, Any]:
    """Guess serializer for a path.

    Args:
        path (str): Path to guess serializer for.
    """
    ext = os.path.splitext(path)[-1]
    if ext in SERIALIZER_FROM_EXT_FILENAME:
        filename = os.path.basename(path)
        if filename in SERIALIZER_FROM_EXT_FILENAME[ext]:
            return SERIALIZER_FROM_EXT_FILENAME[ext][filename], None
    try:
        return serializers[ext], None
    except Exception:
        # try to guess the file type with identify
        serializer_name = _identify_serializer(
            os.path.basename(path),
        )
        if f".{serializer_name}" in serializers:
            return serializers[f".{serializer_name}"], None
        if serializer_name == "text":  # pragma: no branch
            return serializers_fallback, None
        return None, serializer_name


def _get_serializer_function(  # noqa: PLR0912
    url: str,
    prefer_serializer: str | None = None,
    loader_function_name: str = "loads",
) -> SerializerFunction:
    url_parts = urllib.parse.urlsplit(url)
    serializer = None

    if prefer_serializer is not None:
        if f".{prefer_serializer}" in serializers:
            serializer = serializers[f".{prefer_serializer}"]
        elif f".{prefer_serializer}" == ".text":
            serializer = serializers_fallback
        else:
            raise SerializerError(
                _file_can_not_be_serialized_as_object_error(
                    url,
                    (
                        f"\nPreferred serializer '{prefer_serializer}'"
                        " not supported"
                    ),
                ),
            )
    else:
        serializer, serializer_name = guess_serializer_for_path(url_parts.path)
        if serializer is None:  # pragma: no cover
            raise SerializerError(
                _file_can_not_be_serialized_as_object_error(
                    url,
                    (
                        f"\nSerializer detected as '{serializer_name}'"
                        " not supported"
                    ),
                ),
            ) from None
    serializer = serializer[0 if loader_function_name == "loads" else 1]  # type: ignore
    # prepare serializer function
    serializer_definition, module = None, None
    for i, serializer_def in enumerate(serializer):
        try:
            module = importlib.import_module(
                serializer_def["module"],  # type: ignore
            )
        except ImportError:  # pragma: no cover
            # if module for implementation is not importable, try next maybe
            if i > len(serializer) - 1:
                raise
        else:
            serializer_definition = serializer_def
            break
    if serializer_definition is None:  # pragma: no cover
        raise SerializerError(
            _file_can_not_be_serialized_as_object_error(
                url,
                (
                    f"\nSerializer for url '{url}' can't be located,"
                    " surely because the library to handle it is"
                    " not installed."
                ),
            ),
        )

    loader_function: SerializerFunction = getattr(
        module,
        serializer_definition.get(  # type: ignore
            "function",
            loader_function_name,
        ),
    )

    function_kwargs: SerializerFunctionKwargs = {}

    """
    if "function_kwargs" in serializer:
        function_kwargs = {}
        for kwarg_name, kwarg_values in serializer[
            "function_kwargs"
        ].items():
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
    """

    if "function_kwargs_from_url_path" in serializer_definition:  # type: ignore
        function_kwargs.update(
            serializer_definition["function_kwargs_from_url_path"](  # type: ignore
                os.path.basename(url_parts.path),
            ),
        )

    return functools.partial(loader_function, **function_kwargs)


def guess_preferred_serializer(url: str) -> tuple[str, str]:
    """Guess preferred serializer for URL.

    Args:
        url (str): URL to guess serializer for.

    Returns:
        tuple: Filename and serializer.
    """
    try:
        url, serializer_name = url.rsplit("?", maxsplit=1)
    except ValueError:
        url_parts = urllib.parse.urlsplit(url)
        ext = os.path.splitext(url_parts.path)[-1].lstrip(".")
        if f".{ext}" in serializers:
            return url, ext
        return url, _identify_serializer(os.path.basename(url_parts.path))
    else:
        return url, serializer_name


def _file_can_not_be_serialized_as_object_error(
    url: str,
    error_message: str,
) -> str:
    return f"'{url}' can't be serialized as a valid object:{error_message}"


def deserialize_for_url(
    url: str,
    content: Any,
    prefer_serializer: str | None = None,
) -> Any:
    """Deserialize content for URL.

    Args:
        url (str): URL to deserialize content for.
        content (Any): Content to deserialize.
        prefer_serializer (str): Preferred serializer.

    Returns:
        str: Deserialized content.
    """
    return _get_serializer_function(
        url,
        prefer_serializer=prefer_serializer,
        loader_function_name="dumps",
    )(content)


def serialize_for_url(
    url: str,
    string: str,
    prefer_serializer: str | None = None,
) -> Any:
    """Serializes to JSON a string according to the given URI.

    Args:
        url (str): URI of the file, used to detect the type of the file,
            either using the extension or through `identify`_.
        string (str): File content to serialize.
        prefer_serializer (str): Preferred serializer.

    Returns:
        dict: Result of the object serialization.

    .. _identify: https://github.com/pre-commit/identify
    """
    try:
        # serialize
        result = _get_serializer_function(
            url,
            prefer_serializer=prefer_serializer,
        )(
            string,
        )
    except Exception:
        # handle exceptions in third party packages without importing them
        exc_class, exc, _ = sys.exc_info()
        package_name = exc_class.__module__.split(".")[0]
        if package_name in (  # Examples:
            "json",  # json.serializer.JSONDecodeError
            "pyjson5",  # pyjson5.Json5IllegalCharacter
            "tomli",  # tomli.TOMLDecodeError
            "tomlkit",  # tomlkit.exceptions.UnexpectedEofError
        ):
            raise SerializerError(
                _file_can_not_be_serialized_as_object_error(
                    url,
                    f" {exc.args[0]}",  # type: ignore
                ),
            ) from None
        if package_name == "ruamel":
            raise SerializerError(
                _file_can_not_be_serialized_as_object_error(
                    url,
                    f"\n{str(exc)}",
                ),
            ) from None
        raise  # pragma: no cover
    return result
