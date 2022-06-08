import abc
import typing as t

from dataclasses import dataclass, field as dataclass_field


@dataclass
class BaseReporter(abc.ABC):
    errors_by_files: t.Dict[str, t.List[str]] = dataclass_field(
        default_factory=dict,
    )

    @property
    def success(self) -> bool:
        return len(self.errors_by_files) == 0

    def run(self) -> None:
        if not self.success:
            raise self.exception_class(self.generate_report())
    
    def report(self, error: t.Dict[str, str]) -> None:
        if error["file"] not in self.errors_by_files:
            self.errors_by_files[error["file"]] = []
        self.errors_by_files[error["file"]].append(error["message"])
    
    @property
    @abc.abstractmethod
    def exception_class(self):
        pass
    
    @abc.abstractmethod
    def generate_report(self):
        pass
