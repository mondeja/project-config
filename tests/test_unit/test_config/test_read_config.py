import pytest

from project_config.config import read_config
from project_config.config.exceptions import (
    ConfigurationFilesNotFound,
    CustomConfigFileNotFound,
    PyprojectTomlFoundButHasNoConfig,
)


def test_read_config_from_custom_file(tmp_path, minimal_valid_config):
    input_path = tmp_path / "custom-file.toml"
    input_path.write_text(minimal_valid_config.string)
    output_path, config = read_config(input_path.as_posix())

    assert output_path == input_path.as_posix()
    minimal_valid_config.asserts(config)


def test_read_config_from_non_existent_custom_file(tmp_path):
    input_path = tmp_path / "custom-file.toml"
    with pytest.raises(CustomConfigFileNotFound):
        read_config(input_path)


def test_read_config_from_empty_custom_file(tmp_path):
    """Succeeds because config files are validated later."""
    input_path = tmp_path / "custom-file.toml"
    input_path.write_text("")
    read_config(input_path.as_posix())


def test_read_config_from_project_config_toml(
    tmp_path,
    minimal_valid_config,
    chdir,
):
    path = tmp_path / ".project-config.toml"
    path.write_text(minimal_valid_config.string)
    with chdir(tmp_path):
        output_path, config = read_config()
    assert output_path == path.name
    minimal_valid_config.asserts(config)


def test_read_config_from_pyproject_toml(tmp_path, minimal_valid_config, chdir):
    path = tmp_path / "pyproject.toml"
    path.write_text(f"[tool.project-config]\n{minimal_valid_config.string}")
    with chdir(tmp_path):
        output_path, config = read_config()

    assert output_path == f'"{path.name}".[tool.project-config]'
    minimal_valid_config.asserts(config)


def test_read_config_from_default_files_project_config_toml_precedence(
    tmp_path,
    minimal_valid_config,
    chdir,
):
    """.project-config.toml takes precedence over pyproject.toml
    when both files exists.
    """
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(minimal_valid_config.with_style("pyproject"))

    project_config_path = tmp_path / ".project-config.toml"
    project_config_path.write_text(
        minimal_valid_config.with_style("project-config"),
    )

    with chdir(tmp_path):
        output_path, config = read_config()
    assert output_path == project_config_path.name
    minimal_valid_config.asserts(config, expected_style="project-config")


def test_pyproject_toml_no_section(
    tmp_path,
    chdir,
):
    path = tmp_path / "pyproject.toml"
    path.write_text("")

    with chdir(tmp_path), pytest.raises(PyprojectTomlFoundButHasNoConfig):
        read_config()


def test_config_files_not_found(
    tmp_path,
    chdir,
):
    with chdir(tmp_path), pytest.raises(ConfigurationFilesNotFound):
        read_config()
