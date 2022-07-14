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

        assert run(["fix"]) == 0
        out, err = capsys.readouterr()
        assert err == ""
        assert out == ""


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

        assert run(["fix"]) == 0
        out, err = capsys.readouterr()
        assert err == ""
        assert out == ""


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

        exitcode = run(["fix", "--config", "custom-file.toml"])
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == "", msg
        assert out == "", msg
        assert exitcode == 0


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

        assert run(["fix"]) == 0
        out, err = capsys.readouterr()
        assert err == ""
        assert out == ""


def test_toml_file_already_exists_and_section_found(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        file = tmp_path / "pyproject.toml"
        file.write_text(
            '[tool.project-config]\nstyle = ["style.json5"]\n'
            'cache = "5 minutes"\n',
        )
        assert run(["init", "-c", "pyproject.toml"]) == 1

        out, err = capsys.readouterr()
        assert out == ""
        assert err == (
            "The configuration for project-config has already been"
            " initialized at pyproject.toml[tool.project-config]\n"
        )


def test_project_config_ini_is_fixable(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        project_config_file = tmp_path / ".project-config.toml"
        style_file = tmp_path / "style.json5"

        assert run(["init"]) == 0
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == "", msg
        assert out == "Configuration initialized at .project-config.toml\n", msg

        expected_project_config_content = (
            'style = ["style.json5"]\ncache = "5 minutes"\n'
        )
        assert (
            project_config_file.read_text() == expected_project_config_content
        )
        project_config_file.write_text("")
        assert style_file.exists()

        config_file = tmp_path / "custom-file.toml"
        config_file.write_text('style = ["style.json5"]\n')

        exitcode = run(["fix", "--config", "custom-file.toml", "--no-color"])
        assert (
            project_config_file.read_text() == expected_project_config_content
        )
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err.count("(FIXED)") == 3, msg
        assert out == "", msg
        assert exitcode == 1, msg

        exitcode = run(["fix", "--config", "custom-file.toml", "--no-color"])
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == "", msg
        assert out == "", msg
        assert exitcode == 0, msg


def test_pyproject_toml_ini_is_fixable(tmp_path, chdir, capsys):
    with chdir(tmp_path):
        pyproject_toml_file = tmp_path / "pyproject.toml"
        style_file = tmp_path / "style.json5"

        assert run(["init", "-c", "pyproject.toml"]) == 0
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == "", msg
        assert (
            out
            == "Configuration initialized at pyproject.toml[tool.project-config]\n"
        ), msg

        expected_pyproject_toml_content = '[tool.project-config]\nstyle = ["style.json5"]\ncache = "5 minutes"\n'
        assert (
            pyproject_toml_file.read_text() == expected_pyproject_toml_content
        )
        pyproject_toml_file.write_text("")
        assert style_file.exists()

        config_file = tmp_path / "custom-file.toml"
        config_file.write_text('style = ["style.json5"]\n')

        exitcode = run(["fix", "--config", "custom-file.toml", "--no-color"])
        assert (
            pyproject_toml_file.read_text() == expected_pyproject_toml_content
        )
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err.count("(FIXED)") == 5, msg
        assert out == "", msg
        assert exitcode == 1, msg

        exitcode = run(["fix", "--config", "custom-file.toml", "--no-color"])
        out, err = capsys.readouterr()
        msg = f"{out}\n---\n{err}"
        assert err == "", msg
        assert out == "", msg
        assert exitcode == 0, msg
