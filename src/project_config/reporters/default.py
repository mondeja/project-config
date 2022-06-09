from project_config.reporters.base import BaseReporter


class ProjectConfigDefaultReporter(BaseReporter):
    def generate_report(self) -> str:
        report_message = ""
        for file, error_messages in self.errors.items():
            report_message += f"{file}\n"
            for error_message in error_messages:
                report_message += f"  - {error_message}\n"
        return report_message.rstrip("\n")
