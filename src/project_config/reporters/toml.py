import typing as t

import tomlkit

from project_config.reporters.base import BaseReporter


class ProjectConfigTomlReporter(BaseReporter):
    def generate_report(self) -> t.Any:
        return tomlkit.dumps(self.errors)
