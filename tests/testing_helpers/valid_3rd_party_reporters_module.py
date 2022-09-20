from project_config.reporters.base import BaseReporter


class _ValidBaseReporter(BaseReporter):
    def generate_errors_report(self):
        pass

    def generate_data_report(self, data_key, data):  # noqa: U100
        pass


class ValidReporter(_ValidBaseReporter):
    pass


class ValidColorReporter(_ValidBaseReporter):
    pass
