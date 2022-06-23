"""Invalid reporters module because does not expose a black/white reporter."""

from project_config.reporters.base import BaseReporter


class ValidColorReporter(BaseReporter):
    pass


class OtherValidColorReporter(BaseReporter):
    pass


class ValidReporter(BaseReporter):
    pass
