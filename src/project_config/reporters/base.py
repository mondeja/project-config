import abc
import os
import typing as t

import colored

from project_config.exceptions import ProjectConfigCheckFailedBase


class BaseReporter(abc.ABC):
    exception_class = ProjectConfigCheckFailedBase

    def __init__(
        self,
        rootdir: str,
        errors: t.Dict[str, t.List[t.Dict[str, str]]] = {},
        format: t.Optional[str] = None,
    ):
        self.rootdir = rootdir
        self.errors = errors
        self.format = format

        # configuration, styles...
        self.data: t.Dict[str, t.Any] = {}

    @abc.abstractmethod
    def generate_errors_report(self) -> str:
        pass

    def generate_data_report(self, data_key: str, data: t.Dict[str, t.Any]) -> str:
        raise NotImplementedError

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def raise_errors(self) -> None:
        if not self.success:
            raise self.exception_class(self.generate_errors_report())

    def report_error(self, error: t.Dict[str, str]) -> None:
        file = os.path.relpath(error.pop("file"), self.rootdir)
        if file not in self.errors:
            self.errors[file] = []
        self.errors[file].append(error)


class BaseFormattedReporter(BaseReporter, abc.ABC):
    @abc.abstractmethod
    def format_file(self, fname: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def format_error_message(self, error_message: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def format_definition(self, definition: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def format_key(self, key: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def format_metachar(self, metachar: str) -> str:
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
    def format_file(self, fname: str) -> str:
        return fname

    def format_error_message(self, error_message: str) -> str:
        return error_message

    def format_definition(self, definition: str) -> str:
        return definition

    def format_key(self, key: str) -> str:
        return key

    def format_metachar(self, metachar: str) -> str:
        return metachar

    def format_config_key(self, config_key: str) -> str:
        return config_key

    def format_config_value(self, config_value: str) -> str:
        return config_value


def bold_color(value: str, color: str) -> str:
    return colored.stylize(value, colored.fg(color) + colored.attr("bold"))  # type: ignore


class BaseColorReporter(BaseFormattedReporter):
    def format_file(self, fname: str) -> str:
        return bold_color(fname, "light_red")

    def format_error_message(self, error_message: str) -> str:
        return bold_color(error_message, "yellow")

    def format_definition(self, definition: str) -> str:
        return bold_color(definition, "blue")

    def format_key(self, key: str) -> str:
        return bold_color(key, "green")

    def format_metachar(self, metachar: str) -> str:
        return bold_color(metachar, "grey_37")

    format_config_key = format_definition
    format_config_value = format_error_message
