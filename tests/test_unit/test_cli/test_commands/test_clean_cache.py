import os
import shutil
import sys

import pytest
from project_config.__main__ import run
from project_config.cache import CACHE_DIR, generate_possible_cache_dirs


@pytest.mark.skipif(
    "win" in sys.platform,
    reason="Failing on Windows due to PermissionError",
)
def test_clean_cache(capsys, tmp_path):
    temp_cache_dir = str(tmp_path / "cache")
    if os.path.exists(CACHE_DIR):
        shutil.copytree(CACHE_DIR, temp_cache_dir)

    assert run(["clean", "cache"]) == 0
    out, err = capsys.readouterr()
    assert out == "Cache removed successfully!\n"
    assert err == ""

    for possible_cache_dirpath in generate_possible_cache_dirs():
        assert not os.path.isdir(possible_cache_dirpath)

    if os.path.exists(CACHE_DIR):
        shutil.copytree(temp_cache_dir, CACHE_DIR)
