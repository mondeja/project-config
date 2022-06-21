import multiprocessing
import os
import sys
import time

import pytest
from contextlib_chdir import chdir as chdir_ctx

from project_config import Tree
from project_config.utils import GET, HTTPError


testsdir = os.path.abspath(os.path.dirname(__file__))
if testsdir not in sys.path:
    sys.path.insert(0, testsdir)


from testing_helpers import (  # noqa: E402
    TEST_SERVER_URL,
    testing_server_process,
)


@pytest.fixture
def chdir():
    return chdir_ctx


def _assert_minimal_valid_config(config, expected_style="foo"):
    assert isinstance(config, dict)
    assert len(config) == 1
    assert config["style"] == expected_style


def _minimal_valid_config_with_style(value):
    return f"style = '{value}'"


default_minimal_valid_config_string = _minimal_valid_config_with_style("foo")


@pytest.fixture
def minimal_valid_config():
    min_valid_config = type(
        "MinimalValidConfig",
        (),
        {
            "asserts": _assert_minimal_valid_config,
            "with_style": _minimal_valid_config_with_style,
        },
    )
    min_valid_config.string = default_minimal_valid_config_string
    return min_valid_config


def _assert_minimal_valid_style(value):
    pass


@pytest.fixture
def minimal_valid_style():
    min_valid_style = type(
        "MinimalValidStyle",
        (),
        {
            "asserts": _assert_minimal_valid_style,
        },
    )
    min_valid_style.string = '{"rules": [{"files": ["foo"]}]}'
    return min_valid_style


def _create_files(files, rootdir):
    for fpath, content in files.items():
        if content is False:
            continue
        full_path = rootdir / fpath
        if content is None:
            full_path.mkdir()
        else:
            # ensure parent path directory exists
            parent_fpath, filename = os.path.splitext(str(full_path))
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)
            full_path.write_text(content)


def _create_tree(files, rootdir, cache_files=False):
    _create_files(files, rootdir)
    tree = Tree(rootdir)
    if cache_files:
        tree.cache_files(list(files))
    return tree


@pytest.fixture
def create_files():
    return _create_files


@pytest.fixture
def create_tree():
    return _create_tree


def _assert_plugin_action(
    plugin_method,
    rootdir,
    files,
    value,
    rule,
    expected_results,
):
    results = list(
        plugin_method(
            value,
            _create_tree(files, rootdir, cache_files=True),
            rule,
        ),
    )

    assert len(results) == len(expected_results)

    for (
        (result_type, result_value),
        (expected_result_type, expected_result_value),
    ) in zip(results, expected_results):
        assert result_type == expected_result_type
        assert result_value == expected_result_value


@pytest.fixture
def assert_plugin_action():
    return _assert_plugin_action


def on_start():
    proc = multiprocessing.Process(target=testing_server_process, args=())
    proc.start()
    return proc


@pytest.fixture(autouse=True, scope="session")
def _session_fixture():
    proc = on_start()
    start, timeout = time.time(), 10
    end = start + timeout
    started = False
    while time.time() < end:
        try:
            result = GET(f"{TEST_SERVER_URL}/ping", use_cache=False)
        except HTTPError:
            time.sleep(0.05)
        else:
            if result == "pong":
                started = True
                break
            time.sleep(0.05)
    if not started:
        raise TimeoutError(
            f"Testing server has not started after {timeout} seconds",
        )

    yield
    proc.terminate()
