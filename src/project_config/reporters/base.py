import abc
import os
import typing as t

import simple_chalk as chalk

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

    @abc.abstractmethod
    def generate_report(self) -> str:
        pass

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def run(self) -> None:
        if not self.success:
            raise self.exception_class(self.generate_report())

    def report(self, error: t.Dict[str, str]) -> None:
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


class BaseColorReporter(BaseFormattedReporter):
    format_file = chalk.bold.redBright
    format_error_message = chalk.bold.yellow
    format_definition = chalk.bold.blue

    format_key = chalk.bold.green
    format_metachar = chalk.yellowBright
