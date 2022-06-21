"""Base reporters."""

import abc
import os
import typing as t

import colored

from project_config.compat import TypeAlias
from project_config.exceptions import ProjectConfigCheckFailedBase
from project_config.types import ErrorDict


FilesErrors: TypeAlias = t.Dict[str, t.List[ErrorDict]]


class BaseReporter(abc.ABC):
    """Base reporter from which all reporters inherit."""

    exception_class = ProjectConfigCheckFailedBase

    def __init__(
        self,
        rootdir: str,
        fmt: t.Optional[str] = None,
    ):
        self.rootdir = rootdir
        self.errors: FilesErrors = {}
        self.format = fmt

        # configuration, styles...
        self.data: t.Dict[str, t.Any] = {}

    @abc.abstractmethod
    def generate_errors_report(self) -> str:
        """Generate check errors report.

        This method must be implemented by inherited reporters.
        """

    def generate_data_report(
        self,
        data_key: str,
        data: t.Dict[str, t.Any],
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
            file = os.path.relpath(error["file"], self.rootdir) + (
                "/" if error["file"].endswith("/") else ""
            )
        else:
            file = "[CONFIGURATION]"

        if file not in self.errors:
            self.errors[file] = []

        self.errors[file].append(error)


class BaseFormattedReporter(BaseReporter, abc.ABC):
    """Reporter that requires formatted fields."""

    @abc.abstractmethod
    def format_file(self, fname: str) -> str:
        """File name formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_error_message(self, error_message: str) -> str:
        """Error message formatter."""
        raise NotImplementedError

    @abc.abstractmethod
    def format_definition(self, definition: str) -> str:
        """Definition formatter."""
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


self_format_noop: t.Callable[[type, str], str] = lambda s, v: v


class BaseNoopFormattedReporter(BaseFormattedReporter):
    """Reporter that requires formatted fields without format."""

    def format_file(self, fname: str) -> str:  # noqa: D102
        return fname

    def format_error_message(self, error_message: str) -> str:  # noqa: D102
        return error_message

    def format_definition(self, definition: str) -> str:  # noqa: D102
        return definition

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


class BaseColorReporter(BaseFormattedReporter):
    """Base reporter with colorized output."""

    def format_file(self, fname: str) -> str:  # noqa: D102
        return bold_color(fname, "light_red")

    def format_error_message(self, error_message: str) -> str:  # noqa: D102
        return bold_color(error_message, "yellow")

    def format_definition(self, definition: str) -> str:  # noqa: D102
        return bold_color(definition, "blue")

    def format_key(self, key: str) -> str:  # noqa: D102
        return bold_color(key, "green")

    def format_metachar(self, metachar: str) -> str:  # noqa: D102
        return bold_color(metachar, "grey_37")

    def format_config_key(self, config_key: str) -> str:  # noqa: D102
        return bold_color(config_key, "blue")

    def format_config_value(self, config_value: str) -> str:  # noqa: D102
        return bold_color(config_value, "yellow")
