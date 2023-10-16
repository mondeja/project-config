import argparse
import multiprocessing
import os
import sys
import time

import pytest
from contextlib_chdir import chdir as chdir_ctx

from project_config.__main__ import parse_args
from project_config.tests.pytest_plugin.helpers import (
    create_files as _create_files,
    create_tree as _create_tree,
)
from project_config.utils.http import GET, ProjectConfigHTTPError


testsdir = os.path.abspath(os.path.dirname(__file__))
if testsdir not in sys.path:
    sys.path.insert(0, testsdir)


from testing_helpers import (  # noqa: E402
    TEST_SERVER_URL,
    testing_server_process,
)


# get default argparse namespace for CLI
DEFAULT_ARGPARSE_NAMESPACE = parse_args(["check"])


@pytest.fixture
def chdir():
    return chdir_ctx


@pytest.fixture
def fake_cli_namespace():
    def _fake_cli_namespace(**kwargs):
        namespace = {}
        namespace.update(vars(DEFAULT_ARGPARSE_NAMESPACE))
        namespace.update(kwargs)
        return argparse.Namespace(**namespace)

    return _fake_cli_namespace


def _assert_minimal_valid_config(config, expected_style="foo.json"):
    assert isinstance(config, dict)
    assert len(config) == 1
    assert config["style"] == expected_style


def _minimal_valid_config_with_style(value):
    return f"style = '{value}'"


default_minimal_valid_config_string = _minimal_valid_config_with_style(
    "foo.json",
)


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


def _assert_minimal_valid_style(_value):
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
            result = GET(
                f"{TEST_SERVER_URL}/ping",
                use_cache=False,
                timeout=10,
                sleep=0,
            )
        except ProjectConfigHTTPError:
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
