"""Github flavored Markdown reporters."""

from __future__ import annotations

import json
import os
from typing import Any

from project_config.reporters.base import (
    BaseNoopFormattedReporter,
)


def maybe_write_report_to_github_summary(report: str) -> None:
    """Write report to Github summary if available."""
    github_step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if github_step_summary_path is not None and os.path.isfile(
        github_step_summary_path,
    ):
        with open(github_step_summary_path, "a", encoding="utf-8") as f:
            f.write(report)


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
                    "  :hammer_and_wrench: FIXED\n"
                    if error.get("fixed")
                    else (
                        "  :wrench: FIXABLE\n"
                        if error.get("fixable", False)
                        else ""
                    )
                )
                report += (
                    f"- :x: {error['message']}\n\n{fixed_item}"
                    f"  :writing_hand: <code>{error['definition']}</code>\n"
                )
                if "hint" in error:
                    report += f"  :bell: **{error['hint']}**\n"
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
            rootdir_name = os.path.basename(self.rootdir)
            report += (
                f"## project-config styles for {rootdir_name}\n\n"
                f"<details>\n  <summary>Show {len(rules)} rules</summary>\n\n"
            )
            if len(rules) > 0:
                report += f"```json\n{json.dumps(rules, indent=2)}\n```\n"
            report += "</details>\n\n"
        else:
            report += "## Configuration for project-config\n\n"
            for key, value in data.items():
                report += f"- **{key}**:"
                if isinstance(value, list):
                    report += "\n"
                    for value_item in value:
                        report += f"  - {value_item}\n"
                else:
                    report += f" {value}\n"
        maybe_write_report_to_github_summary(report)
        return report


GithubFlavoredMarkdownColorReporter = GithubFlavoredMarkdownReporter
