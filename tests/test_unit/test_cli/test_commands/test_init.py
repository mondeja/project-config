import pytest

from project_config.__main__ import run


def test_init_default(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        assert run(["init"]) == 0

        out, err = capsys.readouterr()
        assert err == ""
        assert out == "Configuration initialized at .project-config.toml\n"

        project_config_toml_file = tmp_path / ".project-config.toml"
        assert project_config_toml_file.exists()
        assert project_config_toml_file.read_text() == (
            'style = ["style.json5"]\ncache = "5 minutes"\n'
        )

        style_file = tmp_path / "style.json5"
        assert style_file.exists()

        assert run(["check"]) == 0


def test_init_pyproject_toml(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        assert run(["init", "-c", "pyproject.toml"]) == 0

        out, err = capsys.readouterr()
        assert err == ""
        assert out == (
            "Configuration initialized at pyproject.toml[tool.project-config]\n"
        )

        project_config_toml_file = tmp_path / "pyproject.toml"
        assert project_config_toml_file.exists()
        assert project_config_toml_file.read_text() == (
            '[tool.project-config]\nstyle = ["style.json5"]\n'
            'cache = "5 minutes"\n'
        )

        style_file = tmp_path / "style.json5"
        assert style_file.exists()

        assert run(["check"]) == 0


def test_init_custom_file(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        assert run(["init", "-c", "custom-file.toml"]) == 0

        out, err = capsys.readouterr()
        assert err == ""
        assert out == "Configuration initialized at custom-file.toml\n"

        project_config_toml_file = tmp_path / "custom-file.toml"
        assert project_config_toml_file.exists()
        assert project_config_toml_file.read_text() == (
            'style = ["style.json5"]\ncache = "5 minutes"\n'
        )

        style_file = tmp_path / "style.json5"
        assert style_file.exists()

        assert run(["check", "-c", "custom-file.toml"]) == 0


@pytest.mark.parametrize(
    "filename",
    (
        ".project-config.toml",
        "pyproject.toml.toml",
        "custom-file.toml",
    ),
)
def test_init_file_already_exists(filename, tmp_path, chdir, capsys):
    with chdir(tmp_path):
        file = tmp_path / filename
        file.write_text('\nfoo = "bar"\n')
        assert run(["init", "-c", filename]) == 1

        out, err = capsys.readouterr()
        assert out == ""
        assert err == (
            "The configuration for project-config has already been"
            f" initialized at {filename}\n"
        )


def test_toml_file_already_exists_but_section_not_found(
    tmp_path,
    chdir,
    capsys,
):
    with chdir(tmp_path):
        file = tmp_path / "pyproject.toml"
        file.write_text('[tool.poetry]\nname = "foo"\n')
        assert run(["init", "-c", "pyproject.toml"]) == 0

        out, err = capsys.readouterr()
        assert out == (
            "Configuration initialized at pyproject.toml"
            "[tool.project-config]\n"
        )
        assert err == ""

        assert (
            file.read_text()
            == """[tool.poetry]
name = "foo"

[tool.project-config]
style = ["style.json5"]
cache = "5 minutes"
"""
        )

        style_file = tmp_path / "style.json5"
        assert style_file.exists()

        assert run(["check"]) == 0
