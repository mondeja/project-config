import json

from project_config.reporters.base import BaseReporter


class ProjectConfigJsonReporter(BaseReporter):
    def generate_report(self) -> str:
        return json.dumps(self.errors)
