"""Common exceptions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectConfigException(Exception):
    """Base exception for all the exceptions in project-config."""

    message: str


class ProjectConfigCheckFailed(ProjectConfigException):
    """Exception raised when a ``check`` command has failed.

    Means that an error has been found in the style of the
    project when using the ``check`` command through the CLI.
    """


class ProjectConfigNotImplementedError(
    ProjectConfigException,
    NotImplementedError,
):
    """Some functionality is not yet implemented."""
