import tomlkit

from project_config.reporters.base import BaseReporter


class ProjectConfigTomlReporter(BaseReporter):
    def generate_report(self) -> str:
        return tomlkit.dumps(self.errors)
