import multiprocessing
import os
import sys
import time

import pytest
from contextlib_chdir import chdir as chdir_ctx

from project_config.tests.pytest_plugin.helpers import (
    create_files as _create_files,
    create_tree as _create_tree,
)
from project_config.utils.http import GET, HTTPError


testsdir = os.path.abspath(os.path.dirname(__file__))
if testsdir not in sys.path:
    sys.path.insert(0, testsdir)


from testing_helpers import (  # noqa: E402
    TEST_SERVER_URL,
    testing_server_process,
)


# disable project-config cache
os.environ["PROJECT_CONFIG_USE_CACHE"] = "false"


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


@pytest.fixture
def create_files():
    return _create_files


@pytest.fixture
def create_tree():
    return _create_tree


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
