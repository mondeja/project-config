from project_config.__main__ import run
from project_config.cache import Cache


def test_show_cache(capsys):
    assert run(["show", "cache"]) == 0
    out, err = capsys.readouterr()
    assert out == f"{Cache.get_directory()}\n"
    assert err == ""
