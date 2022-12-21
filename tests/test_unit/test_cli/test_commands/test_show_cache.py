"""Tests for 'project-config show cache' command."""

from project_config.__main__ import run
from project_config.cache import (
    CACHE_DIR as EXPECTED_CACHE_DIR,
    generate_possible_cache_dirs,
)


def test_show_cache(capsys):
    possible_cache_dirs = list(generate_possible_cache_dirs())

    assert run(["show", "cache"]) == 0
    out, err = capsys.readouterr()
    assert err == ""

    cache_dir = out.rstrip("\r\n")
    assert cache_dir == EXPECTED_CACHE_DIR
    assert cache_dir in possible_cache_dirs
