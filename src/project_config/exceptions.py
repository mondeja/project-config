from dataclasses import dataclass


@dataclass
class ProjectConfigException(Exception):
    message: str
