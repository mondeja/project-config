import abc
import typing as t
from dataclasses import dataclass, field as dataclass_field

from project_config.exceptions import ProjectConfigCheckFailedBase


class AbstractReporter(abc.ABC):
    

    @abc.abstractmethod
    def generate_report(self) -> str:
        pass


@dataclass
class BaseReporterDataClass:
    # Workaround for: https://github.com/python/mypy/issues/5374
    # see https://github.com/python/mypy/issues/5374#issuecomment-568335302

    errors: t.Dict[str, t.List[str]] = dataclass_field(
        default_factory=dict,  # {file: [...errors...]}
    )


class BaseReporter(AbstractReporter, BaseReporterDataClass):
    exception_class = ProjectConfigCheckFailedBase

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def run(self) -> None:
        if not self.success:
            raise self.exception_class(self.generate_report())

    def report(self, error: t.Dict[str, str]) -> None:
        if error["file"] not in self.errors:
            self.errors[error["file"]] = []
        self.errors[error["file"]].append(error["message"])
