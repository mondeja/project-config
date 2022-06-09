from dataclasses import dataclass


@dataclass
class ProjectConfigException(Exception):
    message: str


class ProjectConfigCheckFailedBase(ProjectConfigException):
    pass


class ProjectConfigCheckFailed(ProjectConfigCheckFailedBase):
    def __init__(self, errors_report: str):
        super().__init__(
            "Project configuration check has found failures:\n" f"{errors_report}"
        )

class ProjectConfigNotImplementedError(ProjectConfigException, NotImplementedError):
    pass
