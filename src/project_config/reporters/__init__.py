from project_config.reporters.default import ProjectConfigDefaultReporter
from project_config.reporters.json import ProjectConfigJsonReporter

reporters = {
    "default": ProjectConfigDefaultReporter,
    "json": ProjectConfigJsonReporter,
}
