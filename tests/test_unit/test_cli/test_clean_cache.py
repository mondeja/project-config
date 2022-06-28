import os
import shutil

from project_config.__main__ import run
from project_config.cache import Cache


def test_clean_cache(capsys, tmp_path):
    cache_dir = Cache.get_directory()
    temp_cache_dir = str(tmp_path / "cache")
    if os.path.exists(cache_dir):
        shutil.copytree(cache_dir, temp_cache_dir)

    assert run(["clean", "cache"]) == 0
    out, err = capsys.readouterr()
    assert out == "Cache removed successfully!\n"
    assert err == ""

    if os.path.exists(temp_cache_dir):
        shutil.copytree(temp_cache_dir, cache_dir)
