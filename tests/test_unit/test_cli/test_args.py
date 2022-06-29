import os

import pytest

from project_config.__main__ import run


@pytest.mark.parametrize("arg", ("--nocache", "--no-cache"))
def test_nocache_option_sets_environment_variable(
    tmp_path,
    chdir,
    capsys,
    monkeypatch,
    arg,
):
    monkeypatch.setenv("PROJECT_CONFIG_USE_CACHE", "true")
    with chdir(tmp_path):
        run(["check", arg])
    assert os.environ.get("PROJECT_CONFIG_USE_CACHE") == "false"
    capsys.readouterr()
