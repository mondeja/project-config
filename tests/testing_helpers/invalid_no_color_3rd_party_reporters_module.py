"""Invalid reporters module because does not expose a color reporter."""

from project_config.reporters.base import BaseReporter


class ValidReporter(BaseReporter):
    pass
