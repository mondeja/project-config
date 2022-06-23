from project_config.reporters.base import BaseColorReporter


class ValidBasedColorReporter(BaseColorReporter):
    def generate_errors_report(self):
        pass

    def generate_data_report(self, data_key, data):
        pass


class InvalidNotBasedReporter:
    pass
