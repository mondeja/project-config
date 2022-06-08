from project_config.reporters.base import BaseReporter
from project_config.exceptions import ProjectConfigCheckFailed


class ProjectConfigDefaultReporter(BaseReporter):
    @property
    def exception_class(self):
        return ProjectConfigCheckFailed

    def generate_report(self) -> str:
        report_message = ""
        for file, error_messages in self.errors_by_files.items():
            report_message += f"  {file}\n"
            for error_message in error_messages:
                report_message += f"    - {error_message}\n"
        return report_message.rstrip("\n")

