import json
import typing as t

import yaml


try:
    from yaml import CSafeDumper as Dumper, CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader, SafeDumper as Dumper  # type: ignore

from project_config.reporters.base import BaseReporter


class ProjectConfigYamlReporter(BaseReporter):
    def generate_report(self) -> t.Any:
        return yaml.dump(
            yaml.load(
                json.dumps(self.errors),
                Loader=Loader,
            ),
            Dumper=Dumper,
            default_flow_style=False,
        )
