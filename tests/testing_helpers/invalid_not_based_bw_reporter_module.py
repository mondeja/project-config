from project_config.reporters.base import BaseColorReporter


class ValidBasedColorReporter(BaseColorReporter):
    def generate_errors_report(self):
        pass

    def generate_data_report(self, data_key, data):  # noqa: U100
        pass


class InvalidNotBasedReporter:
    pass
