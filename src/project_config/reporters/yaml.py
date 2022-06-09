import json
import yaml
try:
    from yaml import CSafeLoader as Loader, CSafeDumper as Dumper
except ImportError:
    from yaml import SafeLoader as Loader, SafeDumper as Dumper


from project_config.reporters.base import BaseReporter


class ProjectConfigYamlReporter(BaseReporter):
    def generate_report(self) -> str:
        return yaml.dump(
            yaml.load(
                json.dumps(self.errors),
                Loader=Loader,
            ),
            Dumper=Dumper,
            default_flow_style=False,
        )
