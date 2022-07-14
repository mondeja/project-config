"""Pytest plugin for project-config."""

from __future__ import annotations

import pytest


pytest.register_assert_rewrite("project_config.tests.pytest_plugin.plugin")
pytest.register_assert_rewrite("project_config.tests.pytest_plugin.helpers")

from project_config.tests.pytest_plugin.plugin import (  # noqa: E402
    project_config_data_report_asserter,
    project_config_errors_report_asserter,
    project_config_plugin_action_asserter,
)


__all__ = (
    "project_config_data_report_asserter",
    "project_config_errors_report_asserter",
    "project_config_plugin_action_asserter",
)
