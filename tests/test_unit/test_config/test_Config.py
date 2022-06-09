"""Tests for Config class API."""

import json

import pytest

from project_config.config import Config
from project_config.config.exceptions import ConfigurationFilesNotFound


def test_Config___getitem__(tmp_path, chdir, minimal_valid_config, minimal_valid_style):
    (tmp_path / "foo").write_text(minimal_valid_style.string)
    (tmp_path / "pyproject.toml").write_text(
        f"[tool.project-config]\n{minimal_valid_config.string}"
    )

    with chdir(tmp_path):
        config = Config(None)
    assert config["style"] == "foo"


def test_Config_fails(tmp_path, chdir):
    with chdir(tmp_path), pytest.raises(ConfigurationFilesNotFound):
        config = Config(None)
