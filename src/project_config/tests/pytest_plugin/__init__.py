"""Pytest plugin for project-config."""

import pytest


pytest.register_assert_rewrite("project_config.tests.pytest_plugin.plugin")

from project_config.tests.pytest_plugin.plugin import (  # noqa: E402
    _create_files,
    _create_tree,
    project_config_plugin_action_asserter,
)


__all__ = (
    "_create_files",
    "_create_tree",
    "project_config_plugin_action_asserter",
)
