from project_config.reporters.base import BaseReporter


class ValidBasedReporter(BaseReporter):
    def generate_errors_report(self):
        pass

    def generate_data_report(self, data_key, data):
        pass


class InvalidNotBasedColorReporter:
    pass
