"""Github flavored Markdown reporters."""

from __future__ import annotations

import json
import os
from typing import Any

from project_config.compat import (
    cached_function,
    importlib_metadata as im,
)
from project_config.reporters.base import (
    BaseNoopFormattedReporter,
)


CONFIG_SETTINGS_DOCS_TITLES = {
    "style": "style-string-or-string",
    "cache": "cache-string",
    "cli": "cli-object",
}


def maybe_write_report_to_github_summary(report: str) -> None:
    """Write report to Github summary if available."""
    github_step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if github_step_summary_path is not None and os.path.isfile(
        github_step_summary_path,
    ):
        with open(github_step_summary_path, "a", encoding="utf-8") as f:
            f.write(report)


def plugin_or_verb_docs_url_prefix() -> str:
    """Return the URL to the plugin docs."""
    return (
        "https://mondeja.github.io/project-config/"
        f"{im.version('project-config')}/reference/plugins.html#"
    )


@cached_function
def config_docs_url_prefix() -> str:
    """Return the URL to the config docs."""
    return (
        "https://mondeja.github.io/project-config/"
        f"{im.version('project-config')}/reference/config.html#"
    )


def config_docs_markdown_link(key: str) -> str:
    """Return the markdown link to the config docs."""
    if key not in CONFIG_SETTINGS_DOCS_TITLES:
        return key
    return (
        f"[{key}]({config_docs_url_prefix()}{CONFIG_SETTINGS_DOCS_TITLES[key]})"
    )


@cached_function
def styling_docs_url_prefix() -> str:
    """Return the URL to the styling docs."""
    return (
        "https://mondeja.github.io/project-config/"
        f"{im.version('project-config')}/reference/styling.html#"
    )


class GithubFlavoredMarkdownReporter(BaseNoopFormattedReporter):
    """Github flavored Markdown reporter."""

    def raise_errors(self, errors_report: str | None = None) -> None:
        """Raise errors failure if no success.

        Raise the correspondent exception class for the reporter
        if the reporter has reported any error.
        """
        errors_report = self.generate_errors_report()
        maybe_write_report_to_github_summary(errors_report)

        super().raise_errors(errors_report=errors_report)

    def generate_errors_report(self) -> str:
        """Generate errors report in custom project-config format."""
        n_errors = sum(len(errors) for errors in self.errors.values())
        n_files = len(self.errors)

        report = (
            "## Summary\n\n"
            f"Found {n_errors} errors in {n_files} file"
            f"{'s' if n_files > 1 else ''}.\n\n"
        )

        report += "## Errors\n\n"
        for file, errors in self.errors.items():
            report += f"<details>\n  <summary>{file}</summary>\n\n"
            for error in errors:
                fixed_item = (
                    "  :hammer_and_wrench: FIXED\n\n"
                    if error.get("fixed")
                    else (
                        "  :wrench: FIXABLE\n\n"
                        if error.get("fixable", False)
                        else ""
                    )
                )
                report += (
                    f"- :x: {error['message']}\n\n{fixed_item}"
                    f"  :writing_hand: <code>{error['definition']}</code>\n\n"
                )
                if "hint" in error:
                    report += f"  :bell: **{error['hint']}**\n\n"
            report += "</details>\n\n"

        return report

    def generate_data_report(
        self,
        data_key: str,
        data: dict[str, Any],
    ) -> str:
        """Generate data report in Github flavored Markdown format."""
        report = ""
        if data_key == "style":
            # TODO: Better output for style with details over each rule
            rules = data.get("rules", [])
            report += (
                f"## [Styles]({styling_docs_url_prefix().rstrip('#')})\n\n"
                f"<details>\n  <summary>Show {len(rules)} rules</summary>\n\n"
            )
            if len(rules) > 0:
                report += f"```json\n{json.dumps(rules, indent=2)}\n```\n"
            report += "</details>\n\n"
        elif data_key == "plugins":
            url_prefix = plugin_or_verb_docs_url_prefix()
            report += f"## [Plugins]({url_prefix.rstrip('#')})\n\n"
            for plugin_name, plugin_verbs in data.items():
                report += (
                    f"### **[{plugin_name}]"
                    f"({url_prefix}{plugin_name.lower()})**\n\n"
                )
                for verb in plugin_verbs:
                    report += f"- [{verb}]({url_prefix}{verb.lower()})\n"
                report += "\n"
        else:
            report += (
                "## [Configuration]"
                f"({config_docs_url_prefix().rstrip('#')})\n\n"
            )
            for key, value in data.items():
                report += f"- **{config_docs_markdown_link(key)}**:"
                if isinstance(value, list):
                    report += "\n"
                    for value_item in value:
                        report += f"  - {value_item}\n"
                elif isinstance(value, dict):
                    report += "\n"
                    for value_k, value_v in value.items():
                        report += f"  - **{value_k}**: {value_v}\n"
                else:
                    report += f" {value}\n"
        maybe_write_report_to_github_summary(report)
        return report.rstrip()


class GithubFlavoredMarkdownColorReporter(  # noqa: D101
    GithubFlavoredMarkdownReporter,
):
    pass
