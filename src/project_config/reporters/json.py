from project_config.reporters.base import BaseReporter
from project_config.exceptions import ProjectConfigCheckFailedBase

import json


class ProjectConfigJsonReporter(BaseReporter):
    @property
    def exception_class(self):
        return ProjectConfigCheckFailedBase

    def generate_report(self) -> str:
        return json.dumps(self.errors_by_files)
