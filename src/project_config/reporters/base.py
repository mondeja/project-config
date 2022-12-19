"""Base reporters."""

from __future__ import annotations

import abc
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import colored

from project_config.exceptions import (
    ProjectConfigCheckFailed,
    ProjectConfigException,
)


if TYPE_CHECKING:
    from project_config.compat import TypeAlias
    from project_config.types import ErrorDict

    FilesErrors: TypeAlias = dict[str, list[ErrorDict]]
    FormatterDefinitionType: TypeAlias = Callable[[str], str]


class InvalidColors(ProjectConfigException):
    """Invalid not supported colors in colored formatter."""

    def __init__(self, errors: list[str]):
        message = (
            "Invalid colors or subjects in 'colors' configuration"
            " for reporters:\n"
        )
        for error in errors:
            message += f"  - {error}\n"
        super().__init__(message)


class BaseReporter(abc.ABC):
    """Base reporter from which all reporters inherit."""

    __slots__ = {
        "rootdir",
        "errors",
        "format",
        "only_hints",
        "data",
    }

    exception_class = ProjectConfigCheckFailed

    def __init__(
        self,
        rootdir: str,
        fmt: str | None = None,
        only_hints: bool = False,
    ):
        self.rootdir = rootdir
        self.errors: FilesErrors = {}
        self.format = fmt
        self.only_hints = only_hints

        # configuration, styles...
        self.data: dict[str, Any] = {}

    @abc.abstractmethod
    def generate_errors_report(self) -> str:
        """Generate check errors report.

        This method must be implemented by inherited reporters.
        """

    def generate_data_report(
        self,
        data_key: str,  # noqa: U100
        data: dict[str, Any],  # noqa: U100
    ) -> str:
        """Generate data report for configuration or styles.

        This method should be implemented by inherited reporters.

        Args:
            data_key (str): Configuration for which the data will
                be generated. Could be either ``"config"`` or
                ``"style"``.
            data (dict): Data to report.
        """
        raise NotImplementedError

    @property
    def success(self) -> bool:
        """Return if the reporter has not reported errors.

        Returns:
            bool: ``True`` if no errors reported, ``False`` otherwise.
        """
        return len(self.errors) == 0

    def raise_errors(self) -> None:
        """Raise errors failure if no success.

        Raise the correspondent exception class for the reporter
        if the reporter has reported any error.
        """
        if not self.success:
            raise self.exception_class(self.generate_errors_report())

    def report_error(self, error: ErrorDict) -> None:
        """Report an error.

        Args:
            error (dict): Error to report.
        """
        if "file" in error:
            file = error.pop("file")
            file = os.path.relpath(file, self.rootdir) + (
                "/" if file.endswith("/") else ""
            )
        else:
            file = "[CONFIGURATION]"  # pragma: no cover

        if file not in self.errors:
            self.errors[file] = []

        if "hint" in error and self.only_hints:
            error["message"] = error.pop("hint")

        self.errors[file].append(error)


class BaseFormattedReporter(BaseReporter, abc.ABC):
    """Reporter that requires formatted fields."""

    @abc.abstractmethod
    def format_fixed(self, output: str) -> str:
        """File name formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_file(self, fname: str) -> str:
        """File name formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_error_message(
        self,
        error_message: str,
    ) -> str:
        """Error message formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_definition(self, definition: str) -> str:
        """Definition formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_hint(self, hint: str) -> str:
        """Hint formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_key(self, key: str) -> str:
        """Serialized key formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_metachar(self, metachar: str) -> str:
        """Meta characters string formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_config_key(self, config_key: str) -> str:
        """Configuration data key formatter, for example 'style'."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_config_value(self, config_value: str) -> str:
        """Configuration data value formatter, for example 'style' urls."""
        raise NotImplementedError


self_format_noop: Callable[[type, str], str] = lambda self, v: v


class BaseNoopFormattedReporter(BaseFormattedReporter):
    """Reporter that requires formatted fields without format."""

    def format_fixed(self, output: str) -> str:  # noqa: D102
        return output

    def format_file(self, fname: str) -> str:  # noqa: D102
        return fname

    def format_error_message(self, error_message: str) -> str:  # noqa: D102
        return error_message

    def format_definition(self, definition: str) -> str:  # noqa: D102
        return definition

    def format_hint(self, hint: str) -> str:  # noqa: D102
        return hint

    def format_key(self, key: str) -> str:  # noqa: D102
        return key

    def format_metachar(self, metachar: str) -> str:  # noqa: D102
        return metachar

    def format_config_key(self, config_key: str) -> str:  # noqa: D102
        return config_key

    def format_config_value(self, config_value: str) -> str:  # noqa: D102
        return config_value


def bold_color(value: str, color: str) -> str:
    """Colorize a string with bold formatting using `colored`_ library.

    .. _colored: https://gitlab.com/dslackw/colored

    Args:
        value (str): Value to colorize.
        color (str): Color to use for the formatting.

    Returns:
        str: Colorized string.
    """
    return colored.stylize(  # type: ignore
        value,
        colored.fg(color) + colored.attr("bold"),
    )


def colored_color_exists(color: str) -> bool:
    """Check if a color exists in the `colored`_ library.

    .. _colored: https://gitlab.com/dslackw/colored

    Args:
        color (str): Color to check.

    Returns:
        bool: ``True`` if the color exists, ``False`` otherwise.
    """
    try:
        colored.fg(color)
    except KeyError:  # pragma: no cover (tested, but not supported on CI)
        return False
    else:
        return True


class BaseColorReporter(BaseFormattedReporter):
    """Base reporter with colorized output."""

    def __init__(
        self,
        *args: Any,
        colors: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.colors = self._normalize_colors(colors or {})
        super().__init__(*args, **kwargs)

    def _normalize_colors(self, colors: dict[str, str]) -> dict[str, str]:
        normalized_colors: dict[str, str] = {}
        errors: list[str] = []
        for subject, color in colors.items():
            normalized_subject = (
                subject.lower().replace("-", "_").replace(" ", "_")
            )
            if not hasattr(self, f"format_{normalized_subject}"):
                errors.append(
                    f"Invalid subject '{normalized_subject}' to colorize",
                )
            if not colored_color_exists(color):  # pragma: no cover
                errors.append(f"Color '{color}' not supported")
            normalized_colors[normalized_subject] = color
        if errors:
            raise InvalidColors(errors)
        return normalized_colors

    def format_fixed(self, output: str) -> str:  # noqa: D102
        return bold_color(output, self.colors.get("fixed", "green"))

    def format_file(self, fname: str) -> str:  # noqa: D102
        return bold_color(fname, self.colors.get("file", "light_red"))

    def format_error_message(self, error_message: str) -> str:  # noqa: D102
        return bold_color(
            error_message,
            self.colors.get("error_message", "yellow"),
        )

    def format_definition(self, definition: str) -> str:  # noqa: D102
        return bold_color(definition, self.colors.get("definition", "blue"))

    def format_hint(self, hint: str) -> str:  # noqa: D102
        return bold_color(hint, self.colors.get("hint", "green"))

    def format_key(self, key: str) -> str:  # noqa: D102
        return bold_color(key, self.colors.get("key", "cyan"))

    def format_metachar(self, metachar: str) -> str:  # noqa: D102
        return bold_color(metachar, self.colors.get("metachar", "grey_37"))

    def format_config_key(self, config_key: str) -> str:  # noqa: D102
        return bold_color(config_key, self.colors.get("config_key", "blue"))

    def format_config_value(self, config_value: str) -> str:  # noqa: D102
        return bold_color(
            config_value,
            self.colors.get("config_value", "yellow"),
        )
