from dataclasses import dataclass


@dataclass
class ProjectConfigException(Exception):
    message: str


class ProjectConfigCheckFailedBase(ProjectConfigException):
    pass


class ProjectConfigNotImplementedError(ProjectConfigException, NotImplementedError):
    pass
