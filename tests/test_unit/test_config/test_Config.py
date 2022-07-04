"""Tests for Config class API."""


import pytest

from project_config.config import Config
from project_config.config.exceptions import ConfigurationFilesNotFound


def test_Config___getitem__(
    tmp_path,
    chdir,
    minimal_valid_config,
    minimal_valid_style,
):
    (tmp_path / "foo.json").write_text(minimal_valid_style.string)
    (tmp_path / "pyproject.toml").write_text(
        f"[tool.project-config]\n{minimal_valid_config.string}",
    )

    with chdir(tmp_path):
        config = Config(str(tmp_path), None)
        assert config["style"] == "foo.json"
        config.load_style()
        assert config["style"] == {"rules": [{"files": ["foo"]}]}
    assert isinstance(config.dict_, dict)


def test_Config_fails(tmp_path, chdir):
    with chdir(tmp_path), pytest.raises(ConfigurationFilesNotFound):
        Config(str(tmp_path), None)
